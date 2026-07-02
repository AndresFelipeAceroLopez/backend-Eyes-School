from fastapi import APIRouter, Query

from app.application.profesores.schemas import (
    AgregarEspecializacionRequest,
    ProfesorCreate,
    ProfesorEspecializacionOut,
    ProfesorOut,
    ProfesorUpdate,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.profesores.service import ProfesorService
from app.core.dependencies import AuthUser, CurrentUser, DbSession, require_roles
from app.core.exceptions import ForbiddenException
from app.infrastructure.repositories.actores_repository import ProfesorRepository

router = APIRouter(prefix="/profesores", tags=["Profesores"])


async def _assert_propio_o_admin(db: AsyncSession, current_user: CurrentUser, id_profesor: int) -> None:
    """El admin gestiona a cualquier profesor; el docente, solo el suyo."""
    if current_user.nombre_rol == "admin":
        return
    propio = await ProfesorRepository(db).get_by_usuario(current_user.id_usuario)
    if propio is None or propio.id_profesor != id_profesor:
        raise ForbiddenException("Solo puede gestionar sus propias especializaciones")


# El docente necesita la lista para ver/cargar horarios (resolver nombre de
# profesor por curso/materia). Solo se abre la LECTURA de la lista; crear/editar/
# eliminar y el detalle individual siguen restringidos según corresponda.
@router.get("", response_model=list[ProfesorOut], dependencies=[require_roles("admin", "docente")])
async def list_profesores(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    estado: str | None = None,
):
    return await ProfesorService(db).list(skip=skip, limit=limit, estado=estado)


@router.post("", response_model=ProfesorOut, status_code=201, dependencies=[require_roles("admin")])
async def create_profesor(data: ProfesorCreate, db: DbSession):
    return await ProfesorService(db).create(data)


@router.get("/{id_profesor}", response_model=ProfesorOut, dependencies=[require_roles("admin", "docente")])
async def get_profesor(id_profesor: int, db: DbSession):
    return await ProfesorService(db).get(id_profesor)


@router.put("/{id_profesor}", response_model=ProfesorOut, dependencies=[require_roles("admin")])
async def update_profesor(id_profesor: int, data: ProfesorUpdate, db: DbSession):
    return await ProfesorService(db).update(id_profesor, data)


@router.delete("/{id_profesor}", status_code=204, dependencies=[require_roles("admin")])
async def delete_profesor(id_profesor: int, db: DbSession):
    await ProfesorService(db).delete(id_profesor)


@router.get("/{id_profesor}/especializaciones", response_model=list[ProfesorEspecializacionOut], dependencies=[require_roles("admin", "docente")])
async def get_especializaciones(id_profesor: int, db: DbSession):
    return await ProfesorService(db).get_especializaciones(id_profesor)


@router.post("/{id_profesor}/especializaciones", response_model=ProfesorEspecializacionOut, status_code=201, dependencies=[require_roles("admin", "docente")])
async def agregar_especializacion(id_profesor: int, data: AgregarEspecializacionRequest, db: DbSession, current_user: AuthUser):
    await _assert_propio_o_admin(db, current_user, id_profesor)
    return await ProfesorService(db).agregar_especializacion(id_profesor, data)


@router.delete("/{id_profesor}/especializaciones/{id_especializacion}", status_code=204, dependencies=[require_roles("admin", "docente")])
async def quitar_especializacion(id_profesor: int, id_especializacion: int, db: DbSession, current_user: AuthUser):
    await _assert_propio_o_admin(db, current_user, id_profesor)
    await ProfesorService(db).quitar_especializacion(id_profesor, id_especializacion)
