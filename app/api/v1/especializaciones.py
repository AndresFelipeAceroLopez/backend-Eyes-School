from fastapi import APIRouter

from app.application.profesores.schemas import EspecializacionOut
from app.core.dependencies import DbSession, require_roles
from app.infrastructure.repositories.academico_repository import EspecializacionRepository
from pydantic import BaseModel


class EspecializacionCreate(BaseModel):
    nombre_especializacion: str
    descripcion: str | None = None


router = APIRouter(prefix="/especializaciones", tags=["Especializaciones"])


# Listado público (como GET /cursos): lo consume el formulario de registro,
# donde el usuario aún no está autenticado y no puede enviar token. Solo expone
# nombres de especializaciones; el alta/edición/baja sigue restringida a admin.
@router.get("", response_model=list[EspecializacionOut])
async def list_especializaciones(db: DbSession):
    items = await EspecializacionRepository(db).get_all()
    return [EspecializacionOut.model_validate(e) for e in items]


@router.post("", response_model=EspecializacionOut, status_code=201, dependencies=[require_roles("admin")])
async def create_especializacion(data: EspecializacionCreate, db: DbSession):
    item = await EspecializacionRepository(db).create(data.model_dump())
    return EspecializacionOut.model_validate(item)


@router.get("/{id_especializacion}", response_model=EspecializacionOut, dependencies=[require_roles("admin")])
async def get_especializacion(id_especializacion: int, db: DbSession):
    from app.core.exceptions import NotFoundException
    item = await EspecializacionRepository(db).get_by_id(id_especializacion)
    if not item:
        raise NotFoundException("Especialización no encontrada")
    return EspecializacionOut.model_validate(item)


@router.put("/{id_especializacion}", response_model=EspecializacionOut, dependencies=[require_roles("admin")])
async def update_especializacion(id_especializacion: int, data: EspecializacionCreate, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = EspecializacionRepository(db)
    item = await repo.get_by_id(id_especializacion)
    if not item:
        raise NotFoundException("Especialización no encontrada")
    updated = await repo.update(item, data.model_dump())
    return EspecializacionOut.model_validate(updated)


@router.delete("/{id_especializacion}", status_code=204, dependencies=[require_roles("admin")])
async def delete_especializacion(id_especializacion: int, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = EspecializacionRepository(db)
    item = await repo.get_by_id(id_especializacion)
    if not item:
        raise NotFoundException("Especialización no encontrada")
    await repo.update(item, {"activo": False})
