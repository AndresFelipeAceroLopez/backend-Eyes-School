from fastapi import APIRouter, Query

from app.application.profesores.schemas import (
    AgregarEspecializacionRequest,
    ProfesorCreate,
    ProfesorEspecializacionOut,
    ProfesorOut,
    ProfesorUpdate,
)
from app.application.profesores.service import ProfesorService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/profesores", tags=["Profesores"])


@router.get("", response_model=list[ProfesorOut], dependencies=[require_roles("admin")])
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


@router.get("/{id_profesor}/especializaciones", response_model=list[ProfesorEspecializacionOut], dependencies=[require_roles("admin", "docente")])
async def get_especializaciones(id_profesor: int, db: DbSession):
    return await ProfesorService(db).get_especializaciones(id_profesor)


@router.post("/{id_profesor}/especializaciones", response_model=ProfesorEspecializacionOut, status_code=201, dependencies=[require_roles("admin")])
async def agregar_especializacion(id_profesor: int, data: AgregarEspecializacionRequest, db: DbSession):
    return await ProfesorService(db).agregar_especializacion(id_profesor, data)


@router.delete("/{id_profesor}/especializaciones/{id_especializacion}", status_code=204, dependencies=[require_roles("admin")])
async def quitar_especializacion(id_profesor: int, id_especializacion: int, db: DbSession):
    await ProfesorService(db).quitar_especializacion(id_profesor, id_especializacion)
