from fastapi import APIRouter, Query

from app.application.novedades.schemas import (
    NovedadCreate,
    NovedadOut,
    NovedadUpdate,
    TipoNovedadCreate,
    TipoNovedadOut,
)
from app.application.novedades.service import NovedadService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(tags=["Novedades"])


@router.get("/tipos-novedad", response_model=list[TipoNovedadOut], dependencies=[require_roles("admin", "docente", "estudiante", "padre")])
async def list_tipos(db: DbSession):
    return await NovedadService(db).list_tipos()


@router.post("/tipos-novedad", response_model=TipoNovedadOut, status_code=201, dependencies=[require_roles("admin")])
async def create_tipo(data: TipoNovedadCreate, db: DbSession):
    return await NovedadService(db).create_tipo(data)


@router.put("/tipos-novedad/{id_tipo}", response_model=TipoNovedadOut, dependencies=[require_roles("admin")])
async def update_tipo(id_tipo: int, data: TipoNovedadCreate, db: DbSession):
    return await NovedadService(db).update_tipo(id_tipo, data)


@router.delete("/tipos-novedad/{id_tipo}", status_code=204, dependencies=[require_roles("admin")])
async def delete_tipo(id_tipo: int, db: DbSession):
    await NovedadService(db).delete_tipo(id_tipo)


# Listado global = vista de gestión. Profesor y admin hacen el CRUD completo.
# Estudiantes y padres NO lo consumen: leen las novedades del estudiante
# asociado vía /estudiantes/{id}/novedades.
@router.get("/novedades", response_model=list[NovedadOut], dependencies=[require_roles("admin", "docente")])
async def list_novedades(
    db: DbSession,
    id_estudiante: int | None = None,
    id_tipo: int | None = None,
    estado: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await NovedadService(db).list(id_estudiante=id_estudiante, id_tipo=id_tipo, estado=estado, skip=skip, limit=limit)


@router.post("/novedades", response_model=NovedadOut, status_code=201, dependencies=[require_roles("admin", "docente")])
async def create_novedad(data: NovedadCreate, db: DbSession):
    return await NovedadService(db).create(data)


@router.get("/novedades/{id_novedad}", response_model=NovedadOut, dependencies=[require_roles("admin", "docente")])
async def get_novedad(id_novedad: int, db: DbSession):
    return await NovedadService(db).get(id_novedad)


@router.put("/novedades/{id_novedad}", response_model=NovedadOut, dependencies=[require_roles("admin", "docente")])
async def update_novedad(id_novedad: int, data: NovedadUpdate, db: DbSession):
    return await NovedadService(db).update(id_novedad, data)


# CRUD completo de novedades = profesor y admin. El borrado que hace el admin
# al eliminar un usuario va además por la cascada de DELETE /usuarios/{id}.
@router.delete("/novedades/{id_novedad}", status_code=204, dependencies=[require_roles("admin", "docente")])
async def delete_novedad(id_novedad: int, db: DbSession):
    await NovedadService(db).delete(id_novedad)
