"""BE-08: una entrada y una salida por estudiante y día; la salida exige una entrada previa."""

from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.application.asistencia import service as asistencia_service
from app.application.asistencia.schemas import AsistenciaCreate
from app.core.exceptions import BusinessRuleException, ConflictException

HOY = date(2026, 11, 2)


class _RepoFalso:
    """Repositorio de asistencia: `existentes` son los tipos ya registrados ese día."""

    existentes: set[str] = set()
    consultas: list[str] = []
    creados: list[dict] = []

    def __init__(self, session):
        pass

    async def exists_for_day(self, id_estudiante, fecha, tipo):
        _RepoFalso.consultas.append(tipo)
        return tipo in _RepoFalso.existentes

    async def create(self, data):
        _RepoFalso.creados.append(data)
        return SimpleNamespace(
            id_asistencia=1, fecha_registro=datetime(2026, 11, 2, 7), codigo_qr=None, activo=True,
            **data,
        )


@pytest.fixture
def servicio(monkeypatch):
    _RepoFalso.existentes, _RepoFalso.consultas, _RepoFalso.creados = set(), [], []
    monkeypatch.setattr(asistencia_service, "AsistenciaRepository", _RepoFalso)
    monkeypatch.setattr(asistencia_service, "AsistenciaAulaRepository", lambda s: None)
    monkeypatch.setattr(asistencia_service, "EstudianteRepository", lambda s: None)
    return asistencia_service.AsistenciaService(SimpleNamespace())


def _registro(tipo):
    return AsistenciaCreate(id_estudiante=10, fecha=HOY, estado="Presente", tipo=tipo)


async def test_la_primera_entrada_se_guarda(servicio):
    await servicio.create(_registro("entrada"), registrado_por=7)

    assert len(_RepoFalso.creados) == 1


async def test_la_segunda_entrada_responde_409_y_no_se_guarda(servicio):
    _RepoFalso.existentes = {"entrada"}

    with pytest.raises(ConflictException) as error:
        await servicio.create(_registro("entrada"), registrado_por=7)

    assert "Ya existe un registro de entrada" in error.value.detail
    assert _RepoFalso.creados == []


async def test_la_salida_despues_de_la_entrada_se_guarda(servicio):
    _RepoFalso.existentes = {"entrada"}

    await servicio.create(_registro("salida"), registrado_por=7)

    assert len(_RepoFalso.creados) == 1


async def test_la_segunda_salida_responde_409(servicio):
    _RepoFalso.existentes = {"entrada", "salida"}

    with pytest.raises(ConflictException):
        await servicio.create(_registro("salida"), registrado_por=7)


async def test_dos_registros_de_clase_se_guardan_sin_consultar_duplicados(servicio):
    await servicio.create(_registro("clase"), registrado_por=7)
    await servicio.create(_registro("clase"), registrado_por=7)

    assert len(_RepoFalso.creados) == 2
    assert _RepoFalso.consultas == []


async def test_una_salida_sin_entrada_previa_responde_400(servicio):
    with pytest.raises(BusinessRuleException) as error:
        await servicio.create(_registro("salida"), registrado_por=7)

    assert error.value.status_code == 400
    assert error.value.detail == "No hay entrada registrada hoy para este estudiante"
    assert _RepoFalso.creados == []
