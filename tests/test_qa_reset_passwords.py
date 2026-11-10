"""BE-INF-2: el script de contraseñas de QA solo actúa con ENVIRONMENT=qa."""

import pytest

from app.core.security import hash_password
from scripts.qa_reset_passwords import reset_passwords


class _Actualizador:
    def __init__(self):
        self.hashes: list[str] = []

    async def __call__(self, password_hash):
        self.hashes.append(password_hash)
        return [("admin@eyesschool.edu.co", "admin")]


async def test_en_produccion_el_script_no_hace_nada():
    actualizar = _Actualizador()

    reporte = await reset_passwords("production", "Colegio#2026", actualizar, hash_password)

    assert reporte == []
    assert actualizar.hashes == []


@pytest.mark.parametrize("entorno", ["development", "test", "", "QA-prod"])
async def test_en_otros_entornos_tampoco_actua(entorno):
    actualizar = _Actualizador()

    assert await reset_passwords(entorno, "Colegio#2026", actualizar, hash_password) == []
    assert actualizar.hashes == []


async def test_en_qa_asigna_la_contrasena_con_hash_y_reporta_correo_y_rol():
    actualizar = _Actualizador()

    reporte = await reset_passwords("qa", "Colegio#2026", actualizar, hash_password)

    assert reporte == [("admin@eyesschool.edu.co", "admin")]
    assert actualizar.hashes[0].startswith("$2")
    assert "Colegio#2026" not in str(reporte)


async def test_en_qa_una_contrasena_debil_se_rechaza():
    actualizar = _Actualizador()

    with pytest.raises(SystemExit):
        await reset_passwords("qa", "12345678", actualizar, hash_password)

    assert actualizar.hashes == []


async def test_en_qa_sin_contrasena_se_rechaza():
    with pytest.raises(SystemExit):
        await reset_passwords("qa", None, _Actualizador(), hash_password)
