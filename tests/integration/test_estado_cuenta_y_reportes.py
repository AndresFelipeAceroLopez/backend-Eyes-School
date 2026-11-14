"""N-31 y N-23 contra PostgreSQL real (planeación de cierre, BC-04 y BC-05)."""

import shutil
import uuid

import pytest
from sqlalchemy import text

from app.application.auth.service import MENSAJE_CUENTA_DESACTIVADA, MENSAJE_CUENTA_PENDIENTE
from tests.integration.conftest import ADMIN, DOCENTE, PASSWORD, encabezado

pytestmark = pytest.mark.integration


def _cuenta(correo: str, id_rol: int) -> dict:
    return {
        "tipo_documento": "CC", "numero_documento": str(uuid.uuid4().int)[:10],
        "primer_nombre": "Qa", "primer_apellido": "Cierre", "correo": correo,
        "password": PASSWORD, "id_rol": id_rol,
    }


async def _login(api, correo):
    return await api.post("/api/v1/auth/login", json={"correo": correo, "password": PASSWORD})


# ---------------------------------------------------------------------------------- N-31


async def test_un_docente_recien_registrado_ve_que_su_cuenta_esta_pendiente(api):
    correo = f"pendiente.{uuid.uuid4().hex[:8]}@example.com"
    assert (await api.post("/api/v1/auth/register", json=_cuenta(correo, 1))).status_code == 201

    respuesta = await _login(api, correo)

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == MENSAJE_CUENTA_PENDIENTE


async def test_una_cuenta_desactivada_por_el_admin_ve_que_esta_desactivada(api):
    admin = await encabezado(api, ADMIN)
    assert (await api.patch("/api/v1/usuarios/2/estado?estado=false", headers=admin)).status_code == 200

    respuesta = await _login(api, DOCENTE)

    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == MENSAJE_CUENTA_DESACTIVADA


async def test_al_validarla_el_admin_la_cuenta_deja_de_estar_pendiente(api, db):
    correo = f"validada.{uuid.uuid4().hex[:8]}@example.com"
    registro = await api.post("/api/v1/auth/register", json=_cuenta(correo, 1))
    id_usuario = registro.json()["id_usuario"]
    admin = await encabezado(api, ADMIN)

    await api.patch(f"/api/v1/usuarios/{id_usuario}/estado?estado=true", headers=admin)
    assert (await _login(api, correo)).status_code == 200

    # Si después la desactiva, ya no se confunde con una cuenta por validar.
    await api.patch(f"/api/v1/usuarios/{id_usuario}/estado?estado=false", headers=admin)
    respuesta = await _login(api, correo)
    assert respuesta.json()["detail"] == MENSAJE_CUENTA_DESACTIVADA
    pendiente = await db.scalar(text(
        'SELECT "pendienteValidacion" FROM public.usuario WHERE "idUsuario" = :id'
    ), {"id": id_usuario})
    assert pendiente is False


async def test_con_la_contrasena_equivocada_no_se_revela_el_estado(api):
    correo = f"oculta.{uuid.uuid4().hex[:8]}@example.com"
    await api.post("/api/v1/auth/register", json=_cuenta(correo, 1))

    respuesta = await api.post("/api/v1/auth/login", json={"correo": correo, "password": "Otra#2026x"})

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Credenciales inválidas"


# ---------------------------------------------------------------------------------- N-23


async def test_el_archivo_de_un_reporte_sobrevive_a_un_despliegue(api, tmp_path, monkeypatch):
    """Subir → «desplegar» (se borra el disco) → descargar → 200 con el mismo contenido."""
    monkeypatch.chdir(tmp_path)
    admin = await encabezado(api, ADMIN)
    contenido = b"%PDF-1.4 reporte de cierre " + uuid.uuid4().bytes

    subida = await api.post(
        "/api/v1/reportes/archivo", headers=admin,
        files={"file": ("cierre.pdf", contenido, "application/pdf")},
    )
    assert subida.status_code == 200
    ruta = subida.json()
    creado = await api.post("/api/v1/reportes", headers=admin, json={
        "nombre_reporte": "Reporte de cierre", "tipo_reporte": "Asistencia",
        "fecha_inicio": "2026-11-01", "fecha_fin": "2026-11-13", "id_administrador": 1,
        "archivo_generado": ruta,
    })
    assert creado.status_code == 201

    # Lo que hace un despliegue de Oryx: el disco de la app vuelve a empezar vacío.
    shutil.rmtree(tmp_path / "static", ignore_errors=True)

    descarga = await api.get(f"/api/v1/reportes/{creado.json()['id_reporte']}/archivo", headers=admin)
    assert descarga.status_code == 200
    assert descarga.content == contenido
    assert descarga.headers["content-type"] == "application/pdf"
    assert "attachment" in descarga.headers["content-disposition"]
