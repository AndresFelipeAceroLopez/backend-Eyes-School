import pytest

from tests.integration.conftest import ADMIN, encabezado

pytestmark = pytest.mark.integration


async def test_el_admin_inicia_sesion_y_lista_usuarios(api):
    headers = await encabezado(api, ADMIN)

    respuesta = await api.get("/api/v1/usuarios", headers=headers)

    assert respuesta.status_code == 200
    assert len(respuesta.json()) >= 10
