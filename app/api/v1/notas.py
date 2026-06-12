from fastapi import APIRouter, Query

from app.application.notas.schemas import NotaCreate, NotaOut, NotaUpdate
from app.application.notas.service import NotaService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/notas", tags=["Notas"])


@router.get("", response_model=list[NotaOut], dependencies=[require_roles("admin", "docente")])
async def list_notas(
    db: DbSession,
    id_estudiante: int | None = None,
    id_materia: int | None = None,
    id_periodo: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await NotaService(db).list(
        id_estudiante=id_estudiante, id_materia=id_materia, id_periodo=id_periodo, skip=skip, limit=limit
    )


@router.post("", response_model=NotaOut, status_code=201, dependencies=[require_roles("docente")])
async def create_nota(data: NotaCreate, db: DbSession):
    return await NotaService(db).create(data)


@router.get("/{id_nota}", response_model=NotaOut, dependencies=[require_roles("admin", "docente")])
async def get_nota(id_nota: int, db: DbSession):
    return await NotaService(db).get(id_nota)


@router.put("/{id_nota}", response_model=NotaOut, dependencies=[require_roles("docente")])
async def update_nota(id_nota: int, data: NotaUpdate, db: DbSession):
    return await NotaService(db).update(id_nota, data)


@router.delete("/{id_nota}", status_code=204, dependencies=[require_roles("admin")])
async def delete_nota(id_nota: int, db: DbSession):
    await NotaService(db).delete(id_nota)
