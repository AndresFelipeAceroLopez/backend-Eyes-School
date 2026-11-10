"""BE-12: el correo se normaliza (minúsculas, sin espacios) y se valida su formato."""

import pytest
from pydantic import ValidationError

from app.application.auth.schemas import ForgotPasswordRequest, LoginRequest
from app.application.usuarios.schemas import UsuarioCreate, UsuarioUpdate


def _usuario(correo):
    return UsuarioCreate(
        tipo_documento="CC", numero_documento="1", primer_nombre="Ana", primer_apellido="Gómez",
        id_rol=2, correo=correo,
    )


def test_el_login_normaliza_el_correo():
    assert LoginRequest(correo=" Ana@X.com ", password="x").correo == "ana@x.com"


def test_recuperar_contrasena_normaliza_el_correo():
    assert ForgotPasswordRequest(correo=" ANA@X.COM").correo == "ana@x.com"


def test_crear_un_usuario_normaliza_el_correo():
    assert _usuario("  Ana@X.com ").correo == "ana@x.com"


def test_actualizar_un_usuario_normaliza_el_correo():
    assert UsuarioUpdate(correo="Ana@X.com").correo == "ana@x.com"


@pytest.mark.parametrize("correo", ["no-es-correo", "ana@", "@x.com", "ana x@x.com", ""])
def test_un_correo_con_formato_invalido_se_rechaza(correo):
    with pytest.raises(ValidationError):
        _usuario(correo)


def test_el_correo_sigue_siendo_opcional():
    assert _usuario(None).correo is None
