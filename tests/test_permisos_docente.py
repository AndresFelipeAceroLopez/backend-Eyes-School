"""BE-11: el docente solo califica lo que dicta y solo edita sus propias novedades."""

from types import SimpleNamespace

import pytest

from app.application.notas import service as notas_service
from app.application.notas.schemas import NotaCreate
from app.application.novedades import service as novedades_service
from app.application.novedades.schemas import NovedadUpdate
from app.core.exceptions import ForbiddenException
from tests import dobles
from tests.conftest import bearer

DOCENTE = SimpleNamespace(nombre_rol="docente", id_usuario=7)
ADMIN = SimpleNamespace(nombre_rol="admin", id_usuario=1)


@pytest.fixture
def notas(monkeypatch):
    dobles.RepoNotas.reiniciar()
    dobles.RepoAsignaciones.consultas = []
    for nombre, doble in {
        "NotaRepository": dobles.RepoNotas,
        "ProfesorRepository": dobles.RepoProfesores,
        "EstudianteRepository": dobles.RepoEstudiantes,
        "AsignacionRepository": dobles.RepoAsignaciones,
    }.items():
        monkeypatch.setattr(notas_service, nombre, doble)
    monkeypatch.setattr(dobles.RepoProfesores, "profesor", SimpleNamespace(id_profesor=3))
    return notas_service.NotaService(SimpleNamespace())


def _nota():
    return NotaCreate(id_estudiante=10, id_materia=2, id_periodo=1, nota=4.0)


async def test_un_docente_con_asignacion_crea_la_nota(notas, monkeypatch):
    monkeypatch.setattr(dobles.RepoAsignaciones, "dicta", True)

    nota = await notas.create(_nota(), DOCENTE)

    assert nota.nota == 4.0
    # materia 2 en el curso actual (5) del estudiante, con el profesor del token
    assert dobles.RepoAsignaciones.consultas == [(3, 2, 5)]


async def test_un_docente_sin_asignacion_no_puede_calificar(notas, monkeypatch):
    monkeypatch.setattr(dobles.RepoAsignaciones, "dicta", False)

    with pytest.raises(ForbiddenException):
        await notas.create(_nota(), DOCENTE)

    assert dobles.RepoNotas.creadas == []


async def test_un_docente_sin_asignacion_no_puede_editar_ni_borrar_una_nota(notas, monkeypatch):
    monkeypatch.setattr(dobles.RepoAsignaciones, "dicta", False)
    dobles.RepoNotas.por_id = {
        1: SimpleNamespace(id_nota=1, id_estudiante=10, id_materia=2, nota=3.0)
    }

    from app.application.notas.schemas import NotaUpdate

    with pytest.raises(ForbiddenException):
        await notas.update(1, NotaUpdate(nota=4.0), DOCENTE)
    with pytest.raises(ForbiddenException):
        await notas.delete(1, DOCENTE)


async def test_el_docente_lista_solo_las_notas_de_sus_cursos(notas):
    await notas.list(actor=DOCENTE)
    await notas.list(actor=ADMIN)

    assert dobles.RepoNotas.filtros[0]["id_profesor"] == 3
    assert dobles.RepoNotas.filtros[1]["id_profesor"] is None


# --- novedades ----------------------------------------------------------------------------


@pytest.fixture
def novedades(monkeypatch):
    dobles.RepoNovedades.reiniciar()
    dobles.RepoNovedades.por_id = {1: dobles.novedad(id_novedad=1, registrado_por=9)}
    for nombre, doble in {
        "NovedadRepository": dobles.RepoNovedades,
        "TipoNovedadRepository": dobles.RepoTiposNovedad,
        "PadreRepository": dobles.RepoPadres,
        "EstudianteRepository": dobles.RepoEstudiantes,
        "DispositivoRepository": dobles.RepoDispositivos,
    }.items():
        monkeypatch.setattr(novedades_service, nombre, doble)
    return novedades_service.NovedadService(SimpleNamespace())


async def test_un_docente_no_edita_la_novedad_de_otro_docente(novedades):
    with pytest.raises(ForbiddenException):
        await novedades.update(1, NovedadUpdate(descripcion="x"), DOCENTE)
    with pytest.raises(ForbiddenException):
        await novedades.delete(1, DOCENTE)

    assert dobles.RepoNovedades.borradas == []


async def test_el_admin_edita_la_novedad_ajena(novedades):
    actualizada = await novedades.update(1, NovedadUpdate(descripcion="Corregida"), ADMIN)

    assert actualizada.descripcion == "Corregida"


async def test_el_autor_edita_y_borra_su_novedad(novedades):
    autor = SimpleNamespace(nombre_rol="docente", id_usuario=9)

    await novedades.update(1, NovedadUpdate(descripcion="Ajuste"), autor)
    await novedades.delete(1, autor)

    assert dobles.RepoNovedades.borradas == [1]


async def test_un_docente_sin_asignacion_recibe_403_por_http(client, monkeypatch, sin_base_de_datos):
    dobles.RepoNotas.reiniciar()
    for nombre, doble in {
        "NotaRepository": dobles.RepoNotas,
        "ProfesorRepository": dobles.RepoProfesores,
        "EstudianteRepository": dobles.RepoEstudiantes,
        "AsignacionRepository": dobles.RepoAsignaciones,
    }.items():
        monkeypatch.setattr(notas_service, nombre, doble)
    monkeypatch.setattr(dobles.RepoAsignaciones, "dicta", False)
    cuerpo = {"id_estudiante": 10, "id_materia": 2, "id_periodo": 1, "nota": 4.0}

    response = await client.post("/api/v1/notas", json=cuerpo, headers=bearer("docente", 1, 7))

    assert response.status_code == 403
