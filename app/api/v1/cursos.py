from fastapi import APIRouter, Query

from app.application.cursos.schemas import CursoCreate, CursoOut, CursoUpdate
from app.application.cursos.service import CursoService
from app.application.estudiantes.schemas import EstudianteOut
from app.application.estudiantes.service import EstudianteService
from app.application.horarios.schemas import HorarioOut
from app.application.horarios.service import HorarioService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/cursos", tags=["Cursos"])


@router.get("", response_model=list[CursoOut])
async def list_cursos(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    activo: bool | None = None,
):
    return await CursoService(db).list(skip=skip, limit=limit, activo=activo)


@router.post("", response_model=CursoOut, status_code=201, dependencies=[require_roles("admin")])
async def create_curso(data: CursoCreate, db: DbSession):
    return await CursoService(db).create(data)


@router.get("/{id_curso}", response_model=CursoOut)
async def get_curso(id_curso: int, db: DbSession):
    return await CursoService(db).get(id_curso)


@router.put("/{id_curso}", response_model=CursoOut, dependencies=[require_roles("admin")])
async def update_curso(id_curso: int, data: CursoUpdate, db: DbSession):
    return await CursoService(db).update(id_curso, data)


@router.get("/{id_curso}/estudiantes", response_model=list[EstudianteOut], dependencies=[require_roles("admin", "docente")])
async def get_estudiantes_curso(id_curso: int, db: DbSession):
    return await EstudianteService(db).list(id_curso=id_curso)


@router.get("/{id_curso}/horarios", response_model=list[HorarioOut])
async def get_horarios_curso(id_curso: int, db: DbSession):
    return await HorarioService(db).list(id_curso=id_curso)
