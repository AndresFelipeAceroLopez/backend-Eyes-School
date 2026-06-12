from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class EstudianteCreate(BaseModel):
    id_usuario: int
    codigo_estudiante: str
    fecha_ingreso: date
    estado: Literal["Activo", "Inactivo", "Retirado", "Graduado", "Suspendido"] = "Activo"
    id_curso_actual: int | None = None


class EstudianteUpdate(BaseModel):
    codigo_estudiante: str | None = None
    fecha_ingreso: date | None = None
    fecha_egreso: date | None = None
    estado: Literal["Activo", "Inactivo", "Retirado", "Graduado", "Suspendido"] | None = None
    id_curso_actual: int | None = None


class EstudianteOut(BaseModel):
    id_estudiante: int
    id_usuario: int
    codigo_estudiante: str
    fecha_ingreso: date
    fecha_egreso: date | None
    estado: str
    id_curso_actual: int | None
    fecha_registro: datetime
    model_config = {"from_attributes": True}


class EstudianteIPSCreate(BaseModel):
    id_ips: int
    nombre_ips: str
    fecha_afiliacion: date
    fecha_vencimiento: date | None = None
    tipo_afiliacion: Literal["Contributivo", "Subsidiado", "Especial"]


class EstudianteIPSOut(BaseModel):
    id_estudiante: int
    id_ips: int
    nombre_ips: str
    fecha_afiliacion: date
    fecha_vencimiento: date | None
    tipo_afiliacion: str
    activo: bool
    model_config = {"from_attributes": True}
