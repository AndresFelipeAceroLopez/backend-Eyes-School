from typing import Literal

from pydantic import BaseModel

from app.application.common.tipos import HoraLocal


class HorarioCreate(BaseModel):
    id_curso: int
    id_materia: int
    dia: Literal["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"]
    hora_inicio: HoraLocal
    hora_fin: HoraLocal
    salon: str


class HorarioUpdate(BaseModel):
    dia: Literal["Lunes", "Martes", "Miercoles", "Jueves", "Viernes"] | None = None
    hora_inicio: HoraLocal | None = None
    hora_fin: HoraLocal | None = None
    salon: str | None = None
    activo: bool | None = None


class HorarioOut(BaseModel):
    id_horario: int
    id_curso: int
    id_materia: int
    dia: str
    hora_inicio: HoraLocal
    hora_fin: HoraLocal
    salon: str
    activo: bool
    model_config = {"from_attributes": True}


class AsignarProfesorHorarioRequest(BaseModel):
    id_profesor: int
