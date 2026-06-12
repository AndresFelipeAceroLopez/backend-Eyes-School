from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class AsistenciaCreate(BaseModel):
    id_estudiante: int
    fecha: date
    estado: Literal["Presente", "Ausente", "Tarde", "Excusa", "Suspensión"]
    observacion: str | None = None
    registrado_por: int
    tipo: Literal["entrada", "salida", "clase"] | None = None


class AsistenciaQRCreate(BaseModel):
    codigo_qr: str
    tipo: Literal["entrada", "salida", "clase"] = "entrada"
    registrado_por: int


class AsistenciaUpdate(BaseModel):
    estado: Literal["Presente", "Ausente", "Tarde", "Excusa", "Suspensión"] | None = None
    observacion: str | None = None


class AsistenciaOut(BaseModel):
    id_asistencia: int
    id_estudiante: int
    fecha: date
    estado: str
    observacion: str | None
    registrado_por: int
    fecha_registro: datetime
    tipo: str | None
    codigo_qr: str | None
    activo: bool | None
    model_config = {"from_attributes": True}


class AsistenciaAulaCreate(BaseModel):
    id_estudiante: int
    id_horario: int
    fecha: date
    estado: Literal["Presente", "Ausente", "Tarde", "Excusa", "Suspensión"]
    observacion: str
    registrado_por: int


class AsistenciaAulaOut(BaseModel):
    id_asistencia_aula: int
    id_estudiante: int
    id_horario: int
    fecha: date
    estado: str
    observacion: str
    registrado_por: int
    fecha_registro: datetime
    model_config = {"from_attributes": True}
