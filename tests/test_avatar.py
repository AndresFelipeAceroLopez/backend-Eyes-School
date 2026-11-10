"""BE-14: el avatar se valida por su contenido real, su formato y su tamaño."""

import io
import os

import pytest
from PIL import Image

from app.application.auth import service as auth_service
from tests import dobles
from tests.conftest import bearer

pytestmark = pytest.mark.usefixtures("sin_base_de_datos")


@pytest.fixture(autouse=True)
def entorno(monkeypatch, tmp_path):
    dobles.RepoUsuariosAuth.reiniciar(dobles.usuario_auth())
    monkeypatch.setattr(auth_service, "UsuarioRepository", dobles.RepoUsuariosAuth)
    monkeypatch.setattr(auth_service, "AVATAR_DIR", str(tmp_path))
    return tmp_path


def _imagen(formato="PNG", tamano=(200, 200)) -> bytes:
    # Ruido para que el archivo pese algunos KB y no se comprima a nada.
    imagen = Image.frombytes("RGB", tamano, os.urandom(tamano[0] * tamano[1] * 3))
    salida = io.BytesIO()
    imagen.save(salida, format=formato)
    return salida.getvalue()


async def _subir(client, nombre, contenido, content_type):
    return await client.post(
        "/api/v1/auth/me/avatar",
        files={"file": (nombre, contenido, content_type)},
        headers=bearer("docente", 1, 7),
    )


async def test_un_png_real_se_guarda_con_extension_png(client, entorno):
    response = await _subir(client, "foto.png", _imagen("PNG"), "image/png")

    assert response.status_code == 200
    guardado = response.json().rsplit("/", 1)[-1]
    assert guardado.endswith(".png")
    assert (entorno / guardado).is_file()
    assert dobles.RepoUsuariosAuth.usuario.foto_perfil == response.json()


async def test_la_extension_la_decide_el_formato_detectado_no_el_nombre(client):
    response = await _subir(client, "foto.png", _imagen("JPEG"), "image/png")

    assert response.status_code == 200
    assert response.json().endswith(".jpg")


async def test_un_texto_con_nombre_png_se_rechaza(client, entorno):
    response = await _subir(client, "foto.png", b"esto no es una imagen", "image/png")

    assert response.status_code == 400
    assert list(entorno.iterdir()) == []


async def test_una_pagina_html_con_content_type_de_imagen_se_rechaza(client, entorno):
    html = b"<html><script>alert(document.cookie)</script></html>"

    response = await _subir(client, "pagina.html", html, "image/png")

    assert response.status_code == 400
    assert list(entorno.iterdir()) == []


async def test_un_svg_con_script_se_rechaza(client):
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'

    response = await _subir(client, "x.svg", svg, "image/svg+xml")

    assert response.status_code == 400


async def test_una_imagen_de_3_mb_se_rechaza(client, entorno):
    response = await _subir(client, "grande.png", b"\x89PNG" + b"0" * (3 * 1024 * 1024), "image/png")

    assert response.status_code == 400
    assert "2 MB" in response.json()["detail"]
    assert list(entorno.iterdir()) == []


async def test_un_formato_de_imagen_no_permitido_se_rechaza(client):
    response = await _subir(client, "x.gif", _imagen("GIF", (20, 20)), "image/gif")

    assert response.status_code == 400
