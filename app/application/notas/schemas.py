from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

# Escala de notas del colegio: de 0.0 a 5.0 (igual que la web y la app).
NOTA_MIN = 0.0
NOTA_MAX = 5.0


class NotaCreate(BaseModel):
    id_estudiante: int
    id_materia: int
    id_periodo: Annotated[int, Field(ge=1, le=4)]
    nota: Annotated[float, Field(ge=NOTA_MIN, le=NOTA_MAX)]
    observacion: str | None = None


class NotaUpdate(BaseModel):
    nota: Annotated[float, Field(ge=NOTA_MIN, le=NOTA_MAX)] | None = None
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
