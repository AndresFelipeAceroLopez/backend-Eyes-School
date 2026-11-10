"""DEF-023: un id fuera del rango de PostgreSQL debe responder 422, no 500.

Lo encontró `schemathesis` contra el contrato de QA y se verificó a mano en 9 de 9 endpoints con
parámetro de id. FastAPI valida que el parámetro sea un entero, pero no su magnitud: el valor
llegaba a la consulta, la base lo rechazaba y el error subía sin capturar.

La corrección es un manejador de `DBAPIError` en `main.py` que responde 422 **solo** cuando el
error viene del valor que mandó el cliente. El caso que más importa de este archivo es el
último: un fallo real de la base (conexión caída) tiene que seguir siendo 500, porque
convertirlo en 422 escondería una caída del servidor.
"""

import asyncpg
import pytest
from sqlalchemy.exc import DBAPIError, OperationalError

from app.core.dependencies import get_db
from main import _es_dato_invalido, app

# 2^63: no cabe en bigint, que es lo máximo que PostgreSQL acepta para un id.
FUERA_DE_RANGO = 9223372036854775808


def _error_de_dato() -> DBAPIError:
    """Reproduce el error tal como lo envuelve SQLAlchemy cuando asyncpg rechaza el valor."""
    envoltorio = Exception("asyncpg wrapper")
    envoltorio.__cause__ = asyncpg.exceptions.DataError("value out of int64 range")
    return DBAPIError("SELECT ...", {}, envoltorio)


def _fallo_de_la_base() -> DBAPIError:
    """Un fallo real del servidor: la conexión se cayó. No lo mandó el cliente."""
    envoltorio = Exception("asyncpg wrapper")
    envoltorio.__cause__ = asyncpg.exceptions.ConnectionDoesNotExistError("connection closed")
    return OperationalError("SELECT ...", {}, envoltorio)


def test_distingue_un_valor_invalido_de_una_caida_de_la_base():
    assert _es_dato_invalido(_error_de_dato()) is True
    assert _es_dato_invalido(_fallo_de_la_base()) is False


@pytest.mark.parametrize(
    "ruta",
    [
        "/api/v1/estudiantes/{}",
        "/api/v1/cursos/{}",
        "/api/v1/usuarios/{}",
        "/api/v1/notas/{}",
        "/api/v1/asistencia/{}",
        "/api/v1/materias/{}",
        "/api/v1/profesores/{}",
        "/api/v1/novedades/{}",
        "/api/v1/reportes/{}",
        "/api/v1/cursos/{}/horarios",
        "/api/v1/especializaciones/{}",
    ],
)
async def test_un_id_fuera_de_rango_responde_422_y_no_500(client, ruta, monkeypatch):
    """Con el id gigante, la base rechaza el valor y la API debe responder 422."""

    class _SesionQueRechazaElValor:
        async def execute(self, *_a, **_k):
            raise _error_de_dato()

        async def scalar(self, *_a, **_k):
            raise _error_de_dato()

        async def get(self, *_a, **_k):
            raise _error_de_dato()

    async def _db():
        yield _SesionQueRechazaElValor()

    app.dependency_overrides[get_db] = _db
    try:
        from tests.conftest import bearer

        r = await client.get(ruta.format(FUERA_DE_RANGO), headers=bearer("admin", 3))
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert r.status_code == 422, f"{ruta} respondió {r.status_code}"
    assert r.json()["detail"] == "Valor fuera del rango permitido."


async def test_una_caida_de_la_base_sigue_siendo_500(client, monkeypatch):
    """La red importante: un fallo real del servidor NO se disfraza de error del cliente."""

    class _SesionCaida:
        async def execute(self, *_a, **_k):
            raise _fallo_de_la_base()

        async def scalar(self, *_a, **_k):
            raise _fallo_de_la_base()

        async def get(self, *_a, **_k):
            raise _fallo_de_la_base()

    async def _db():
        yield _SesionCaida()

    from tests.conftest import bearer

    app.dependency_overrides[get_db] = _db
    try:
        with pytest.raises(DBAPIError):
            await client.get("/api/v1/estudiantes/1", headers=bearer("admin", 3))
    finally:
        app.dependency_overrides.pop(get_db, None)
