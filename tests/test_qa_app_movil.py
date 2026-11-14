"""Defectos de la API encontrados en las pruebas de la app móvil (11/11/2026).

N-04: el porcentaje de asistencia del inicio llegaba a 140,6 %.
N-13: se podía guardar una novedad con la descripción vacía.
"""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.application.dashboard.service import DashboardService, porcentaje_asistencia
from app.application.novedades.schemas import NovedadCreate, NovedadUpdate
from tests.conftest import bearer

# --- N-04 · porcentaje de asistencia ------------------------------------------------------


def test_sin_registros_no_hay_porcentaje():
    assert porcentaje_asistencia({}) is None


def test_todo_presente_es_100():
    assert porcentaje_asistencia({"Presente": 4}) == 100.0


def test_la_llegada_tarde_cuenta_como_asistencia():
    # Mismo criterio que la app y el panel web (N-20).
    assert porcentaje_asistencia({"Presente": 2, "Tarde": 1, "Ausente": 1}) == 75.0


def test_excusa_y_suspension_no_cuentan_como_asistencia():
    assert porcentaje_asistencia({"Presente": 1, "Excusa": 1, "Suspensión": 2}) == 25.0


@pytest.mark.parametrize(
    "conteos",
    [
        {"Presente": 7},
        {"Presente": 3, "Tarde": 9},
        {"Presente": 1, "Ausente": 0},
    ],
)
def test_nunca_pasa_de_100(conteos):
    assert porcentaje_asistencia(conteos) <= 100.0


class _SesionQueRegistra:
    """Devuelve filas (estado, cantidad) y guarda la consulta que recibió."""

    def __init__(self, filas):
        self.filas = filas
        self.consultas = []

    async def execute(self, stmt):
        self.consultas.append(str(stmt.compile(compile_kwargs={"literal_binds": True})))
        return SimpleNamespace(all=lambda: self.filas)


async def test_el_porcentaje_sale_de_una_sola_consulta_sobre_registros_activos():
    sesion = _SesionQueRegistra([("Presente", 2), ("Ausente", 1)])
    servicio = DashboardService(sesion)

    porcentaje = await servicio._get_porcentaje_asistencia(1)

    assert porcentaje == pytest.approx(66.67)
    assert len(sesion.consultas) == 1
    sql = sesion.consultas[0].lower().replace('public.', '').replace('"', '')
    # Numerador y denominador salen del mismo conjunto: solo registros activos.
    assert "asistencia.activo = true" in sql
    assert "group by asistencia.estado" in sql
    assert "asistencia.idestudiante = 1" in sql


# --- N-13 · descripción obligatoria de la novedad ------------------------------------------

CUERPO = {"id_estudiante": 1, "id_tipo_novedad": 2, "fecha": "2026-11-11"}


@pytest.mark.parametrize("descripcion", ["", "   ", "\n\t"])
def test_una_novedad_sin_descripcion_se_rechaza(descripcion):
    with pytest.raises(ValidationError):
        NovedadCreate(**CUERPO, descripcion=descripcion)


def test_la_descripcion_se_guarda_sin_espacios_de_mas():
    assert NovedadCreate(**CUERPO, descripcion="  No entregó la tarea  ").descripcion == (
        "No entregó la tarea"
    )


def test_al_editar_tampoco_se_puede_dejar_vacia():
    with pytest.raises(ValidationError):
        NovedadUpdate(descripcion="  ")
    assert NovedadUpdate().descripcion is None


@pytest.mark.usefixtures("sin_base_de_datos")
async def test_la_api_responde_422_a_una_novedad_vacia(client):
    respuesta = await client.post(
        "/api/v1/novedades",
        json={**CUERPO, "descripcion": ""},
        headers=bearer("docente", 1),
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"][0]["loc"][-1] == "descripcion"
