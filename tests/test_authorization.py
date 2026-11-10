"""Autorización vista desde HTTP.

Todas estas peticiones se rechazan antes de llegar a la base de datos, así que
corren sin Postgres. Si una de ellas llegara a la base, fallaría por
conexión: esa es la señal de que un endpoint dejó de exigir autenticación.
"""

import pytest

from app.core.security import create_refresh_token
from main import app
from tests.conftest import bearer

PUBLICOS = {
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"),
    ("POST", "/api/v1/auth/logout"),
    ("POST", "/api/v1/auth/forgot-password"),
    ("POST", "/api/v1/auth/reset-password"),
    # Catálogos que el formulario de registro necesita antes de iniciar sesión.
    ("GET", "/api/v1/cursos"),
    ("GET", "/api/v1/cursos/{id_curso}"),
    ("GET", "/api/v1/cursos/{id_curso}/horarios"),
    ("GET", "/api/v1/especializaciones"),
}


def _endpoints():
    for path, methods in app.openapi()["paths"].items():
        for method, spec in methods.items():
            yield method.upper(), path, spec


def test_solo_los_endpoints_publicos_declarados_no_piden_token():
    sin_token = {
        (method, path)
        for method, path, spec in _endpoints()
        if not spec.get("security")
    }

    assert sin_token == PUBLICOS


def test_todo_endpoint_no_publico_declara_bearer():
    protegidos = [(m, p) for m, p, _ in _endpoints() if (m, p) not in PUBLICOS]

    assert len(protegidos) >= 90
    for method, path, spec in _endpoints():
        if (method, path) in PUBLICOS:
            continue
        assert spec.get("security") == [{"HTTPBearer": []}], f"{method} {path}"


async def test_sin_token_se_responde_401(client):
    response = await client.get("/api/v1/usuarios")

    assert response.status_code == 401


async def test_un_token_invalido_se_responde_401(client):
    response = await client.get("/api/v1/usuarios", headers={"Authorization": "Bearer no-es-un-jwt"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Token inválido o expirado"


async def test_un_refresh_token_no_sirve_como_access_token(client):
    refresh, _ = create_refresh_token({"sub": "1", "idRol": 3, "rol": "admin"})

    response = await client.get("/api/v1/usuarios", headers={"Authorization": f"Bearer {refresh}"})

    assert response.status_code == 401


@pytest.mark.parametrize(("rol", "id_rol"), [("docente", 1), ("estudiante", 2), ("padre", 4)])
async def test_solo_el_admin_lista_usuarios(client, rol, id_rol):
    response = await client.get("/api/v1/usuarios", headers=bearer(rol, id_rol))

    assert response.status_code == 403


async def test_cors_acepta_cualquier_origen_sin_credenciales(client):
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://sitio-cualquiera.example",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert "access-control-allow-credentials" not in response.headers
    assert "authorization" in response.headers["access-control-allow-headers"].lower()


# --- BE-04: asistencia de un estudiante ajeno ------------------------------------------------

from datetime import date, datetime  # noqa: E402
from types import SimpleNamespace  # noqa: E402

from app.api.v1 import asistencia as asistencia_api  # noqa: E402
from app.api.v1 import padres as padres_api  # noqa: E402
from app.application.asistencia.schemas import AsistenciaOut  # noqa: E402
from app.core.exceptions import ForbiddenException  # noqa: E402


def _asistencia(id_estudiante: int = 10) -> AsistenciaOut:
    return AsistenciaOut(
        id_asistencia=5, id_estudiante=id_estudiante, fecha=date(2026, 11, 2), estado="Presente",
        observacion=None, registrado_por=1, fecha_registro=datetime(2026, 11, 2, 7, 0),
        tipo="entrada", codigo_qr=None, activo=True,
    )


class _AsistenciaFalsa:
    llamadas: list[dict] = []

    def __init__(self, db):
        pass

    async def list(self, **filtros):
        _AsistenciaFalsa.llamadas.append(filtros)
        return []

    async def get(self, id_asistencia):
        return _asistencia(id_estudiante=99)


@pytest.fixture
def asistencia(monkeypatch, sin_base_de_datos):
    _AsistenciaFalsa.llamadas = []
    monkeypatch.setattr(asistencia_api, "AsistenciaService", _AsistenciaFalsa)
    return monkeypatch


def _acceso(monkeypatch, permitido: bool):
    async def fake(db, current_user, id_estudiante):
        if not permitido:
            raise ForbiddenException("Solo puede consultar la información del estudiante asociado")

    monkeypatch.setattr(asistencia_api, "assert_acceso_estudiante", fake)


async def test_un_padre_que_pide_la_asistencia_de_otro_estudiante_recibe_403(client, asistencia):
    _acceso(asistencia, permitido=False)

    response = await client.get("/api/v1/asistencia?id_estudiante=99", headers=bearer("padre", 4))

    assert response.status_code == 403
    assert _AsistenciaFalsa.llamadas == []


async def test_un_padre_sin_filtro_de_estudiante_recibe_400(client, asistencia):
    _acceso(asistencia, permitido=True)

    response = await client.get("/api/v1/asistencia", headers=bearer("padre", 4))

    assert response.status_code == 400
    assert _AsistenciaFalsa.llamadas == []


async def test_un_estudiante_lee_su_propia_asistencia(client, asistencia):
    _acceso(asistencia, permitido=True)

    response = await client.get("/api/v1/asistencia?id_estudiante=10", headers=bearer("estudiante", 2))

    assert response.status_code == 200
    assert _AsistenciaFalsa.llamadas[0]["id_estudiante"] == 10


async def test_el_detalle_de_una_asistencia_ajena_recibe_403(client, asistencia):
    _acceso(asistencia, permitido=False)

    response = await client.get("/api/v1/asistencia/5", headers=bearer("padre", 4))

    assert response.status_code == 403


async def test_el_admin_lista_la_asistencia_sin_filtro(client, asistencia):
    _acceso(asistencia, permitido=False)  # no debe ni consultarse para el admin

    response = await client.get("/api/v1/asistencia", headers=bearer("admin", 3))

    assert response.status_code == 200
    assert _AsistenciaFalsa.llamadas[0]["id_estudiante"] is None


# --- BE-05: vínculo de otro padre -----------------------------------------------------------


class _PadresFalsos:
    def __init__(self, session):
        pass

    async def get_by_id(self, id_padre):
        return SimpleNamespace(
            id_padre=id_padre, id_usuario=4, id_estudiante=10, parentesco="Madre", ocupacion=None
        )


@pytest.fixture
def padres(monkeypatch, sin_base_de_datos):
    monkeypatch.setattr(padres_api, "PadreRepository", _PadresFalsos)


async def test_un_padre_pide_su_propio_registro(client, padres):
    response = await client.get("/api/v1/padres/1", headers=bearer("padre", 4, id_usuario=4))

    assert response.status_code == 200


async def test_un_padre_no_puede_pedir_el_registro_de_otro_padre(client, padres):
    response = await client.get("/api/v1/padres/1", headers=bearer("padre", 4, id_usuario=5))

    assert response.status_code == 403


async def test_el_admin_pide_el_registro_de_cualquier_padre(client, padres):
    response = await client.get("/api/v1/padres/1", headers=bearer("admin", 3, id_usuario=1))

    assert response.status_code == 200


# --- CP-NF-003: cabeceras de seguridad que marcó OWASP ZAP ---


async def test_todas_las_respuestas_llevan_nosniff(client):
    """Segunda barrera para BE-14: los avatares se sirven públicos desde /static/avatars.

    Sin `nosniff`, un navegador puede ignorar el Content-Type y ejecutar como HTML un archivo
    subido por un usuario.
    """
    # `/openapi.json` no consulta la base: así la prueba comprueba la cabecera y nada más.
    r = await client.get("/openapi.json")

    assert r.status_code == 200
    assert r.headers.get("X-Content-Type-Options") == "nosniff"


async def test_hsts_solo_sobre_https(client):
    """La especificación dice que HSTS no se envía sobre HTTP, y el cliente de pruebas es http."""
    r = await client.get("/openapi.json")

    assert "Strict-Transport-Security" not in r.headers
