from fastapi import APIRouter, Query

from app.application.padres.schemas import HijoOut, PadreCreate, PadreOut
from app.application.padres.service import PadreService
from app.core.dependencies import AuthUser, DbSession, require_roles
from app.core.exceptions import ForbiddenException, NotFoundException
from app.infrastructure.repositories.actores_repository import PadreRepository

router = APIRouter(prefix="/padres", tags=["Padres"])


@router.get("/me", response_model=PadreOut, dependencies=[require_roles("padre")])
async def get_mi_padre(current_user: AuthUser, db: DbSession, id_estudiante: int | None = None):
    """Vínculo del acudiente con uno de sus hijos (el primero si no se indica `id_estudiante`)."""
    return await PadreService(db).mi_vinculo(current_user.id_usuario, id_estudiante)


@router.get("/me/hijos", response_model=list[HijoOut], dependencies=[require_roles("padre")])
async def list_mis_hijos(current_user: AuthUser, db: DbSession):
    return await PadreService(db).hijos(current_user.id_usuario)


@router.get("", response_model=list[PadreOut], dependencies=[require_roles("admin")])
async def list_padres(db: DbSession, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    items = await PadreRepository(db).get_all(skip=skip, limit=limit)
    return [PadreOut.model_validate(p) for p in items]


@router.post("", response_model=PadreOut, status_code=201, dependencies=[require_roles("admin")])
async def create_padre(data: PadreCreate, db: DbSession):
    item = await PadreRepository(db).create(data.model_dump())
    return PadreOut.model_validate(item)


@router.get("/{id_padre}", response_model=PadreOut, dependencies=[require_roles("admin", "padre")])
async def get_padre(id_padre: int, db: DbSession, current_user: AuthUser):
    item = await PadreRepository(db).get_by_id(id_padre)
    if not item:
        raise NotFoundException("Padre no encontrado")
    # Un acudiente solo puede ver sus propios vínculos, no los de otro acudiente.
    if current_user.nombre_rol == "padre" and item.id_usuario != current_user.id_usuario:
        raise ForbiddenException()
    return PadreOut.model_validate(item)


@router.put("/{id_padre}", response_model=PadreOut, dependencies=[require_roles("admin")])
async def update_padre(id_padre: int, data: PadreCreate, db: DbSession):
    repo = PadreRepository(db)
    item = await repo.get_by_id(id_padre)
    if not item:
        raise NotFoundException("Padre no encontrado")
    updated = await repo.update(item, data.model_dump())
    return PadreOut.model_validate(updated)


@router.delete("/{id_padre}", status_code=204, dependencies=[require_roles("admin")])
async def delete_padre(id_padre: int, db: DbSession):
    repo = PadreRepository(db)
    item = await repo.get_by_id(id_padre)
    if not item:
        raise NotFoundException("Padre no encontrado")
    await repo.delete(item)
