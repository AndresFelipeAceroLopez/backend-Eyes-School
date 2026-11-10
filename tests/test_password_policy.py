"""BE-09: la API aplica la misma política de contraseña que la web (5 reglas).

Son los mismos casos que `tests/password.test.ts` de la web y `validators_test.dart` de la app.
"""

from datetime import datetime
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.application.auth.schemas import RegisterRequest, ResetPasswordRequest
from app.application.usuarios import service as usuarios_service
from app.application.usuarios.schemas import UsuarioUpdate
from app.core.password_policy import validar_password
from app.core.security import hash_password
from tests.conftest import bearer


def test_una_contrasena_que_cumple_todo_no_tiene_fallos():
    assert validar_password("Colegio#2026") == []


@pytest.mark.parametrize(
    ("password", "regla"),
    [
        ("Ab1#", "longitud"),
        ("colegio#2026", "mayúscula"),
        ("COLEGIO#2026", "minúscula"),
        ("Colegio#ocho", "número"),
        ("Colegio2026", "especial"),
    ],
)
def test_cada_regla_incumplida_se_reporta(password, regla):
    fallos = validar_password(password)

    assert any(regla in f for f in fallos)


async def test_registrarse_con_una_contrasena_debil_responde_422(client):
    cuerpo = {
        "tipo_documento": "CC", "numero_documento": "123", "primer_nombre": "Ana",
        "primer_apellido": "Gómez", "correo": "ana@x.com", "password": "Colegio2026", "id_rol": 4,
    }

    response = await client.post("/api/v1/auth/register", json=cuerpo)

    assert response.status_code == 422


def test_restablecer_con_una_contrasena_debil_se_rechaza():
    with pytest.raises(ValidationError):
        ResetPasswordRequest(token="t", new_password="12345678")
    assert ResetPasswordRequest(token="t", new_password="Colegio#2026").new_password


def test_el_registro_aplica_la_politica_heredada_de_usuario():
    with pytest.raises(ValidationError):
        RegisterRequest(
            tipo_documento="CC", numero_documento="1", primer_nombre="A", primer_apellido="B",
            id_rol=2, password="corta",
        )


# --- cambio de contraseña propio: exige la actual -------------------------------------------


class _UsuariosFalsos:
    actualizado: dict | None = None

    def __init__(self, session):
        pass

    async def get_by_id_with_rol(self, id_usuario):
        return SimpleNamespace(
            id_usuario=id_usuario, tipo_documento="CC", numero_documento="1", primer_nombre="Ana",
            segundo_nombre=None, primer_apellido="Gómez", segundo_apellido=None, genero=None,
            direccion=None, correo="ana@x.com", telefono=None, estado=True,
            fecha_registro=datetime(2026, 1, 1), ultimo_acceso=None, id_rol=1, foto_perfil=None,
            rol=None, password=hash_password("Actual#2026"),
        )

    async def correo_exists(self, correo, exclude_id=None):
        return False

    async def update(self, user, data):
        _UsuariosFalsos.actualizado = data
        return user


@pytest.fixture
def usuarios(monkeypatch, sin_base_de_datos):
    _UsuariosFalsos.actualizado = None
    monkeypatch.setattr(usuarios_service, "UsuarioRepository", _UsuariosFalsos)
    monkeypatch.setattr(usuarios_service, "SesionRepository", lambda s: None)


async def test_cambiar_la_propia_contrasena_sin_la_actual_responde_400(client, usuarios):
    response = await client.put(
        "/api/v1/usuarios/7", json={"password": "Nueva#2026"}, headers=bearer("docente", 1, 7)
    )

    assert response.status_code == 400
    assert _UsuariosFalsos.actualizado is None


async def test_cambiar_la_propia_contrasena_con_una_actual_incorrecta_responde_400(client, usuarios):
    response = await client.put(
        "/api/v1/usuarios/7",
        json={"password": "Nueva#2026", "password_actual": "Otra#2026"},
        headers=bearer("docente", 1, 7),
    )

    assert response.status_code == 400


async def test_cambiar_la_propia_contrasena_con_la_actual_correcta_la_guarda_con_hash(client, usuarios):
    response = await client.put(
        "/api/v1/usuarios/7",
        json={"password": "Nueva#2026", "password_actual": "Actual#2026"},
        headers=bearer("docente", 1, 7),
    )

    assert response.status_code == 200
    assert _UsuariosFalsos.actualizado["password"].startswith("$2")
    assert "password_actual" not in _UsuariosFalsos.actualizado
    assert _UsuariosFalsos.actualizado["password_actualizada"] is not None


async def test_el_admin_cambia_la_contrasena_de_otro_sin_la_actual(client, usuarios):
    response = await client.put(
        "/api/v1/usuarios/7", json={"password": "Nueva#2026"}, headers=bearer("admin", 3, 1)
    )

    assert response.status_code == 200


def test_actualizar_usuario_sin_contrasena_no_la_valida():
    assert UsuarioUpdate(primer_nombre="Ana").password is None
