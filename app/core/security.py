import asyncio
import weakref
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import anyio
import bcrypt as _bcrypt
import jwt

# Las capas de arriba capturan JWTError sin depender de la librería que firma.
from jwt import PyJWTError as JWTError  # noqa: F401 (reexportado)

from app.core.config import settings


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# DEF-038 (BC-02). bcrypt tarda ~200 ms de CPU por diseño. Llamado directamente desde una ruta
# async, ese tiempo CONGELA el bucle de eventos: medido el 13/11/2026, tres logins seguidos
# retrasaron 605 ms a todas las demás peticiones del proceso. Por eso las rutas usan estas
# versiones, que lo ejecutan en un hilo (bcrypt libera el GIL: 4 en paralelo tardan lo que 1).
#
# El límite evita el problema contrario: que una ráfaga de logins ocupe todos los núcleos y deje
# sin CPU a la navegación. Se crea uno por bucle de eventos porque un CapacityLimiter queda atado
# al bucle en el que se usa (cada prueba de pytest-asyncio abre uno nuevo).
_limites_bcrypt: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, anyio.CapacityLimiter]" = (
    weakref.WeakKeyDictionary()
)


def _limite_bcrypt() -> anyio.CapacityLimiter:
    bucle = asyncio.get_running_loop()
    limite = _limites_bcrypt.get(bucle)
    if limite is None:
        limite = anyio.CapacityLimiter(settings.BCRYPT_CONCURRENCIA)
        _limites_bcrypt[bucle] = limite
    return limite


async def hash_password_async(password: str) -> str:
    return await anyio.to_thread.run_sync(hash_password, password, limiter=_limite_bcrypt())


async def verify_password_async(plain: str, hashed: str) -> bool:
    return await anyio.to_thread.run_sync(verify_password, plain, hashed, limiter=_limite_bcrypt())


def create_access_token(payload: dict) -> str:
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    data["type"] = "access"
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(payload: dict) -> tuple[str, str]:
    jti = str(uuid4())
    data = payload.copy()
    data["exp"] = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    data["type"] = "refresh"
    data["jti"] = jti
    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def sello_password(password_actualizada: datetime | None) -> int:
    """Marca de la última contraseña (ms desde 1970; 0 si nunca se cambió).

    Va dentro del token de recuperación: al cambiar la contraseña la marca cambia y el
    mismo enlace deja de servir.
    """
    if password_actualizada is None:
        return 0
    return int(password_actualizada.replace(tzinfo=timezone.utc).timestamp() * 1000)


def create_password_reset_token(id_usuario: int, pwd_ts: int = 0) -> str:
    data = {
        "sub": str(id_usuario),
        "type": "reset",
        "pwd_ts": pwd_ts,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
