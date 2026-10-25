"""Configuración común de las pruebas.

Las variables de entorno se fijan ANTES de importar la app: tienen prioridad
sobre el archivo .env, así que ninguna prueba puede conectarse a la base de
datos real ni a Redis aunque el .env del desarrollador apunte a producción.
"""

import os

os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@127.0.0.1:1/test"
os.environ["REDIS_URL"] = "redis://127.0.0.1:1/0"
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas-de-32-bytes-o-mas"
os.environ["ENVIRONMENT"] = "test"
os.environ["CORS_ORIGINS"] = "*"

import httpx  # noqa: E402
import pytest  # noqa: E402

from app.core.security import create_access_token  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def bearer(rol: str, id_rol: int, id_usuario: int = 1) -> dict[str, str]:
    """Encabezado de un usuario autenticado con el rol dado."""
    token = create_access_token({"sub": str(id_usuario), "idRol": id_rol, "rol": rol})
    return {"Authorization": f"Bearer {token}"}
