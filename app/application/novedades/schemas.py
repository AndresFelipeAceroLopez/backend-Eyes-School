from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class TipoNovedadCreate(BaseModel):
    nombre_tipo: str
    descripcion: str | None = None
    nivel_gravedad: Literal["Bajo", "Medio", "Alto", "Crítico"] = "Bajo"
    requiere_accion: bool = False


class TipoNovedadOut(BaseModel):
    id_tipo_novedad: int
    nombre_tipo: str
    descripcion: str | None
    nivel_gravedad: str
    requiere_accion: bool
    activo: bool
    model_config = {"from_attributes": True}


class NovedadCreate(BaseModel):
    id_estudiante: int
    id_tipo_novedad: int
    fecha: date
    descripcion: str
    accion_tomada: str | None = None
    registrado_por: int


class NovedadUpdate(BaseModel):
    descripcion: str | None = None
    accion_tomada: str | None = None
    fecha_resolucion: date | None = None
    id_tipo_novedad: int | None = None
    # El front maneja dos estados: "Pendiente" y "Completado".
    estado: Literal["Pendiente", "Completado"] | None = None


class NovedadOut(BaseModel):
    id_novedad: int
    id_estudiante: int
    id_tipo_novedad: int
    fecha: date
    descripcion: str
    accion_tomada: str | None
    registrado_por: int
    fecha_resolucion: date | None
    estado: str
    model_config = {"from_attributes": True}
