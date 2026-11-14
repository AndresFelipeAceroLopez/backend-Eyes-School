"""BE-15 y BE-19: el boletín se genera en memoria; sin notas responde 404 con el mensaje del CA."""

from types import SimpleNamespace

import pytest

from app.api.v1 import notas as notas_api
from app.application.notas import service as notas_service
from app.core.exceptions import NotFoundException

MENSAJE = "No hay datos disponibles para generar el boletín."


class _RepoBoletin:
    notas: list = []

    def __init__(self, session):
        pass

    async def get_with_filters(self, **filtros):
        return _RepoBoletin.notas

    async def get_estudiante_con_usuario(self, id_estudiante):
        usuario = SimpleNamespace(
            primer_nombre="Ana", segundo_nombre=None, primer_apellido="Gómez", segundo_apellido=None
        )
        return SimpleNamespace(codigo_estudiante="E-10", usuario=usuario)

    async def get_promedio_estudiante(self, id_estudiante):
        return 4.0


def _nota(periodo: int, nombre: str, valor: float):
    return SimpleNamespace(
        id_periodo=periodo, id_materia=1, nota=valor, materia=SimpleNamespace(nombre_materia=nombre)
    )


@pytest.fixture
def servicio(monkeypatch):
    _RepoBoletin.notas = []
    monkeypatch.setattr(notas_service, "NotaRepository", _RepoBoletin)
    for nombre in ("ProfesorRepository", "EstudianteRepository", "AsignacionRepository"):
        monkeypatch.setattr(notas_service, nombre, lambda s: None)
    return notas_service.NotaService(SimpleNamespace())


async def test_un_estudiante_sin_notas_lanza_not_found_con_el_texto_exacto(servicio):
    with pytest.raises(NotFoundException) as error:
        await servicio.generate_boletin_pdf(10)

    assert error.value.status_code == 404
    assert error.value.detail == MENSAJE


async def test_un_estudiante_con_notas_recibe_un_pdf_en_memoria(servicio, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    _RepoBoletin.notas = [_nota(1, "Matemáticas", 4.5), _nota(2, "Español", 3.5)]

    contenido = await servicio.generate_boletin_pdf(10)

    assert isinstance(contenido, bytes)
    assert contenido.startswith(b"%PDF")
    assert list(tmp_path.iterdir()) == []  # no queda ningún archivo temporal


class _ServicioHttp:
    def __init__(self, db):
        pass

    async def generate_boletin_pdf(self, id_estudiante):
        if id_estudiante == 11:
            raise NotFoundException(MENSAJE)
        return b"%PDF-1.4 falso"


@pytest.fixture
def http(monkeypatch, sin_base_de_datos):
    async def permitido(db, current_user, id_estudiante):
        return None

    monkeypatch.setattr(notas_api, "NotaService", _ServicioHttp)
    monkeypatch.setattr(notas_api, "assert_acceso_estudiante", permitido)


async def test_http_sin_notas_responde_404_con_el_mensaje(client, http):
    from tests.conftest import bearer

    response = await client.get(
        "/api/v1/notas/estudiantes/11/boletin/pdf", headers=bearer("estudiante", 2)
    )

    assert response.status_code == 404
    assert response.json()["detail"] == MENSAJE


async def test_http_con_notas_responde_pdf_adjunto(client, http):
    from tests.conftest import bearer

    response = await client.get(
        "/api/v1/notas/estudiantes/10/boletin/pdf", headers=bearer("estudiante", 2)
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "boletin_10.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")
