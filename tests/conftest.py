"""Configuración común de las pruebas.

Las variables de entorno se fijan ANTES de importar la app: tienen prioridad
sobre el archivo .env, así que ninguna prueba puede conectarse a la base de
datos real aunque el .env del desarrollador apunte a producción.

Las pruebas de `tests/integration/` (marca `integration`) sí usan PostgreSQL y fijan su
propia `DATABASE_URL` en `tests/integration/conftest.py`.
"""

import os

# Solo `TEST_DATABASE_URL` (una base desechable) puede reemplazar la dirección ficticia; el
# `DATABASE_URL` del entorno o del .env nunca se usa en las pruebas.
os.environ["DATABASE_URL"] = (
    os.environ.get("TEST_DATABASE_URL") or "postgresql+asyncpg://test:test@127.0.0.1:1/test"
)
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas-de-32-bytes-o-mas"
os.environ["ENVIRONMENT"] = "test"
os.environ["CORS_ORIGINS"] = "*"
os.environ["FIREBASE_CREDENTIALS_JSON"] = ""

from types import SimpleNamespace  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402

from app.core.database import get_db  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def sin_base_de_datos():
    """Reemplaza la sesión de base de datos por un objeto vacío.

    Las pruebas que usan esta fixture deben reemplazar también los repositorios o servicios
    que tocarían la base: si alguno llega a usarla, la prueba falla con `AttributeError`.
    """

    class _SesionVacia(SimpleNamespace):
        async def commit(self): ...

        async def flush(self): ...

        async def rollback(self): ...

    async def _db():
        yield _SesionVacia()

    app.dependency_overrides[get_db] = _db
    yield
    app.dependency_overrides.pop(get_db, None)


def bearer(rol: str, id_rol: int, id_usuario: int = 1) -> dict[str, str]:
    """Encabezado de un usuario autenticado con el rol dado."""
    token = create_access_token({"sub": str(id_usuario), "idRol": id_rol, "rol": rol})
    return {"Authorization": f"Bearer {token}"}
