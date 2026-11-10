from datetime import date

from fastapi import APIRouter, Query

from app.application.asistencia.schemas import (
    AsistenciaCreate,
    AsistenciaOut,
    AsistenciaUpdate,
)
from app.application.asistencia.service import AsistenciaService
from app.application.common.authz import assert_acceso_estudiante
from app.core.dependencies import AuthUser, DbSession, require_roles
from app.core.exceptions import BusinessRuleException

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])

# Roles que solo pueden ver la asistencia de sus propios estudiantes.
_ROLES_CON_PROPIEDAD = ("padre", "estudiante")


@router.get("", response_model=list[AsistenciaOut], dependencies=[require_roles("admin", "docente", "padre", "estudiante")])
async def list_asistencia(
    db: DbSession,
    current_user: AuthUser,
    id_estudiante: int | None = None,
    fecha: date | None = None,
    tipo: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    if current_user.nombre_rol in _ROLES_CON_PROPIEDAD:
        # Sin filtro devolvería la asistencia de todos los estudiantes.
        if id_estudiante is None:
            raise BusinessRuleException("Debe indicar el estudiante (id_estudiante)")
        await assert_acceso_estudiante(db, current_user, id_estudiante)
    return await AsistenciaService(db).list(id_estudiante=id_estudiante, fecha=fecha, tipo=tipo, skip=skip, limit=limit)


@router.post("", response_model=AsistenciaOut, status_code=201, dependencies=[require_roles("admin", "docente")])
async def create_asistencia(data: AsistenciaCreate, db: DbSession, current_user: AuthUser):
    return await AsistenciaService(db).create(data, registrado_por=current_user.id_usuario)


@router.get("/{id_asistencia}", response_model=AsistenciaOut, dependencies=[require_roles("admin", "docente", "padre", "estudiante")])
async def get_asistencia(id_asistencia: int, db: DbSession, current_user: AuthUser):
    item = await AsistenciaService(db).get(id_asistencia)
    if current_user.nombre_rol in _ROLES_CON_PROPIEDAD:
        await assert_acceso_estudiante(db, current_user, item.id_estudiante)
    return item


@router.put("/{id_asistencia}", response_model=AsistenciaOut, dependencies=[require_roles("admin", "docente")])
async def update_asistencia(id_asistencia: int, data: AsistenciaUpdate, db: DbSession):
    return await AsistenciaService(db).update(id_asistencia, data)


@router.delete("/{id_asistencia}", status_code=204, dependencies=[require_roles("admin")])
async def delete_asistencia(id_asistencia: int, db: DbSession):
    await AsistenciaService(db).delete(id_asistencia)
