"""BE-06: las notas van de 0.0 a 5.0, igual que en la web y la app."""

import pytest
from pydantic import ValidationError

from app.application.notas.schemas import NotaCreate, NotaUpdate
from tests.conftest import bearer


def _nota(valor):
    return NotaCreate(id_estudiante=1, id_materia=1, id_periodo=1, nota=valor)


@pytest.mark.parametrize("valor", [0.0, 0.1, 4.9, 5.0])
def test_las_notas_dentro_de_la_escala_se_aceptan(valor):
    assert _nota(valor).nota == valor


@pytest.mark.parametrize("valor", [-0.1, 5.1, 10])
def test_las_notas_fuera_de_la_escala_se_rechazan(valor):
    with pytest.raises(ValidationError):
        _nota(valor)


def test_actualizar_una_nota_tambien_respeta_la_escala():
    with pytest.raises(ValidationError):
        NotaUpdate(nota=5.1)
    assert NotaUpdate(nota=5.0).nota == 5.0


async def test_post_notas_con_5_1_responde_422(client):
    cuerpo = {"id_estudiante": 1, "id_materia": 1, "id_periodo": 1, "nota": 5.1}

    response = await client.post("/api/v1/notas", json=cuerpo, headers=bearer("docente", 1))

    assert response.status_code == 422
