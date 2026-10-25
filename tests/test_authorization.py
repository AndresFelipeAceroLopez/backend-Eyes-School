"""Autorización vista desde HTTP.

Todas estas peticiones se rechazan antes de llegar a la base de datos, así que
corren sin Postgres ni Redis. Si una de ellas llegara a la base, fallaría por
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
