from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.dependencies import DbSession, require_roles
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
    model_config = {"from_attributes": True}


router = APIRouter(prefix="/padres", tags=["Padres"])


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
