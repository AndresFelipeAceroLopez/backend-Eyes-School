from pydantic import BaseModel


class MateriaCreate(BaseModel):
    nombre_materia: str
    codigo_materia: str
    activa: bool = True


class MateriaUpdate(BaseModel):
    nombre_materia: str | None = None
    codigo_materia: str | None = None
    activa: bool | None = None


class MateriaOut(BaseModel):
    id_materia: int
    nombre_materia: str
    codigo_materia: str
    activa: bool
    model_config = {"from_attributes": True}
