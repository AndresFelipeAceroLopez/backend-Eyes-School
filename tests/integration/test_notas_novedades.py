"""Notas, novedades, notificaciones, boletín y avatar contra PostgreSQL
(CP-INT-041 a 058, 072).

Seed: Carlos (usuario 2, profesor 1) dicta la materia 1 en los cursos 1, 2, 5 y 6; María
(usuario 5, profesor 2) dicta en los cursos 1, 3 y 5; Lucía (usuario 9, profesor 3), materia 2
en el curso 1. Los estudiantes 1 y 2 son del curso 1; el 3, del curso 2.
"""

import io
import os

import pytest
from PIL import Image
from sqlalchemy import func, select, text

from app.application.auth import service as auth_service
from app.infrastructure.models.dispositivos import DispositivoModel
from app.infrastructure.notificador_firebase import get_notificador
from app.infrastructure.repositories.notas_repository import NotaRepository
from main import app
from tests.dobles import NotificadorFalso
from tests.integration.conftest import (
    ADMIN,
    DOCENTE,
    DOCENTE_AJENO,
    ESTUDIANTE,
    PADRE_DOS_HIJOS,
    PADRE_UN_HIJO,
    encabezado,
)

pytestmark = pytest.mark.integration

MARIA = "maria.herrera@eyes.edu.co"


def _nota(**campos):
    return {"id_estudiante": 1, "id_materia": 1, "id_periodo": 2, "nota": 4.0, **campos}


# --- notas ------------------------------------------------------------------------------------


async def test_el_docente_con_asignacion_crea_la_nota_a_su_nombre(api):
    carlos = await encabezado(api, DOCENTE)

    respuesta = await api.post(
        "/api/v1/notas", json=_nota(registrado_por=9), headers=carlos
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["registrado_por"] == 2


async def test_una_nota_repetida_para_estudiante_materia_y_periodo_responde_409(api):
    carlos = await encabezado(api, DOCENTE)

    # El seed ya trae la nota del estudiante 1, materia 1, periodo 1.
    respuesta = await api.post("/api/v1/notas", json=_nota(id_periodo=1), headers=carlos)

    assert respuesta.status_code == 409


async def test_una_nota_fuera_de_la_escala_responde_422(api):
    carlos = await encabezado(api, DOCENTE)

    assert (await api.post("/api/v1/notas", json=_nota(nota=5.1), headers=carlos)).status_code == 422
    assert (await api.post("/api/v1/notas", json=_nota(nota=5.0), headers=carlos)).status_code == 201


async def test_actualizar_una_nota_a_5_1_responde_422(api):
    carlos = await encabezado(api, DOCENTE)

    assert (await api.put("/api/v1/notas/1", json={"nota": 5.1}, headers=carlos)).status_code == 422
    assert (await api.put("/api/v1/notas/1", json={"nota": 4.9}, headers=carlos)).status_code == 200


async def test_un_docente_sin_asignacion_no_califica_esa_materia(api):
    lucia = await encabezado(api, DOCENTE_AJENO)

    # Lucía no dicta la materia 1 en el curso 1
    assert (await api.post("/api/v1/notas", json=_nota(), headers=lucia)).status_code == 403
    # sí dicta la materia 2 en el curso 1
    assert (
        await api.post("/api/v1/notas", json=_nota(id_materia=2, id_periodo=3), headers=lucia)
    ).status_code == 201


async def test_un_docente_sin_asignacion_no_edita_ni_borra_notas_ajenas(api):
    lucia = await encabezado(api, DOCENTE_AJENO)

    # La nota 1 es del estudiante 1, materia 1
    assert (await api.put("/api/v1/notas/1", json={"nota": 4.0}, headers=lucia)).status_code == 403
    assert (await api.delete("/api/v1/notas/1", headers=lucia)).status_code == 403


async def test_el_docente_solo_lista_las_notas_de_los_cursos_que_dicta(api):
    maria = await encabezado(api, MARIA)
    carlos = await encabezado(api, DOCENTE)
    admin = await encabezado(api, ADMIN)

    de_maria = (await api.get("/api/v1/notas?limit=500", headers=maria)).json()
    de_carlos = (await api.get("/api/v1/notas?limit=500", headers=carlos)).json()
    del_admin = (await api.get("/api/v1/notas?limit=500", headers=admin)).json()

    # María dicta en los cursos 1 y 3: ve al estudiante 1 y 2 (curso 1), no al 3 (curso 2)
    assert {n["id_estudiante"] for n in de_maria} == {1, 2}
    assert {n["id_estudiante"] for n in de_carlos} == {1, 2, 3}
    assert len(del_admin) >= len(de_carlos)


async def test_el_promedio_del_estudiante_se_calcula_en_la_base(db):
    promedio = await NotaRepository(db).get_promedio_estudiante(1)

    # Notas del estudiante 1 en el seed: 4.5, 3.8, 4.0 y 4.8
    assert float(promedio) == pytest.approx(4.275)


async def test_el_boletin_de_un_estudiante_con_notas_es_un_pdf_sin_archivos_temporales(api, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sofia = await encabezado(api, ESTUDIANTE)

    respuesta = await api.get("/api/v1/notas/estudiantes/1/boletin/pdf", headers=sofia)

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "application/pdf"
    assert respuesta.content.startswith(b"%PDF")
    assert not (tmp_path / "tmp").exists()


async def test_el_boletin_de_un_estudiante_sin_notas_responde_404_con_el_mensaje(api, db):
    sin_notas = (await db.execute(text(
        'SELECT e."idEstudiante" FROM public.estudiantes e '
        'WHERE NOT EXISTS (SELECT 1 FROM public.notas n WHERE n."idEstudiante" = e."idEstudiante") '
        'LIMIT 1'
    ))).scalar_one()
    admin = await encabezado(api, ADMIN)

    respuesta = await api.get(f"/api/v1/notas/estudiantes/{sin_notas}/boletin/pdf", headers=admin)

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "No hay datos disponibles para generar el boletín."


async def test_un_padre_no_descarga_el_boletin_de_un_estudiante_ajeno(api):
    roberto = await encabezado(api, PADRE_UN_HIJO)

    assert (
        await api.get("/api/v1/notas/estudiantes/1/boletin/pdf", headers=roberto)
    ).status_code == 403


# --- novedades --------------------------------------------------------------------------------

NOVEDAD = {"id_estudiante": 1, "id_tipo_novedad": 1, "fecha": "2026-11-02", "descripcion": "Llegó tarde"}


async def test_la_novedad_se_guarda_a_nombre_del_usuario_del_token(api):
    carlos = await encabezado(api, DOCENTE)

    respuesta = await api.post(
        "/api/v1/novedades", json={**NOVEDAD, "registrado_por": 9}, headers=carlos
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["registrado_por"] == 2


async def test_un_docente_no_edita_ni_borra_la_novedad_de_otro_docente(api):
    maria = await encabezado(api, MARIA)

    # Las novedades del seed las registró Carlos (usuario 2)
    assert (
        await api.put("/api/v1/novedades/1", json={"descripcion": "x"}, headers=maria)
    ).status_code == 403
    assert (await api.delete("/api/v1/novedades/1", headers=maria)).status_code == 403


async def test_el_autor_y_el_admin_si_editan_la_novedad(api):
    carlos = await encabezado(api, DOCENTE)
    admin = await encabezado(api, ADMIN)

    assert (
        await api.put("/api/v1/novedades/1", json={"descripcion": "a"}, headers=carlos)
    ).status_code == 200
    assert (
        await api.put("/api/v1/novedades/1", json={"descripcion": "b"}, headers=admin)
    ).status_code == 200


# --- notificaciones push ----------------------------------------------------------------------


@pytest.fixture
def notificador():
    falso = NotificadorFalso()
    app.dependency_overrides[get_notificador] = lambda: falso
    yield falso
    app.dependency_overrides.pop(get_notificador, None)


async def _registrar_dispositivo(api, correo, token):
    headers = await encabezado(api, correo)
    return await api.post(
        "/api/v1/dispositivos", json={"token_fcm": token, "plataforma": "android"}, headers=headers
    )


async def test_registrar_el_mismo_dispositivo_dos_veces_no_lo_duplica(api, db):
    primero = await _registrar_dispositivo(api, PADRE_DOS_HIJOS, "token-de-rosa-0001")
    segundo = await _registrar_dispositivo(api, PADRE_UN_HIJO, "token-de-rosa-0001")

    total = (await db.execute(select(func.count()).select_from(DispositivoModel))).scalar_one()
    dueno = (await db.execute(select(DispositivoModel.id_usuario))).scalar_one()
    assert (primero.status_code, segundo.status_code) == (201, 201)
    assert total == 1
    assert dueno == 8  # el token pasó a la cuenta de Roberto


async def test_la_novedad_notifica_solo_a_los_acudientes_del_estudiante(api, notificador):
    await _registrar_dispositivo(api, PADRE_DOS_HIJOS, "token-de-rosa-0001")
    await _registrar_dispositivo(api, PADRE_UN_HIJO, "token-de-roberto-02")
    carlos = await encabezado(api, DOCENTE)

    # El estudiante 1 es hijo de Rosa; Roberto es acudiente del estudiante 2.
    respuesta = await api.post("/api/v1/novedades", json=NOVEDAD, headers=carlos)

    assert respuesta.status_code == 201
    assert [e["tokens"] for e in notificador.envios] == [["token-de-rosa-0001"]]
    assert notificador.envios[0]["titulo"] == "Nueva novedad de Sofía Rodríguez"


async def test_sin_dispositivos_registrados_la_novedad_se_guarda_sin_envios(api, notificador):
    carlos = await encabezado(api, DOCENTE)

    respuesta = await api.post("/api/v1/novedades", json=NOVEDAD, headers=carlos)

    assert respuesta.status_code == 201
    assert notificador.envios == []


# --- avatar -----------------------------------------------------------------------------------


def _png() -> bytes:
    salida = io.BytesIO()
    Image.frombytes("RGB", (100, 100), os.urandom(30000)).save(salida, format="PNG")
    return salida.getvalue()


async def test_el_avatar_valida_el_contenido_real_del_archivo(api, tmp_path, monkeypatch):
    monkeypatch.setattr(auth_service, "AVATAR_DIR", str(tmp_path))
    sofia = await encabezado(api, ESTUDIANTE)

    html = await api.post(
        "/api/v1/auth/me/avatar", headers=sofia,
        files={"file": ("pagina.html", b"<script>alert(1)</script>", "image/png")},
    )
    png = await api.post(
        "/api/v1/auth/me/avatar", headers=sofia, files={"file": ("foto.png", _png(), "image/png")}
    )

    assert html.status_code == 400
    assert png.status_code == 200 and png.json().endswith(".png")
    assert len(list(tmp_path.iterdir())) == 1
