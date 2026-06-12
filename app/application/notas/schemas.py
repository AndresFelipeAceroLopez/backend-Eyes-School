from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class NotaCreate(BaseModel):
    id_estudiante: int
    id_materia: int
    id_periodo: Annotated[int, Field(ge=1, le=4)]
    nota: Annotated[float, Field(ge=0, le=10)]
    observacion: str | None = None
    registrado_por: int


class NotaUpdate(BaseModel):
    nota: Annotated[float, Field(ge=0, le=10)] | None = None
    observacion: str | None = None


class NotaOut(BaseModel):
    id_nota: int
    id_estudiante: int
    id_materia: int
    id_periodo: int
    nota: float
    observacion: str | None
    fecha_registro: datetime
    registrado_por: int
    model_config = {"from_attributes": True}
