from fastapi import APIRouter, Query

from app.application.asignaciones.schemas import AsignacionCreate, AsignacionOut, AsignacionUpdate
from app.application.asignaciones.service import AsignacionService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/asignaciones", tags=["Asignaciones"])


@router.get("", response_model=list[AsignacionOut], dependencies=[require_roles("admin", "docente")])
async def list_asignaciones(
    db: DbSession,
    id_profesor: int | None = None,
    id_curso: int | None = None,
    id_materia: int | None = None,
    activo: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await AsignacionService(db).list(
        id_profesor=id_profesor, id_curso=id_curso, id_materia=id_materia, activo=activo, skip=skip, limit=limit
    )


@router.post("", response_model=AsignacionOut, status_code=201, dependencies=[require_roles("admin")])
async def create_asignacion(data: AsignacionCreate, db: DbSession):
    return await AsignacionService(db).create(data)


@router.get("/{id_asignacion}", response_model=AsignacionOut, dependencies=[require_roles("admin", "docente")])
async def get_asignacion(id_asignacion: int, db: DbSession):
    return await AsignacionService(db).get(id_asignacion)


@router.put("/{id_asignacion}", response_model=AsignacionOut, dependencies=[require_roles("admin")])
async def update_asignacion(id_asignacion: int, data: AsignacionUpdate, db: DbSession):
    return await AsignacionService(db).update(id_asignacion, data)


@router.delete("/{id_asignacion}", status_code=204, dependencies=[require_roles("admin")])
async def delete_asignacion(id_asignacion: int, db: DbSession):
    await AsignacionService(db).delete(id_asignacion)
