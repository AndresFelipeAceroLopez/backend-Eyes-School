"""DEF-039: un id fuera del rango de PostgreSQL debe responder 4xx, no 500.

Lo encontró `schemathesis` contra el contrato de QA y se verificó a mano en 9 de 9 endpoints con
parámetro de id. FastAPI valida que el parámetro sea un entero, pero no su magnitud: el valor
llegaba a la consulta, la base lo rechazaba y el error subía sin capturar.

La corrección tiene dos capas (la segunda se rehízo el 13/11/2026, BC-07):

1. **Validación.** Los ids de los routers son `Entero32` (`application/common/tipos.py`): un valor
   fuera del `integer` de PostgreSQL se rechaza con 422 antes de consultar la base, y el contrato
   publica el rango. Antes respondía 422 desde la base y schemathesis lo marcaba (ST202), porque
   para el contrato ese id era válido.
2. **Red de seguridad.** Si un valor igual llega a la base y esta lo rechaza (`DataError`), el
   manejador de `main.py` responde 404 si estaba en la ruta y 422 con forma de error de
   validación si estaba en el cuerpo o la query.

El caso que más importa de este archivo es el último: un fallo real de la base (conexión caída)
tiene que seguir siendo 500, porque convertirlo en 404 o 422 escondería una caída del servidor.
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
async def test_un_id_fuera_de_rango_se_rechaza_antes_de_la_base(client, ruta, monkeypatch):
    """El id gigante responde 422 por validación: la sesión, que fallaría, ni se usa."""

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
    assert r.json()["detail"][0]["type"] == "less_than_equal"


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


async def test_si_la_base_rechaza_un_valor_de_la_ruta_responde_404(client):
    """Red de seguridad: un id en rango que la base rechaza igual no es un 500."""

    class _Sesion:
        async def get(self, *_a, **_k):
            raise _error_de_dato()

        async def execute(self, *_a, **_k):
            raise _error_de_dato()

        async def scalar(self, *_a, **_k):
            raise _error_de_dato()

    async def _db():
        yield _Sesion()

    from tests.conftest import bearer

    app.dependency_overrides[get_db] = _db
    try:
        r = await client.get("/api/v1/cursos/5", headers=bearer("admin", 3))
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert r.status_code == 404
    assert r.json() == {"detail": "Recurso no encontrado"}
