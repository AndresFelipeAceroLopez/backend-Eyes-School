"""BE-18: al registrar una novedad se avisa por push a los acudientes del estudiante."""

import logging
from types import SimpleNamespace

import pytest

from app.api.v1 import dispositivos as dispositivos_api
from app.application.novedades import service as novedades_service
from app.application.novedades.schemas import NovedadCreate
from app.infrastructure.notificador_firebase import get_notificador
from main import app
from tests import dobles
from tests.conftest import bearer

pytestmark = pytest.mark.usefixtures("sin_base_de_datos")

DOCENTE_7 = bearer("docente", 1, id_usuario=7)
CUERPO = {
    "id_estudiante": 10, "id_tipo_novedad": 1, "fecha": "2026-11-02", "descripcion": "Llegó tarde",
}


@pytest.fixture(autouse=True)
def repos(monkeypatch):
    dobles.RepoNovedades.reiniciar()
    dobles.RepoPadres.padres = [SimpleNamespace(id_usuario=4), SimpleNamespace(id_usuario=5)]
    dobles.RepoDispositivos.tokens_por_usuario = {
        4: ["tok-madre"], 5: ["tok-padre-1", "tok-padre-2"], 99: ["tok-de-otro-estudiante"],
    }
    for nombre, doble in {
        "NovedadRepository": dobles.RepoNovedades,
        "TipoNovedadRepository": dobles.RepoTiposNovedad,
        "PadreRepository": dobles.RepoPadres,
        "EstudianteRepository": dobles.RepoEstudiantes,
        "DispositivoRepository": dobles.RepoDispositivos,
    }.items():
        monkeypatch.setattr(novedades_service, nombre, doble)


@pytest.fixture
def notificador():
    falso = dobles.NotificadorFalso()
    app.dependency_overrides[get_notificador] = lambda: falso
    yield falso
    app.dependency_overrides.pop(get_notificador, None)


async def test_crear_una_novedad_envia_un_push_solo_a_los_acudientes_del_estudiante(client, notificador):
    response = await client.post("/api/v1/novedades", json=CUERPO, headers=DOCENTE_7)

    assert response.status_code == 201
    assert len(notificador.envios) == 1
    envio = notificador.envios[0]
    assert sorted(envio["tokens"]) == ["tok-madre", "tok-padre-1", "tok-padre-2"]
    assert envio["titulo"] == "Nueva novedad de Ana Gómez"
    assert envio["datos"]["id_estudiante"] == "10"


async def test_un_estudiante_sin_acudientes_no_genera_envios(client, notificador):
    dobles.RepoPadres.padres = []

    response = await client.post("/api/v1/novedades", json=CUERPO, headers=DOCENTE_7)

    assert response.status_code == 201
    assert notificador.envios == []


async def test_acudientes_sin_dispositivos_no_generan_envios(client, notificador):
    dobles.RepoDispositivos.tokens_por_usuario = {}

    response = await client.post("/api/v1/novedades", json=CUERPO, headers=DOCENTE_7)

    assert response.status_code == 201
    assert notificador.envios == []


async def test_si_firebase_falla_la_novedad_se_guarda_y_el_error_se_registra(client, caplog):
    app.dependency_overrides[get_notificador] = lambda: dobles.NotificadorFalso(falla=True)
    try:
        with caplog.at_level(logging.ERROR):
            response = await client.post("/api/v1/novedades", json=CUERPO, headers=DOCENTE_7)
    finally:
        app.dependency_overrides.pop(get_notificador, None)

    assert response.status_code == 201
    assert len(dobles.RepoNovedades.creadas) == 1
    assert "No se pudo notificar la novedad" in caplog.text


async def test_el_servicio_sin_notificador_configurado_no_falla():
    servicio = novedades_service.NovedadService(SimpleNamespace())

    novedad = await servicio.create(NovedadCreate(**CUERPO), registrado_por=7)

    assert novedad.id_novedad == 1


# --- dispositivos ----------------------------------------------------------------------------


class _DispositivosFalsos:
    guardados: dict[str, dict] = {}

    def __init__(self, session):
        pass

    async def registrar(self, id_usuario, token_fcm, plataforma):
        fila = _DispositivosFalsos.guardados.setdefault(token_fcm, {"id": len(self.guardados) + 1})
        fila.update(id_usuario=id_usuario, plataforma=plataforma)
        return SimpleNamespace(id=fila["id"], token_fcm=token_fcm, plataforma=plataforma)

    async def eliminar_token(self, token_fcm, id_usuario):
        _DispositivosFalsos.guardados.pop(token_fcm, None)


@pytest.fixture
def dispositivos(monkeypatch):
    _DispositivosFalsos.guardados = {}
    monkeypatch.setattr(dispositivos_api, "DispositivoRepository", _DispositivosFalsos)


async def test_registrar_un_dispositivo_responde_201_y_repetirlo_no_lo_duplica(client, dispositivos):
    cuerpo = {"token_fcm": "token-del-telefono-123", "plataforma": "android"}

    primero = await client.post("/api/v1/dispositivos", json=cuerpo, headers=bearer("padre", 4, 4))
    segundo = await client.post("/api/v1/dispositivos", json=cuerpo, headers=bearer("padre", 4, 5))

    assert primero.status_code == segundo.status_code == 201
    assert len(_DispositivosFalsos.guardados) == 1
    assert _DispositivosFalsos.guardados["token-del-telefono-123"]["id_usuario"] == 5


async def test_un_token_o_plataforma_invalidos_responden_422(client, dispositivos):
    malo = await client.post(
        "/api/v1/dispositivos", json={"token_fcm": "x", "plataforma": "android"},
        headers=bearer("padre", 4),
    )
    plataforma = await client.post(
        "/api/v1/dispositivos", json={"token_fcm": "token-del-telefono-123", "plataforma": "nokia"},
        headers=bearer("padre", 4),
    )

    assert malo.status_code == plataforma.status_code == 422


async def test_registrar_un_dispositivo_exige_sesion(client, dispositivos):
    response = await client.post(
        "/api/v1/dispositivos", json={"token_fcm": "token-del-telefono-123", "plataforma": "ios"}
    )

    assert response.status_code == 401


async def test_al_cerrar_sesion_el_dispositivo_se_elimina(client, dispositivos):
    cuerpo = {"token_fcm": "token-del-telefono-123", "plataforma": "android"}
    await client.post("/api/v1/dispositivos", json=cuerpo, headers=bearer("padre", 4))

    response = await client.delete(
        "/api/v1/dispositivos/token-del-telefono-123", headers=bearer("padre", 4)
    )

    assert response.status_code == 204
    assert _DispositivosFalsos.guardados == {}
