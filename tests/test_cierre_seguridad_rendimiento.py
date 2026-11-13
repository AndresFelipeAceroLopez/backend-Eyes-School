"""Cierre de la campaña del backend (planeación de cierre, 13/11/2026).

- BC-02 / DEF-038: bcrypt corre fuera del bucle de eventos y con un límite de concurrencia.
- BC-10 / A09: los eventos de seguridad quedan en el log con hora y ruta, sin secretos.
- BC-10 / A10: el nombre del usuario se escapa en el correo de recuperación.
"""

import asyncio
import logging
import time

import bcrypt
import pytest

from app.application.auth import service as auth_service
from app.application.auth.schemas import LoginRequest
from app.core import security
from app.core.email import build_reset_email_html
from app.core.exceptions import UnauthorizedException
from tests import dobles
from tests.conftest import bearer

# --------------------------------------------------------------------------- BC-02 · bcrypt


async def _retraso_maximo_del_bucle(trabajo) -> float:
    """Mide cuánto se atrasa un temporizador de 10 ms mientras corre `trabajo`."""
    retrasos = []

    async def latido():
        for _ in range(25):
            inicio = time.perf_counter()
            await asyncio.sleep(0.01)
            retrasos.append(time.perf_counter() - inicio - 0.01)

    tarea = asyncio.create_task(latido())
    await asyncio.sleep(0.02)
    await trabajo()
    await tarea
    return max(retrasos)


async def test_verificar_la_contrasena_no_congela_el_bucle_de_eventos():
    """Antes, cada login dejaba quietas todas las demás peticiones ~200 ms (DEF-038)."""
    hash_ = bcrypt.hashpw(b"Actual#2026", bcrypt.gensalt())

    async def tres_logins():
        for _ in range(3):
            assert await security.verify_password_async("Actual#2026", hash_.decode())

    # Tres verificaciones serían ~600 ms de bucle congelado; en un hilo el latido sigue.
    assert await _retraso_maximo_del_bucle(tres_logins) < 0.15


async def test_el_hash_asincrono_es_compatible_con_el_sincrono():
    hash_ = await security.hash_password_async("Clave#2026")
    assert security.verify_password("Clave#2026", hash_)
    assert not await security.verify_password_async("Otra#2026", hash_)


async def test_nunca_corren_mas_hash_a_la_vez_que_el_limite(monkeypatch):
    monkeypatch.setattr(security.settings, "BCRYPT_CONCURRENCIA", 2)
    security._limites_bcrypt.clear()
    en_curso = maximo = 0

    def hash_lento(_password):
        nonlocal en_curso, maximo
        en_curso += 1
        maximo = max(maximo, en_curso)
        time.sleep(0.05)
        en_curso -= 1
        return "hash"

    monkeypatch.setattr(security, "hash_password", hash_lento)
    await asyncio.gather(*(security.hash_password_async("x") for _ in range(6)))

    assert maximo == 2
    security._limites_bcrypt.clear()


# --------------------------------------------------------------------------- BC-10 · A09


@pytest.mark.parametrize(
    ("ruta", "cabeceras", "estado"),
    [
        ("/api/v1/usuarios?token=secreto-en-query", {}, 401),
        ("/api/v1/usuarios", bearer("estudiante", 2), 403),
        ("/api/v1/no-existe", {}, 404),
    ],
)
async def test_los_rechazos_quedan_en_el_log_sin_secretos(client, caplog, ruta, cabeceras, estado):
    caplog.set_level(logging.WARNING, logger="eyes.seguridad")

    respuesta = await client.get(ruta, headers=cabeceras)

    assert respuesta.status_code == estado
    registro = [r for r in caplog.records if r.name == "eyes.seguridad"]
    assert len(registro) == 1
    mensaje = registro[0].getMessage()
    assert f"GET {ruta.split('?')[0]} -> {estado}" in mensaje
    # Ni la query string ni el token del encabezado llegan al log.
    assert "secreto-en-query" not in mensaje
    assert "Bearer" not in mensaje and "eyJ" not in mensaje


async def test_una_respuesta_correcta_no_se_registra_como_evento(client, caplog):
    caplog.set_level(logging.WARNING, logger="eyes.seguridad")
    respuesta = await client.get("/openapi.json")
    assert respuesta.status_code == 200
    assert not [r for r in caplog.records if r.name == "eyes.seguridad"]


@pytest.fixture
def servicio_auth(monkeypatch):
    dobles.RepoSesiones.reiniciar()
    dobles.RepoUsuariosAuth.reiniciar(dobles.usuario_auth())
    monkeypatch.setattr(auth_service, "UsuarioRepository", dobles.RepoUsuariosAuth)
    monkeypatch.setattr(auth_service, "SesionRepository", dobles.RepoSesiones)

    class _Sesion:
        async def commit(self): ...

        async def flush(self): ...

    return auth_service.AuthService(_Sesion())


async def test_el_login_fallido_deja_el_usuario_y_el_intento_pero_no_la_contrasena(
    servicio_auth, caplog
):
    caplog.set_level(logging.WARNING, logger="app.application.auth.service")

    with pytest.raises(UnauthorizedException):
        await servicio_auth.login(LoginRequest(correo="ana@x.com", password="NoEsLaClave#1"))

    texto = " ".join(r.getMessage() for r in caplog.records)
    assert "Inicio de sesión fallido: usuario" in texto and "intento 1" in texto
    assert "NoEsLaClave#1" not in texto
    assert "ana@x.com" not in texto


async def test_el_login_con_correo_desconocido_se_registra_sin_el_correo(servicio_auth, caplog):
    caplog.set_level(logging.WARNING, logger="app.application.auth.service")

    with pytest.raises(UnauthorizedException):
        await servicio_auth.login(LoginRequest(correo="nadie@x.com", password="Algo#2026"))

    texto = " ".join(r.getMessage() for r in caplog.records)
    assert "correo no registrado" in texto
    assert "nadie@x.com" not in texto


# --------------------------------------------------------------------------- BC-10 · A10


def test_el_nombre_se_escapa_en_el_correo_de_recuperacion():
    html = build_reset_email_html('<img src=x onerror="alert(1)">', "https://web/reset?token=t")
    assert "<img" not in html
    assert "&lt;img" in html


# --------------------------------------------------------------------------- BC-07 · contrato


async def test_el_contrato_declara_los_errores_reales(client):
    rutas = (await client.get("/openapi.json")).json()["paths"]

    assert {"401", "403", "404"} <= set(rutas["/api/v1/notas/{id_nota}"]["get"]["responses"])
    assert {"400", "409"} <= set(rutas["/api/v1/notas"]["post"]["responses"])
    # El login es público: 401 (credenciales), 403 (cuenta no activa, N-31) y 429 (bloqueo);
    # no los de escritura.
    assert set(rutas["/api/v1/auth/login"]["post"]["responses"]) == {
        "200", "401", "403", "422", "429",
    }
    error = rutas["/api/v1/notas/{id_nota}"]["get"]["responses"]["404"]
    assert error["content"]["application/json"]["schema"] == {"$ref": "#/components/schemas/ErrorOut"}


async def test_el_boletin_declara_que_responde_pdf(client):
    rutas = (await client.get("/openapi.json")).json()["paths"]
    boletin = rutas["/api/v1/notas/estudiantes/{id_estudiante}/boletin/pdf"]["get"]
    assert "application/pdf" in boletin["responses"]["200"]["content"]


async def test_un_405_lista_todos_los_metodos_de_la_ruta(client):
    """ST205: GET, PUT y DELETE de /cursos/{id} son rutas distintas; Allow debe nombrarlas todas."""
    respuesta = await client.request("OPTIONS", "/api/v1/cursos/1")
    assert respuesta.status_code == 405
    assert set(respuesta.headers["Allow"].split(", ")) == {"GET", "PUT", "DELETE"}


def test_las_fechas_salen_con_zona_utc():
    from datetime import datetime

    from app.application.notas.schemas import NotaOut

    nota = NotaOut(
        id_nota=1, id_estudiante=1, id_materia=1, id_periodo=1, nota=4.5, observacion=None,
        fecha_registro=datetime(2026, 11, 3, 3, 3, 37), registrado_por=2,
    )
    assert nota.model_dump(mode="json")["fecha_registro"] == "2026-11-03T03:03:37Z"


async def test_put_sobre_me_responde_405_y_no_422(client):
    """ST204: `PUT /estudiantes/me` caía en `PUT /estudiantes/{id_estudiante}` con id="me"."""
    for ruta in ("/api/v1/estudiantes/me", "/api/v1/padres/me"):
        respuesta = await client.put(ruta, headers=bearer("admin", 3), json={})
        assert respuesta.status_code == 405, ruta
        assert "GET" in respuesta.headers["Allow"]


@pytest.mark.parametrize("fecha", ["0", "1731456000", "13-11-2026", "2026/11/13"])
async def test_el_filtro_de_fecha_solo_acepta_aaaa_mm_dd(client, fecha):
    """ST201: un número se aceptaba como fecha (segundos desde 1970) y respondía 200 vacío."""
    respuesta = await client.get(
        "/api/v1/asistencia", params={"fecha": fecha}, headers=bearer("admin", 3)
    )
    assert respuesta.status_code == 422
