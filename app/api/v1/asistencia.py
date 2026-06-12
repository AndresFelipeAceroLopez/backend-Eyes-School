from datetime import date

from fastapi import APIRouter, Query

from app.application.asistencia.schemas import (
    AsistenciaAulaCreate,
    AsistenciaAulaOut,
    AsistenciaCreate,
    AsistenciaOut,
    AsistenciaQRCreate,
    AsistenciaUpdate,
)
from app.application.asistencia.service import AsistenciaService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])


@router.get("", response_model=list[AsistenciaOut], dependencies=[require_roles("admin", "docente")])
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


@router.post("/qr", response_model=AsistenciaOut, status_code=201, dependencies=[require_roles("docente")])
async def register_qr(data: AsistenciaQRCreate, db: DbSession):
    return await AsistenciaService(db).register_qr(data)


@router.get("/{id_asistencia}", response_model=AsistenciaOut, dependencies=[require_roles("admin", "docente")])
async def get_asistencia(id_asistencia: int, db: DbSession):
    return await AsistenciaService(db).get(id_asistencia)


@router.put("/{id_asistencia}", response_model=AsistenciaOut, dependencies=[require_roles("admin", "docente")])
async def update_asistencia(id_asistencia: int, data: AsistenciaUpdate, db: DbSession):
    return await AsistenciaService(db).update(id_asistencia, data)


@router.get("/aula", response_model=list[AsistenciaAulaOut], dependencies=[require_roles("admin", "docente")])
async def list_asistencia_aula(
    db: DbSession,
    id_horario: int | None = None,
    id_estudiante: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await AsistenciaService(db).list_aula(id_horario=id_horario, id_estudiante=id_estudiante, skip=skip, limit=limit)


@router.post("/aula", response_model=AsistenciaAulaOut, status_code=201, dependencies=[require_roles("docente")])
async def create_asistencia_aula(data: AsistenciaAulaCreate, db: DbSession):
    return await AsistenciaService(db).create_aula(data)
