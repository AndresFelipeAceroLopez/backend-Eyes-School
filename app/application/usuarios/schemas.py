from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator


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
    correo: str | None = None
    password: str | None = None
    telefono: str | None = None
    id_rol: int


class UsuarioUpdate(BaseModel):
    primer_nombre: str | None = None
    segundo_nombre: str | None = None
    primer_apellido: str | None = None
    segundo_apellido: str | None = None
    genero: Literal["M", "F", "O"] | None = None
    direccion: str | None = None
    correo: str | None = None
    telefono: str | None = None
    id_rol: int | None = None


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
    rol: RolOut | None = None

    model_config = {"from_attributes": True}
