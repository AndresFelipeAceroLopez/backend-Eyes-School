from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt as _bcrypt
import jwt

# Las capas de arriba capturan JWTError sin depender de la librería que firma.
from jwt import PyJWTError as JWTError  # noqa: F401 (reexportado)

from app.core.config import settings


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


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
