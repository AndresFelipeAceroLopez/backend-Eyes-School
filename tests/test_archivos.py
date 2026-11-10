"""BE-15: solo los avatares son públicos; los reportes salen únicamente por el endpoint con token."""

import os
from pathlib import Path

from main import app


async def test_un_reporte_no_se_descarga_por_static(client):
    # Aunque el archivo exista en disco, /static/reportes no está montado.
    ruta = Path("static/reportes/prueba-be15.pdf")
    ruta.write_bytes(b"%PDF-1.4 contenido reservado")
    try:
        response = await client.get("/static/reportes/prueba-be15.pdf")
    finally:
        ruta.unlink(missing_ok=True)

    assert response.status_code == 404


async def test_los_avatares_siguen_siendo_publicos(client):
    ruta = Path("static/avatars/prueba-be15.png")
    ruta.write_bytes(b"\x89PNG")
    try:
        response = await client.get("/static/avatars/prueba-be15.png")
    finally:
        ruta.unlink(missing_ok=True)

    assert response.status_code == 200


def test_solo_la_carpeta_de_avatares_esta_montada():
    montajes = {r.path for r in app.routes if r.__class__.__name__ == "Mount"}

    assert "/static/avatars" in montajes
    assert "/static" not in montajes
    assert os.path.isdir("static/reportes")


async def test_la_descarga_de_reportes_exige_token(client):
    response = await client.get("/api/v1/reportes/1/archivo")

    assert response.status_code == 401
