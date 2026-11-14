"""BE-13 y BE-17: sesiones de refresco en PostgreSQL (sin caché externa), cierre de sesión y enlaces.

Los repositorios de sesiones y usuarios se reemplazan por dobles con estado, de modo que la
secuencia login → refresh → logout → refresh se ejecuta de punta a punta por HTTP.
"""

import pytest

from app.application.auth import service as auth_service
from app.application.auth.schemas import LoginRequest
from app.application.usuarios import service as usuarios_service
from app.core.security import create_password_reset_token, create_refresh_token, decode_token
from tests import dobles
from tests.conftest import bearer

pytestmark = pytest.mark.usefixtures("sin_base_de_datos")


@pytest.fixture(autouse=True)
def repos(monkeypatch):
    dobles.RepoSesiones.reiniciar()
    dobles.RepoUsuariosAuth.reiniciar(dobles.usuario_auth())
    monkeypatch.setattr(auth_service, "UsuarioRepository", dobles.RepoUsuariosAuth)
    monkeypatch.setattr(auth_service, "SesionRepository", dobles.RepoSesiones)
    monkeypatch.setattr(usuarios_service, "UsuarioRepository", dobles.RepoUsuariosAuth)
    monkeypatch.setattr(usuarios_service, "SesionRepository", dobles.RepoSesiones)


async def _login(client):
    response = await client.post(
        "/api/v1/auth/login", json={"correo": "Ana@X.com", "password": "Actual#2026"}
    )
    assert response.status_code == 200
    return response.json()


# --- BE-17: las sesiones viven en la base -----------------------------------------------------


async def test_login_crea_la_sesion_con_el_jti_del_token_emitido(client):
    tokens = await _login(client)

    jti = decode_token(tokens["refresh_token"])["jti"]
    assert [s[:2] for s in dobles.RepoSesiones.creadas] == [(jti, 7)]


async def test_refresh_con_una_sesion_revocada_responde_401(client):
    refresh, _ = create_refresh_token({"sub": "7", "idRol": 1, "rol": "docente"})

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})

    assert response.status_code == 401


async def test_logout_revoca_la_sesion_por_su_jti(client):
    tokens = await _login(client)

    response = await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 204
    assert dobles.RepoSesiones.revocadas == [decode_token(tokens["refresh_token"])["jti"]]


# --- BE-13: sesión y cierre de sesión ---------------------------------------------------------


async def test_refresh_valido_devuelve_un_access_token(client):
    tokens = await _login(client)

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    assert decode_token(response.json()["access_token"])["type"] == "access"


async def test_despues_de_cerrar_sesion_el_refresh_responde_401(client):
    tokens = await _login(client)
    cuerpo = {"refresh_token": tokens["refresh_token"]}

    assert (await client.post("/api/v1/auth/logout", json=cuerpo)).status_code == 204
    assert (await client.post("/api/v1/auth/refresh", json=cuerpo)).status_code == 401


async def test_un_usuario_desactivado_no_puede_renovar_su_sesion(client):
    tokens = await _login(client)
    dobles.RepoUsuariosAuth.usuario.estado = False

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 401


async def test_un_access_token_no_sirve_para_renovar(client):
    tokens = await _login(client)

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})

    assert response.status_code == 401


async def test_desactivar_un_usuario_revoca_todas_sus_sesiones(client):
    response = await client.patch("/api/v1/usuarios/7/estado?estado=false", headers=bearer("admin", 3))

    assert response.status_code == 200
    assert dobles.RepoSesiones.revocadas_de_usuario == [7]


async def test_activar_un_usuario_no_revoca_sesiones(client):
    await client.patch("/api/v1/usuarios/7/estado?estado=true", headers=bearer("admin", 3))

    assert dobles.RepoSesiones.revocadas_de_usuario == []


async def test_el_enlace_de_recuperacion_solo_sirve_una_vez(client):
    token = create_password_reset_token(7, pwd_ts=0)
    cuerpo = {"token": token, "new_password": "Nueva#2026"}

    primero = await client.post("/api/v1/auth/reset-password", json=cuerpo)
    segundo = await client.post("/api/v1/auth/reset-password", json=cuerpo)

    assert primero.status_code == 200
    assert segundo.status_code == 401


async def test_cambiar_la_contrasena_cierra_las_demas_sesiones(client):
    token = create_password_reset_token(7, pwd_ts=0)

    await client.post("/api/v1/auth/reset-password", json={"token": token, "new_password": "Nueva#2026"})

    assert dobles.RepoSesiones.revocadas_de_usuario == [7]


async def test_un_enlace_con_contrasena_debil_responde_422(client):
    token = create_password_reset_token(7, pwd_ts=0)

    response = await client.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "12345678"}
    )

    assert response.status_code == 422


def test_el_servicio_de_autenticacion_no_usa_cache_externa():
    import inspect

    assert ("red" + "is") not in inspect.getsource(auth_service).lower()
    assert LoginRequest(correo=" A@b.co ", password="x").correo == "a@b.co"
