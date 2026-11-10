from typing import Literal

from pydantic import BaseModel


class PadreCreate(BaseModel):
    id_usuario: int
    id_estudiante: int
    parentesco: Literal["Padre", "Madre", "Tutor", "Abuelo", "Otro"]
    ocupacion: str | None = None


class PadreOut(BaseModel):
    id_padre: int
    id_usuario: int
    id_estudiante: int
    parentesco: str
    ocupacion: str | None
    # Datos del estudiante asociado (resueltos en /me para mostrarlos en el perfil
    # del padre sin que tenga que consultar /usuarios, que es admin-only).
    nombre_estudiante: str | None = None
    documento_estudiante: str | None = None
    model_config = {"from_attributes": True}


class HijoOut(BaseModel):
    """Un estudiante vinculado a la cuenta del acudiente."""

    id_estudiante: int
    nombre_estudiante: str | None = None
    documento_estudiante: str | None = None
    parentesco: str
    id_curso_actual: int | None = None
