from datetime import date
from typing import Literal

from pydantic import BaseModel


class ReporteCreate(BaseModel):
    nombre_reporte: str
    tipo_reporte: Literal["Academico", "Disciplinario", "Medico", "Asistencia", "Estadistico"]
    fecha_inicio: date
    fecha_fin: date
    id_administrador: int
    parametros: str = " "


class ReporteEstadoUpdate(BaseModel):
    estado: Literal["Pendiente", "Procesando", "Completado", "Error"]
    archivo_generado: str | None = None


class ReporteOut(BaseModel):
    id_reporte: int
    nombre_reporte: str
    tipo_reporte: str
    fecha_generacion: date
    fecha_inicio: date
    fecha_fin: date
    estado: str
    id_administrador: int
    parametros: str
    archivo_generado: str | None
    model_config = {"from_attributes": True}
