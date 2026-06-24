from datetime import date
from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.dependencies import DbSession, require_roles
from app.infrastructure.repositories.actores_repository import AdministradorRepository


class AdministradorCreate(BaseModel):
    id_usuario: int
    cargo: str
    nivel_acceso: Literal["Bajo", "Medio", "Alto"] = "Bajo"
    fecha_asignacion: date


class AdministradorOut(BaseModel):
    id_administrador: int
    id_usuario: int
    cargo: str
    nivel_acceso: str
    estado: str
    fecha_asignacion: date
    fecha_fin: date | None
    model_config = {"from_attributes": True}


router = APIRouter(prefix="/administradores", tags=["Administradores"])


@router.get("", response_model=list[AdministradorOut], dependencies=[require_roles("admin")])
async def list_admins(db: DbSession, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    items = await AdministradorRepository(db).get_all_with_usuario(skip=skip, limit=limit)
    return [AdministradorOut.model_validate(a) for a in items]


@router.post("", response_model=AdministradorOut, status_code=201, dependencies=[require_roles("admin")])
async def create_admin(data: AdministradorCreate, db: DbSession):
    item = await AdministradorRepository(db).create(data.model_dump())
    return AdministradorOut.model_validate(item)


@router.get("/{id_administrador}", response_model=AdministradorOut, dependencies=[require_roles("admin")])
async def get_admin(id_administrador: int, db: DbSession):
    from app.core.exceptions import NotFoundException
    item = await AdministradorRepository(db).get_by_id(id_administrador)
    if not item:
        raise NotFoundException("Administrador no encontrado")
    return AdministradorOut.model_validate(item)


@router.put("/{id_administrador}", response_model=AdministradorOut, dependencies=[require_roles("admin")])
async def update_admin(id_administrador: int, data: AdministradorCreate, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = AdministradorRepository(db)
    item = await repo.get_by_id(id_administrador)
    if not item:
        raise NotFoundException("Administrador no encontrado")
    updated = await repo.update(item, data.model_dump())
    return AdministradorOut.model_validate(updated)


@router.delete("/{id_administrador}", status_code=204, dependencies=[require_roles("admin")])
async def delete_admin(id_administrador: int, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = AdministradorRepository(db)
    item = await repo.get_by_id(id_administrador)
    if not item:
        raise NotFoundException("Administrador no encontrado")
    await repo.update(item, {"estado": "Inactivo"})
