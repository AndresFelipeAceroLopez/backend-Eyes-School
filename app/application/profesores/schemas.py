from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class EspecializacionOut(BaseModel):
    id_especializacion: int
    nombre_especializacion: str
    descripcion: str | None
    activo: bool
    model_config = {"from_attributes": True}


class ProfesorEspecializacionOut(BaseModel):
    id_profesor: int
    id_especializacion: int
    institucion: str
    especializacion: EspecializacionOut | None = None
    model_config = {"from_attributes": True}


class ProfesorCreate(BaseModel):
    id_usuario: int
    codigo_profesor: str
    titulo: str
    nivel_estudios: str
    fecha_vinculacion: date
    estado: Literal["Activo", "Inactivo", "Vacaciones", "Licencia"] = "Activo"


class ProfesorUpdate(BaseModel):
    codigo_profesor: str | None = None
    titulo: str | None = None
    nivel_estudios: str | None = None
    fecha_vinculacion: date | None = None
    estado: Literal["Activo", "Inactivo", "Vacaciones", "Licencia"] | None = None


class ProfesorOut(BaseModel):
    id_profesor: int
    id_usuario: int
    codigo_profesor: str
    titulo: str
    nivel_estudios: str
    fecha_vinculacion: date
    estado: str
    fecha_registro: datetime
    # Nombre embebido (join con usuario) para resolver el nombre del profesor en
    # horarios sin leer /usuarios. Opcionales: solo se llenan en el listado.
    primer_nombre: str | None = None
    segundo_nombre: str | None = None
    primer_apellido: str | None = None
    segundo_apellido: str | None = None
    model_config = {"from_attributes": True}


class AgregarEspecializacionRequest(BaseModel):
    id_especializacion: int
    institucion: str
