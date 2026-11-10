"""BE-16: tras 5 intentos fallidos el inicio de sesión se bloquea 15 minutos.

La hora entra al servicio como dependencia (`reloj`), así la prueba la adelanta sin esperar.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from app.application.auth import service as auth_service
from app.application.auth.schemas import LoginRequest
from app.core.exceptions import TooManyRequestsException, UnauthorizedException
from tests import dobles

AHORA = datetime(2026, 11, 2, 10, 0, 0)


class _Sesion:
    commits = 0

    async def commit(self):
        _Sesion.commits += 1

    async def flush(self): ...


class _Reloj:
    def __init__(self):
        self.ahora = AHORA

    def __call__(self):
        return self.ahora


@pytest.fixture
def servicio(monkeypatch):
    dobles.RepoSesiones.reiniciar()
    dobles.RepoUsuariosAuth.reiniciar(dobles.usuario_auth())
    monkeypatch.setattr(auth_service, "UsuarioRepository", dobles.RepoUsuariosAuth)
    monkeypatch.setattr(auth_service, "SesionRepository", dobles.RepoSesiones)
    reloj = _Reloj()
    return auth_service.AuthService(_Sesion(), reloj=reloj), reloj


def _intento(password):
    return LoginRequest(correo="ana@x.com", password=password)


async def _fallar(servicio, veces):
    for _ in range(veces):
        with pytest.raises(UnauthorizedException):
            await servicio.login(_intento("incorrecta"))


async def test_el_sexto_intento_responde_429_aunque_la_contrasena_sea_correcta(servicio):
    servicio, _ = servicio
    await _fallar(servicio, 5)

    with pytest.raises(TooManyRequestsException) as error:
        await servicio.login(_intento("Actual#2026"))

    assert error.value.status_code == 429
    assert "espera 15 minutos" in error.value.detail


async def test_fallo_fallo_exito_reinicia_el_contador(servicio):
    servicio, _ = servicio
    await _fallar(servicio, 2)
    assert dobles.RepoUsuariosAuth.usuario.intentos_fallidos == 2

    tokens = await servicio.login(_intento("Actual#2026"))

    assert tokens.access_token
    assert dobles.RepoUsuariosAuth.usuario.intentos_fallidos == 0


async def test_pasados_16_minutos_se_puede_volver_a_intentar(servicio):
    servicio, reloj = servicio
    await _fallar(servicio, 5)
    reloj.ahora = AHORA + timedelta(minutes=16)

    tokens = await servicio.login(_intento("Actual#2026"))

    assert tokens.refresh_token
    assert dobles.RepoUsuariosAuth.usuario.bloqueado_hasta is None


async def test_a_los_14_minutos_el_bloqueo_sigue(servicio):
    servicio, reloj = servicio
    await _fallar(servicio, 5)
    reloj.ahora = AHORA + timedelta(minutes=14)

    with pytest.raises(TooManyRequestsException):
        await servicio.login(_intento("Actual#2026"))


async def test_cuatro_fallos_todavia_no_bloquean(servicio):
    servicio, _ = servicio
    await _fallar(servicio, 4)

    assert dobles.RepoUsuariosAuth.bloqueos == []
    assert (await servicio.login(_intento("Actual#2026"))).access_token


async def test_el_mensaje_de_credenciales_invalidas_es_generico(servicio):
    servicio, _ = servicio
    dobles.RepoUsuariosAuth.usuario = None

    with pytest.raises(UnauthorizedException) as error:
        await servicio.login(LoginRequest(correo="nadie@x.com", password="x"))

    assert error.value.detail == "Credenciales inválidas"


async def test_los_fallos_se_guardan_aunque_la_peticion_termine_en_401(servicio):
    servicio, _ = servicio
    _Sesion.commits = 0

    await _fallar(servicio, 1)

    assert _Sesion.commits == 1
    assert isinstance(SimpleNamespace(), SimpleNamespace)
