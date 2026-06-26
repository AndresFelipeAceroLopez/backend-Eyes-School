from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.dependencies import AuthUser, DbSession, require_roles
from app.infrastructure.repositories.actores_repository import PadreRepository


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


router = APIRouter(prefix="/padres", tags=["Padres"])


@router.get("/me", response_model=PadreOut, dependencies=[require_roles("padre")])
async def get_mi_padre(current_user: AuthUser, db: DbSession):
    from app.core.exceptions import NotFoundException
    from app.infrastructure.models.actores import EstudianteModel
    from app.infrastructure.models.usuario import UsuarioModel
    item = await PadreRepository(db).get_by_usuario(current_user.id_usuario)
    if not item:
        raise NotFoundException("Perfil padre no encontrado")
    out = PadreOut.model_validate(item)
    # Resuelve nombre y documento del estudiante asociado (estudiante → usuario).
    estudiante = await db.get(EstudianteModel, item.id_estudiante)
    if estudiante:
        usuario = await db.get(UsuarioModel, estudiante.id_usuario)
        if usuario:
            out.nombre_estudiante = f"{usuario.primer_nombre} {usuario.primer_apellido}"
            out.documento_estudiante = usuario.numero_documento
    return out


@router.get("", response_model=list[PadreOut], dependencies=[require_roles("admin")])
async def list_padres(db: DbSession, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    items = await PadreRepository(db).get_all(skip=skip, limit=limit)
    return [PadreOut.model_validate(p) for p in items]


@router.post("", response_model=PadreOut, status_code=201, dependencies=[require_roles("admin")])
async def create_padre(data: PadreCreate, db: DbSession):
    item = await PadreRepository(db).create(data.model_dump())
    return PadreOut.model_validate(item)


@router.get("/{id_padre}", response_model=PadreOut, dependencies=[require_roles("admin", "padre")])
async def get_padre(id_padre: int, db: DbSession):
    from app.core.exceptions import NotFoundException
    item = await PadreRepository(db).get_by_id(id_padre)
    if not item:
        raise NotFoundException("Padre no encontrado")
    return PadreOut.model_validate(item)


@router.put("/{id_padre}", response_model=PadreOut, dependencies=[require_roles("admin")])
async def update_padre(id_padre: int, data: PadreCreate, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = PadreRepository(db)
    item = await repo.get_by_id(id_padre)
    if not item:
        raise NotFoundException("Padre no encontrado")
    updated = await repo.update(item, data.model_dump())
    return PadreOut.model_validate(updated)


@router.delete("/{id_padre}", status_code=204, dependencies=[require_roles("admin")])
async def delete_padre(id_padre: int, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = PadreRepository(db)
    item = await repo.get_by_id(id_padre)
    if not item:
        raise NotFoundException("Padre no encontrado")
    await repo.delete(item)
