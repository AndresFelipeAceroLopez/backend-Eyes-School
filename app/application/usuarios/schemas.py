from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, EmailStr, field_validator

from app.core.password_policy import exigir_password_valida


def normalizar_correo(valor):
    """Quita espacios y pasa a minúsculas: `Ana@X.com` y `ana@x.com` son la misma cuenta."""
    return valor.strip().lower() if isinstance(valor, str) else valor


# Correo con formato válido y ya normalizado (BE-12).
Correo = Annotated[EmailStr, BeforeValidator(normalizar_correo)]
# Correo normalizado sin exigir formato: para iniciar sesión, donde no se debe rechazar
# por formato una cuenta que ya existe.
CorreoNormalizado = Annotated[str, BeforeValidator(normalizar_correo)]


class RolOut(BaseModel):
    id_rol: int
    nombre_rol: str

    model_config = {"from_attributes": True}


class UsuarioCreate(BaseModel):
    tipo_documento: Literal["CC", "CE", "TI", "PAS"]
    numero_documento: str
    primer_nombre: str
    segundo_nombre: str | None = None
    primer_apellido: str
    segundo_apellido: str | None = None
    genero: Literal["M", "F", "O"] | None = None
    direccion: str | None = None
    correo: Correo | None = None
    password: str | None = None
    telefono: str | None = None
    id_rol: int

    @field_validator("password")
    @classmethod
    def _password_cumple_la_politica(cls, v: str | None) -> str | None:
        return exigir_password_valida(v) if v is not None else v


class UsuarioUpdate(BaseModel):
    primer_nombre: str | None = None
    segundo_nombre: str | None = None
    primer_apellido: str | None = None
    segundo_apellido: str | None = None
    genero: Literal["M", "F", "O"] | None = None
    direccion: str | None = None
    correo: Correo | None = None
    telefono: str | None = None
    password: str | None = None
    # Quien cambia su propia contraseña debe confirmar la actual (no se guarda).
    password_actual: str | None = None
    id_rol: int | None = None

    @field_validator("password")
    @classmethod
    def _password_cumple_la_politica(cls, v: str | None) -> str | None:
        return exigir_password_valida(v) if v is not None else v


class UsuarioOut(BaseModel):
    id_usuario: int
    tipo_documento: str
    numero_documento: str
    primer_nombre: str
    segundo_nombre: str | None
    primer_apellido: str
    segundo_apellido: str | None
    genero: str | None
    direccion: str | None
    correo: str | None
    telefono: str | None
    estado: bool
    fecha_registro: datetime
    ultimo_acceso: datetime | None
    id_rol: int
    foto_perfil: str | None = None
    rol: RolOut | None = None

    model_config = {"from_attributes": True}
