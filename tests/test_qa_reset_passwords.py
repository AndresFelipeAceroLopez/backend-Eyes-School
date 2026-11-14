"""BE-INF-2: protecciones del script de contraseñas de QA.

Cambia la contraseña de TODOS los usuarios de la base a la que se conecte, así que cada
protección se prueba por separado: el entorno, el origen de DATABASE_URL y, sobre todo, que la
base realmente conectada sea la que se declaró.
"""

import pytest

from app.core.security import hash_password
from scripts.qa_reset_passwords import (
    exigir_database_url_del_entorno,
    main,
    reset_passwords,
    verificar_base,
)


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


# --- Protecciones que miran la base y no una variable (BE-INF-2, puntos 2 y 3) ---


def test_sin_database_url_en_el_entorno_el_script_se_niega(monkeypatch):
    """El .env apunta a producción: si la variable no está en la terminal, no se conecta."""
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(SystemExit) as error:
        exigir_database_url_del_entorno()

    assert "DATABASE_URL" in str(error.value)


def test_con_database_url_en_el_entorno_continua(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@host/qaeyesschool")

    exigir_database_url_del_entorno()  # no lanza


def test_si_la_base_conectada_no_es_la_esperada_no_escribe():
    """Lo que se comprueba es la base realmente conectada, no la variable que se pegó."""
    with pytest.raises(SystemExit) as error:
        verificar_base("eyesschool_prod", "qaeyesschool")

    assert "eyesschool_prod" in str(error.value)
    assert "No se cambió ninguna contraseña" in str(error.value)


def test_si_la_base_conectada_es_la_esperada_continua():
    verificar_base("qaeyesschool", "qaeyesschool")  # no lanza


def test_main_exige_el_argumento_base():
    """Sin --base no hay con qué comparar current_database(): argparse debe cortar."""
    import asyncio

    with pytest.raises(SystemExit):
        asyncio.run(main([]))
