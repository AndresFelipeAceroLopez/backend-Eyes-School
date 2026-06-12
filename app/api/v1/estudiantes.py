from fastapi import APIRouter, Query

from app.application.estudiantes.schemas import (
    EstudianteCreate,
    EstudianteIPSCreate,
    EstudianteIPSOut,
    EstudianteOut,
    EstudianteUpdate,
)
from app.application.estudiantes.service import EstudianteService
from app.application.notas.schemas import NotaOut
from app.application.notas.service import NotaService
from app.application.asistencia.schemas import AsistenciaOut
from app.application.asistencia.service import AsistenciaService
from app.application.novedades.schemas import NovedadOut
from app.application.novedades.service import NovedadService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])


@router.get("", response_model=list[EstudianteOut], dependencies=[require_roles("admin", "docente")])
async def list_estudiantes(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    id_curso: int | None = None,
    estado: str | None = None,
):
    return await EstudianteService(db).list(skip=skip, limit=limit, id_curso=id_curso, estado=estado)


@router.post("", response_model=EstudianteOut, status_code=201, dependencies=[require_roles("admin")])
async def create_estudiante(data: EstudianteCreate, db: DbSession):
    return await EstudianteService(db).create(data)


@router.get("/{id_estudiante}", response_model=EstudianteOut, dependencies=[require_roles("admin", "docente", "padre")])
async def get_estudiante(id_estudiante: int, db: DbSession):
    return await EstudianteService(db).get(id_estudiante)


@router.put("/{id_estudiante}", response_model=EstudianteOut, dependencies=[require_roles("admin")])
async def update_estudiante(id_estudiante: int, data: EstudianteUpdate, db: DbSession):
    return await EstudianteService(db).update(id_estudiante, data)


@router.get("/{id_estudiante}/notas", response_model=list[NotaOut], dependencies=[require_roles("admin", "docente", "estudiante", "padre")])
async def get_notas_estudiante(
    id_estudiante: int,
    db: DbSession,
    id_periodo: int | None = None,
    id_materia: int | None = None,
):
    return await NotaService(db).list(id_estudiante=id_estudiante, id_materia=id_materia, id_periodo=id_periodo)


@router.get("/{id_estudiante}/asistencia", response_model=list[AsistenciaOut], dependencies=[require_roles("admin", "docente", "estudiante", "padre")])
async def get_asistencia_estudiante(
    id_estudiante: int,
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await AsistenciaService(db).list(id_estudiante=id_estudiante, skip=skip, limit=limit)


@router.get("/{id_estudiante}/novedades", response_model=list[NovedadOut], dependencies=[require_roles("admin", "docente", "padre")])
async def get_novedades_estudiante(id_estudiante: int, db: DbSession):
    return await NovedadService(db).list(id_estudiante=id_estudiante)


@router.get("/{id_estudiante}/ips", response_model=list[EstudianteIPSOut], dependencies=[require_roles("admin")])
async def get_ips_estudiante(id_estudiante: int, db: DbSession):
    return await EstudianteService(db).get_ips(id_estudiante)


@router.post("/{id_estudiante}/ips", response_model=EstudianteIPSOut, status_code=201, dependencies=[require_roles("admin")])
async def create_ips_estudiante(id_estudiante: int, data: EstudianteIPSCreate, db: DbSession):
    return await EstudianteService(db).create_ips(id_estudiante, data)
