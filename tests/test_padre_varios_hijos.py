"""BE-07: un padre con varios hijos ya no provoca error 500 y solo accede a los suyos."""

from types import SimpleNamespace

import pytest

from app.application.common import authz
from app.application.dashboard import service as dashboard_service
from app.application.padres import service as padres_service
from app.core.exceptions import ForbiddenException
from tests.conftest import bearer

pytestmark = pytest.mark.usefixtures("sin_base_de_datos")

PADRE = SimpleNamespace(nombre_rol="padre", id_usuario=4)


def _vinculo(id_padre: int, id_estudiante: int, nombre: str):
    usuario = SimpleNamespace(
        primer_nombre=nombre, primer_apellido="Pérez", numero_documento=f"doc{id_estudiante}"
    )
    return SimpleNamespace(
        id_padre=id_padre, id_usuario=4, id_estudiante=id_estudiante, parentesco="Madre",
        ocupacion=None,
        estudiante=SimpleNamespace(id_curso_actual=id_estudiante * 10, usuario=usuario),
    )


class _PadresConDosHijos:
    vinculos: list = []

    def __init__(self, session):
        pass

    async def ids_estudiantes(self, id_usuario):
        return {v.id_estudiante for v in self.vinculos}

    async def list_by_usuario(self, id_usuario):
        return list(self.vinculos)

    async def get_by_usuario(self, id_usuario):
        return self.vinculos[0] if self.vinculos else None


@pytest.fixture
def dos_hijos(monkeypatch):
    monkeypatch.setattr(authz, "PadreRepository", _PadresConDosHijos)
    monkeypatch.setattr(padres_service, "PadreRepository", _PadresConDosHijos)
    monkeypatch.setattr(dashboard_service, "PadreRepository", _PadresConDosHijos)
    monkeypatch.setattr(
        _PadresConDosHijos, "vinculos", [_vinculo(1, 10, "Ana"), _vinculo(2, 11, "Luis")]
    )


async def test_el_acudiente_accede_al_primer_hijo(dos_hijos):
    await authz.assert_acceso_estudiante(SimpleNamespace(), PADRE, 10)


async def test_el_acudiente_accede_al_segundo_hijo(dos_hijos):
    await authz.assert_acceso_estudiante(SimpleNamespace(), PADRE, 11)


async def test_el_acudiente_no_accede_a_un_tercer_estudiante(dos_hijos):
    with pytest.raises(ForbiddenException):
        await authz.assert_acceso_estudiante(SimpleNamespace(), PADRE, 12)


async def test_mis_hijos_lista_los_dos_vinculos(client, dos_hijos):
    response = await client.get("/api/v1/padres/me/hijos", headers=bearer("padre", 4, 4))

    assert response.status_code == 200
    hijos = response.json()
    assert [h["id_estudiante"] for h in hijos] == [10, 11]
    assert hijos[0] == {
        "id_estudiante": 10, "nombre_estudiante": "Ana Pérez", "documento_estudiante": "doc10",
        "parentesco": "Madre", "id_curso_actual": 100,
    }


async def test_mis_hijos_sin_vinculos_responde_lista_vacia(client, dos_hijos, monkeypatch):
    monkeypatch.setattr(_PadresConDosHijos, "vinculos", [])

    response = await client.get("/api/v1/padres/me/hijos", headers=bearer("padre", 4, 4))

    assert response.status_code == 200
    assert response.json() == []


async def test_el_dashboard_de_un_estudiante_ajeno_recibe_403(client, dos_hijos):
    response = await client.get(
        "/api/v1/dashboard/padre?id_estudiante=12", headers=bearer("padre", 4, 4)
    )

    assert response.status_code == 403


async def test_padres_me_sin_parametro_devuelve_el_primer_hijo(client, dos_hijos):
    response = await client.get("/api/v1/padres/me", headers=bearer("padre", 4, 4))

    assert response.status_code == 200
    assert response.json()["id_estudiante"] == 10


async def test_padres_me_con_un_hijo_ajeno_recibe_403(client, dos_hijos):
    response = await client.get("/api/v1/padres/me?id_estudiante=12", headers=bearer("padre", 4, 4))

    assert response.status_code == 403


async def test_padres_me_sin_vinculos_responde_404(client, dos_hijos, monkeypatch):
    monkeypatch.setattr(_PadresConDosHijos, "vinculos", [])

    response = await client.get("/api/v1/padres/me", headers=bearer("padre", 4, 4))

    assert response.status_code == 404
