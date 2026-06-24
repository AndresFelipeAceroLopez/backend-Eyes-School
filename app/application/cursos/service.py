from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.cursos.schemas import CursoCreate, CursoOut, CursoUpdate
from app.core.exceptions import NotFoundException
from app.infrastructure.repositories.academico_repository import CursoRepository


class CursoService:
    def __init__(self, session: AsyncSession):
        self.repo = CursoRepository(session)

    async def list(self, skip: int = 0, limit: int = 100, activo: bool | None = None) -> list[CursoOut]:
        if activo is True:
            items = await self.repo.get_activos(skip=skip, limit=limit)
        else:
            items = await self.repo.get_all(skip=skip, limit=limit)
        return [CursoOut.model_validate(c) for c in items]

    async def get(self, id_curso: int) -> CursoOut:
        item = await self.repo.get_by_id(id_curso)
        if not item:
            raise NotFoundException("Curso no encontrado")
        return CursoOut.model_validate(item)

    async def create(self, data: CursoCreate) -> CursoOut:
        item = await self.repo.create(data.model_dump())
        return CursoOut.model_validate(item)

    async def update(self, id_curso: int, data: CursoUpdate) -> CursoOut:
        item = await self.repo.get_by_id(id_curso)
        if not item:
            raise NotFoundException("Curso no encontrado")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return CursoOut.model_validate(updated)

    async def delete(self, id_curso: int) -> None:
        item = await self.repo.get_by_id(id_curso)
        if not item:
            raise NotFoundException("Curso no encontrado")
        await self.repo.update(item, {"activo": False})
