from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CursoCreate(BaseModel):
    nombre_curso: str
    grado: str
    jornada: Literal["mañana", "tarde", "unica", "1", "2", "3", "4"]
    ano: int
    area: str | None = None
    intensidad_horaria: int | None = None
    descripcion: str | None = None


class CursoUpdate(BaseModel):
    nombre_curso: str | None = None
    grado: str | None = None
    jornada: Literal["mañana", "tarde", "unica", "1", "2", "3", "4"] | None = None
    ano: int | None = None
    area: str | None = None
    intensidad_horaria: int | None = None
    descripcion: str | None = None
    activo: bool | None = None


class CursoOut(BaseModel):
    id_curso: int
    nombre_curso: str
    grado: str
    jornada: str
    ano: int
    area: str | None
    intensidad_horaria: int | None
    descripcion: str | None
    activo: bool
    fecha_creacion: datetime
    model_config = {"from_attributes": True}
