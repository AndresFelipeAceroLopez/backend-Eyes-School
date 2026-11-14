from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

# N-13: una novedad sin descripción no le dice nada al acudiente; la app ya lo exigía, ahora
# también la API (para la web y cualquier otro cliente).
DescripcionNovedad = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


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
    descripcion: DescripcionNovedad
    accion_tomada: str | None = None


class NovedadUpdate(BaseModel):
    descripcion: DescripcionNovedad | None = None
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
