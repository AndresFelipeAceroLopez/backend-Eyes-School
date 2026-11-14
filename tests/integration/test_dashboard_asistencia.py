"""N-04 contra PostgreSQL: los registros de asistencia borrados (borrado lógico) no cuentan
en el porcentaje del inicio, que nunca pasa de 100.

En QA, con registros «Presente» borrados, el inicio del estudiante 1 mostraba 140,6 %.
"""

import pytest
from sqlalchemy import func, select

from app.application.dashboard.service import porcentaje_asistencia
from app.infrastructure.models.asistencia import AsistenciaModel
from tests.integration.conftest import ADMIN, ESTUDIANTE, encabezado

pytestmark = pytest.mark.integration


async def _crear_y_borrar(api, admin, fecha: str) -> None:
    creada = await api.post(
        "/api/v1/asistencia",
        json={
            "id_estudiante": 1,
            "fecha": fecha,
            "estado": "Presente",
            "tipo": "clase",
            "registrado_por": 1,
        },
        headers=admin,
    )
    assert creada.status_code == 201, creada.text
    borrada = await api.delete(
        f"/api/v1/asistencia/{creada.json()['id_asistencia']}", headers=admin
    )
    assert borrada.status_code == 204


async def test_los_registros_borrados_no_inflan_el_porcentaje(api, db):
    admin = await encabezado(api, ADMIN)
    await _crear_y_borrar(api, admin, "2026-06-20")
    await _crear_y_borrar(api, admin, "2026-06-21")

    activos = (await db.execute(
        select(AsistenciaModel.estado, func.count())
        .where(AsistenciaModel.id_estudiante == 1, AsistenciaModel.activo.is_(True))
        .group_by(AsistenciaModel.estado)
    )).all()
    esperado = porcentaje_asistencia({estado: cantidad for estado, cantidad in activos})

    estudiante = await encabezado(api, ESTUDIANTE)
    respuesta = await api.get("/api/v1/dashboard/estudiante", headers=estudiante)

    assert respuesta.status_code == 200
    porcentaje = respuesta.json()["porcentaje_asistencia"]
    assert porcentaje <= 100
    assert porcentaje == pytest.approx(esperado)
