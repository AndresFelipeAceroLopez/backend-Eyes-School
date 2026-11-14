"""Sesiones, bloqueo, recuperación y registro contra PostgreSQL real (CP-INT-006 a 018, 029, 077).

Todo corre sin servicios externos de sesión: las sesiones de refresco viven en la tabla `sesiones_refresco`.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import func, select, text

from app.core.config import settings
from app.core.security import create_password_reset_token
from app.infrastructure.models.sesiones import SesionRefrescoModel
from tests.integration.conftest import (
    ADMIN,
    DOCENTE,
    PADRE_DOS_HIJOS,
    PASSWORD,
    encabezado,
    iniciar_sesion,
)

pytestmark = pytest.mark.integration


async def test_el_correo_no_distingue_mayusculas_al_iniciar_sesion(api):
    tokens = await iniciar_sesion(api, "  ADMIN@EyesSchool.edu.co ")

    assert tokens["access_token"]


async def test_login_guarda_la_sesion_en_la_base(api, db):
    await iniciar_sesion(api, DOCENTE)

    total = (await db.execute(select(func.count()).select_from(SesionRefrescoModel))).scalar_one()
    assert total == 1


async def test_login_refresh_logout_refresh_termina_en_401(api):
    tokens = await iniciar_sesion(api, DOCENTE)
    cuerpo = {"refresh_token": tokens["refresh_token"]}

    assert (await api.post("/api/v1/auth/refresh", json=cuerpo)).status_code == 200
    assert (await api.post("/api/v1/auth/logout", json=cuerpo)).status_code == 204
    assert (await api.post("/api/v1/auth/refresh", json=cuerpo)).status_code == 401


async def test_un_usuario_desactivado_no_renueva_su_sesion(api, db):
    tokens = await iniciar_sesion(api, DOCENTE)
    await db.execute(text('UPDATE public.usuario SET estado = false WHERE "idUsuario" = 2'))

    respuesta = await api.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert respuesta.status_code == 401


async def test_desactivar_desde_el_admin_revoca_las_sesiones(api):
    tokens = await iniciar_sesion(api, DOCENTE)
    admin = await encabezado(api, ADMIN)

    desactivar = await api.patch("/api/v1/usuarios/2/estado?estado=false", headers=admin)
    refrescar = await api.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

    assert desactivar.status_code == 200
    assert refrescar.status_code == 401


async def test_cinco_fallos_bloquean_el_sexto_intento_aunque_la_clave_sea_correcta(api):
    for _ in range(5):
        malo = await api.post(
            "/api/v1/auth/login", json={"correo": DOCENTE, "password": "Incorrecta#1"}
        )
        assert malo.status_code == 401

    bloqueado = await api.post("/api/v1/auth/login", json={"correo": DOCENTE, "password": PASSWORD})

    assert bloqueado.status_code == 429
    assert "15 minutos" in bloqueado.json()["detail"]


async def test_un_acceso_exitoso_reinicia_el_contador_de_fallos(api, db):
    for _ in range(2):
        await api.post("/api/v1/auth/login", json={"correo": DOCENTE, "password": "Incorrecta#1"})
    await iniciar_sesion(api, DOCENTE)

    fallos = (await db.execute(
        text('SELECT "intentosFallidos" FROM public.usuario WHERE "idUsuario" = 2')
    )).scalar_one()
    assert fallos == 0


async def test_el_bloqueo_vencido_permite_volver_a_entrar(api, db):
    await db.execute(text(
        'UPDATE public.usuario SET "bloqueadoHasta" = now() - interval \'16 minutes\' '
        'WHERE "idUsuario" = 2'
    ))

    assert (await iniciar_sesion(api, DOCENTE))["access_token"]


# --- recuperación de contraseña ---------------------------------------------------------------


async def test_restablecer_la_contrasena_permite_entrar_con_la_nueva(api):
    token = create_password_reset_token(2, pwd_ts=0)

    respuesta = await api.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "Nueva#2026"}
    )

    assert respuesta.status_code == 200
    assert (await iniciar_sesion(api, DOCENTE, "Nueva#2026"))["access_token"]
    vieja = await api.post("/api/v1/auth/login", json={"correo": DOCENTE, "password": PASSWORD})
    assert vieja.status_code == 401


async def test_restablecer_con_una_contrasena_debil_responde_422(api):
    token = create_password_reset_token(2, pwd_ts=0)

    respuesta = await api.post(
        "/api/v1/auth/reset-password", json={"token": token, "new_password": "colegio123"}
    )

    assert respuesta.status_code == 422


async def test_el_enlace_de_recuperacion_no_se_puede_reutilizar(api):
    token = create_password_reset_token(2, pwd_ts=0)
    cuerpo = {"token": token, "new_password": "Nueva#2026"}

    primero = await api.post("/api/v1/auth/reset-password", json=cuerpo)
    segundo = await api.post("/api/v1/auth/reset-password", json={**cuerpo, "new_password": "Otra#2026x"})

    assert (primero.status_code, segundo.status_code) == (200, 401)


async def test_un_enlace_vencido_responde_401(api):
    vencido = jwt.encode(
        {"sub": "2", "type": "reset", "pwd_ts": 0,
         "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.SECRET_KEY, algorithm=settings.ALGORITHM,
    )

    respuesta = await api.post(
        "/api/v1/auth/reset-password", json={"token": vencido, "new_password": "Nueva#2026"}
    )

    assert respuesta.status_code == 401


# --- registro y unicidad del correo -----------------------------------------------------------

REGISTRO = {
    "tipo_documento": "CC", "numero_documento": "99900011", "primer_nombre": "Laura",
    "primer_apellido": "Ruiz", "correo": "laura.ruiz@gmail.com", "password": "Colegio#2026",
    "id_rol": 4, "id_estudiante_vinculado": 1, "parentesco": "Madre",
}


async def test_el_registro_de_un_padre_queda_activo_y_vinculado(api, db):
    respuesta = await api.post("/api/v1/auth/register", json=REGISTRO)

    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] is True
    vinculos = (await db.execute(text(
        'SELECT count(*) FROM public.padres WHERE "idUsuario" = :u'
    ), {"u": respuesta.json()["id_usuario"]})).scalar_one()
    assert vinculos == 1


async def test_registrar_un_correo_que_solo_cambia_en_mayusculas_responde_409(api):
    respuesta = await api.post(
        "/api/v1/auth/register", json={**REGISTRO, "correo": PADRE_DOS_HIJOS.upper()}
    )

    assert respuesta.status_code == 409


async def test_el_admin_no_puede_crear_un_usuario_con_un_correo_repetido(api):
    admin = await encabezado(api, ADMIN)

    respuesta = await api.post(
        "/api/v1/usuarios", headers=admin,
        json={**REGISTRO, "numero_documento": "99900012", "correo": "Rosa.Perez@Gmail.com"},
    )

    assert respuesta.status_code == 409


async def test_el_registro_con_contrasena_debil_responde_422(api):
    respuesta = await api.post("/api/v1/auth/register", json={**REGISTRO, "password": "Colegio2026"})

    assert respuesta.status_code == 422


async def test_el_correo_queda_guardado_en_minusculas(api, db):
    respuesta = await api.post(
        "/api/v1/auth/register", json={**REGISTRO, "correo": "Laura.RUIZ@Gmail.com"}
    )

    assert respuesta.json()["correo"] == "laura.ruiz@gmail.com"
