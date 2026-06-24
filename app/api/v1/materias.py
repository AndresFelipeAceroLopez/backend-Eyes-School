from fastapi import APIRouter

from app.application.materias import schemas as s
from app.core.dependencies import DbSession, require_roles
from app.infrastructure.repositories.academico_repository import MateriaRepository

router = APIRouter(prefix="/materias", tags=["Materias"])


@router.get("", response_model=list[s.MateriaOut])
async def list_materias(db: DbSession):
    repo = MateriaRepository(db)
    items = await repo.get_all()
    return [s.MateriaOut.model_validate(m) for m in items]


@router.post("", response_model=s.MateriaOut, status_code=201, dependencies=[require_roles("admin")])
async def create_materia(data: s.MateriaCreate, db: DbSession):
    repo = MateriaRepository(db)
    item = await repo.create(data.model_dump())
    return s.MateriaOut.model_validate(item)


@router.get("/{id_materia}", response_model=s.MateriaOut)
async def get_materia(id_materia: int, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = MateriaRepository(db)
    item = await repo.get_by_id(id_materia)
    if not item:
        raise NotFoundException("Materia no encontrada")
    return s.MateriaOut.model_validate(item)


@router.put("/{id_materia}", response_model=s.MateriaOut, dependencies=[require_roles("admin")])
async def update_materia(id_materia: int, data: s.MateriaUpdate, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = MateriaRepository(db)
    item = await repo.get_by_id(id_materia)
    if not item:
        raise NotFoundException("Materia no encontrada")
    updated = await repo.update(item, data.model_dump(exclude_none=True))
    return s.MateriaOut.model_validate(updated)


@router.delete("/{id_materia}", status_code=204, dependencies=[require_roles("admin")])
async def delete_materia(id_materia: int, db: DbSession):
    from app.core.exceptions import NotFoundException
    repo = MateriaRepository(db)
    item = await repo.get_by_id(id_materia)
    if not item:
        raise NotFoundException("Materia no encontrada")
    await repo.update(item, {"activa": False})
