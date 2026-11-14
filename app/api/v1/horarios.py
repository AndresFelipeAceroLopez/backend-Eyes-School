from fastapi import APIRouter, Query

from app.application.common.tipos import ENTERO32_MAX, Entero32
from app.application.horarios.schemas import (
    AsignarProfesorHorarioRequest,
    HorarioCreate,
    HorarioOut,
    HorarioUpdate,
)
from app.application.horarios.service import HorarioService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/horarios", tags=["Horarios"])


@router.get("", response_model=list[HorarioOut], dependencies=[require_roles("admin", "docente", "estudiante", "padre")])
async def list_horarios(
    db: DbSession,
    id_curso: Entero32 | None = None,
    skip: int = Query(0, ge=0, le=ENTERO32_MAX),
    limit: int = Query(100, ge=1, le=500),
):
    return await HorarioService(db).list(id_curso=id_curso, skip=skip, limit=limit)


@router.post("", response_model=HorarioOut, status_code=201, dependencies=[require_roles("admin")])
async def create_horario(data: HorarioCreate, db: DbSession):
    return await HorarioService(db).create(data)


@router.get("/{id_horario}", response_model=HorarioOut, dependencies=[require_roles("admin", "docente", "estudiante", "padre")])
async def get_horario(id_horario: Entero32, db: DbSession):
    return await HorarioService(db).get(id_horario)


@router.put("/{id_horario}", response_model=HorarioOut, dependencies=[require_roles("admin")])
async def update_horario(id_horario: Entero32, data: HorarioUpdate, db: DbSession):
    return await HorarioService(db).update(id_horario, data)


@router.delete("/{id_horario}", status_code=204, dependencies=[require_roles("admin")])
async def delete_horario(id_horario: Entero32, db: DbSession):
    await HorarioService(db).delete(id_horario)


@router.post("/{id_horario}/profesores", status_code=204, dependencies=[require_roles("admin")])
async def asignar_profesor(id_horario: Entero32, data: AsignarProfesorHorarioRequest, db: DbSession):
    await HorarioService(db).asignar_profesor(id_horario, data)
