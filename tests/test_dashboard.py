"""BE-03: el inicio del estudiante y del padre ya no falla con AttributeError (500)."""

from types import SimpleNamespace

import pytest

from app.api.v1 import dashboard as dashboard_api
from app.application.dashboard.schemas import EstudianteDashboard
from tests.conftest import bearer

pytestmark = pytest.mark.usefixtures("sin_base_de_datos")

DASHBOARD = EstudianteDashboard(
    promedio_general=4.2, porcentaje_asistencia=90.0, novedades_pendientes=1, periodo_actual=1
)


class _ServicioFalso:
    """Dashboard con el estudiante ya resuelto: registra qué estudiante se pidió."""

    pedidos: list[int | None] = []

    def __init__(self, db):
        pass

    async def resolver_estudiante(self, current_user, id_estudiante=None):
        _ServicioFalso.pedidos.append(id_estudiante)
        return 10

    async def get_estudiante_dashboard(self, id_estudiante):
        assert id_estudiante == 10
        return DASHBOARD


@pytest.fixture(autouse=True)
def servicio(monkeypatch):
    _ServicioFalso.pedidos = []
    monkeypatch.setattr(dashboard_api, "DashboardService", _ServicioFalso)


async def test_el_estudiante_ve_su_inicio(client):
    response = await client.get("/api/v1/dashboard/estudiante", headers=bearer("estudiante", 2))

    assert response.status_code == 200
    assert response.json()["promedio_general"] == 4.2


async def test_el_padre_ve_el_inicio_del_estudiante_vinculado(client):
    response = await client.get("/api/v1/dashboard/estudiante", headers=bearer("padre", 4))

    assert response.status_code == 200
    assert response.json()["porcentaje_asistencia"] == 90.0


async def test_el_docente_no_tiene_inicio_de_estudiante(client):
    response = await client.get("/api/v1/dashboard/estudiante", headers=bearer("docente", 1))

    assert response.status_code == 403


async def test_el_padre_puede_pedir_el_inicio_de_uno_de_sus_hijos(client):
    await client.get(
        "/api/v1/dashboard/estudiante?id_estudiante=11", headers=bearer("padre", 4)
    )

    assert _ServicioFalso.pedidos == [11]


# --- resolución del estudiante (servicio real con repositorios dobles) ---------------------


class _PadresFalsos:
    def __init__(self, session):
        pass

    async def ids_estudiantes(self, id_usuario):
        return {10, 11}

    async def get_by_usuario(self, id_usuario):
        return SimpleNamespace(id_estudiante=10)


class _EstudiantesFalsos:
    def __init__(self, session):
        pass

    async def get_by_usuario(self, id_usuario):
        return SimpleNamespace(id_estudiante=77)


@pytest.fixture
def repos(monkeypatch):
    from app.application.dashboard import service

    monkeypatch.setattr(service, "PadreRepository", _PadresFalsos)
    monkeypatch.setattr(service, "EstudianteRepository", _EstudiantesFalsos)
    return service.DashboardService(SimpleNamespace())


async def test_resolver_estudiante_de_un_estudiante_es_el_suyo(repos):
    usuario = SimpleNamespace(nombre_rol="estudiante", id_usuario=5)

    assert await repos.resolver_estudiante(usuario) == 77


async def test_resolver_estudiante_de_un_padre_usa_el_primer_hijo_si_no_se_indica(repos):
    usuario = SimpleNamespace(nombre_rol="padre", id_usuario=4)

    assert await repos.resolver_estudiante(usuario) == 10
    assert await repos.resolver_estudiante(usuario, 11) == 11
