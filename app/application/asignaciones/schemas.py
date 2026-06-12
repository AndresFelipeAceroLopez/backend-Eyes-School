from datetime import date, datetime

from pydantic import BaseModel


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
    fecha_asignacion: datetime
    fecha_finalizacion: date | None
    activo: bool
    model_config = {"from_attributes": True}
