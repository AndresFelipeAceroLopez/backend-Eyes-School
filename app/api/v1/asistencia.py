from datetime import date

from fastapi import APIRouter, Query

from app.application.asistencia.schemas import (
    AsistenciaCreate,
    AsistenciaOut,
    AsistenciaUpdate,
)
from app.application.asistencia.service import AsistenciaService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])


@router.get("", response_model=list[AsistenciaOut], dependencies=[require_roles("admin", "docente", "padre", "estudiante")])
async def list_asistencia(
    db: DbSession,
    id_estudiante: int | None = None,
    fecha: date | None = None,
    tipo: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await AsistenciaService(db).list(id_estudiante=id_estudiante, fecha=fecha, tipo=tipo, skip=skip, limit=limit)


@router.post("", response_model=AsistenciaOut, status_code=201, dependencies=[require_roles("admin", "docente")])
async def create_asistencia(data: AsistenciaCreate, db: DbSession):
    return await AsistenciaService(db).create(data)


@router.get("/{id_asistencia}", response_model=AsistenciaOut, dependencies=[require_roles("admin", "docente", "padre", "estudiante")])
async def get_asistencia(id_asistencia: int, db: DbSession):
    return await AsistenciaService(db).get(id_asistencia)


@router.put("/{id_asistencia}", response_model=AsistenciaOut, dependencies=[require_roles("admin", "docente")])
async def update_asistencia(id_asistencia: int, data: AsistenciaUpdate, db: DbSession):
    return await AsistenciaService(db).update(id_asistencia, data)


@router.delete("/{id_asistencia}", status_code=204, dependencies=[require_roles("admin")])
async def delete_asistencia(id_asistencia: int, db: DbSession):
    await AsistenciaService(db).delete(id_asistencia)
