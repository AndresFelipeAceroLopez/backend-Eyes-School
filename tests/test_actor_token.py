"""BE-10: quién registró asistencia, notas y novedades sale del token, no del cuerpo."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from app.application.asistencia import service as asistencia_service
from app.application.notas import service as notas_service
from app.application.novedades import service as novedades_service
from tests import dobles
from tests.conftest import bearer

pytestmark = pytest.mark.usefixtures("sin_base_de_datos")

DOCENTE_7 = bearer("docente", 1, id_usuario=7)


class _AsistenciaRepo:
    creadas: list[dict] = []

    def __init__(self, session):
        pass

    async def exists_for_day(self, *args):
        return False

    async def create(self, data):
        _AsistenciaRepo.creadas.append(data)
        return SimpleNamespace(
            id_asistencia=1, fecha_registro=datetime(2026, 11, 2), codigo_qr=None, activo=True, **data
        )


async def test_asistencia_se_guarda_con_el_docente_del_token(client, monkeypatch):
    _AsistenciaRepo.creadas = []
    monkeypatch.setattr(asistencia_service, "AsistenciaRepository", _AsistenciaRepo)
    monkeypatch.setattr(asistencia_service, "AsistenciaAulaRepository", lambda s: None)
    monkeypatch.setattr(asistencia_service, "EstudianteRepository", lambda s: None)
    cuerpo = {
        "id_estudiante": 10, "fecha": "2026-11-02", "estado": "Presente", "tipo": "clase",
        "registrado_por": 999,
    }

    response = await client.post("/api/v1/asistencia", json=cuerpo, headers=DOCENTE_7)

    assert response.status_code == 201
    assert _AsistenciaRepo.creadas[0]["registrado_por"] == 7
    assert response.json()["registrado_por"] == 7


async def test_nota_se_guarda_con_el_docente_del_token(client, monkeypatch):
    dobles.RepoNotas.reiniciar()
    for nombre, doble in {
        "NotaRepository": dobles.RepoNotas,
        "ProfesorRepository": dobles.RepoProfesores,
        "EstudianteRepository": dobles.RepoEstudiantes,
        "AsignacionRepository": dobles.RepoAsignaciones,
    }.items():
        monkeypatch.setattr(notas_service, nombre, doble)
    monkeypatch.setattr(dobles.RepoAsignaciones, "dicta", True)
    cuerpo = {
        "id_estudiante": 10, "id_materia": 2, "id_periodo": 1, "nota": 4.5, "registrado_por": 999,
    }

    response = await client.post("/api/v1/notas", json=cuerpo, headers=DOCENTE_7)

    assert response.status_code == 201
    assert dobles.RepoNotas.creadas[0]["registrado_por"] == 7


async def test_novedad_se_guarda_con_el_usuario_del_token(client, monkeypatch):
    dobles.RepoNovedades.reiniciar()
    dobles.RepoPadres.padres = []
    monkeypatch.setattr(novedades_service, "NovedadRepository", dobles.RepoNovedades)
    monkeypatch.setattr(novedades_service, "TipoNovedadRepository", dobles.RepoTiposNovedad)
    monkeypatch.setattr(novedades_service, "PadreRepository", dobles.RepoPadres)
    monkeypatch.setattr(novedades_service, "EstudianteRepository", dobles.RepoEstudiantes)
    monkeypatch.setattr(novedades_service, "DispositivoRepository", dobles.RepoDispositivos)
    cuerpo = {
        "id_estudiante": 10, "id_tipo_novedad": 1, "fecha": "2026-11-02",
        "descripcion": "Llegó tarde", "registrado_por": 999,
    }

    response = await client.post("/api/v1/novedades", json=cuerpo, headers=DOCENTE_7)

    assert response.status_code == 201
    assert dobles.RepoNovedades.creadas[0]["registrado_por"] == 7
