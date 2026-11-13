from datetime import date

from pydantic import BaseModel

from app.application.common.tipos import FechaHoraUTC


class AsignacionCreate(BaseModel):
    id_profesor: int
    id_curso: int
    id_materia: int
    fecha_finalizacion: date | None = None


class AsignacionUpdate(BaseModel):
    fecha_finalizacion: date | None = None
    activo: bool | None = None


class AsignacionOut(BaseModel):
    id_asignacion: int
    id_profesor: int
    id_curso: int
    id_materia: int
    fecha_asignacion: FechaHoraUTC
    fecha_finalizacion: date | None
    activo: bool
    model_config = {"from_attributes": True}
