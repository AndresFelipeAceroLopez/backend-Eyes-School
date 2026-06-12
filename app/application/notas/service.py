from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.notas.schemas import NotaCreate, NotaOut, NotaUpdate
from app.core.exceptions import ConflictException, NotFoundException
from app.infrastructure.repositories.notas_repository import NotaRepository


class NotaService:
    def __init__(self, session: AsyncSession):
        self.repo = NotaRepository(session)

    async def list(
        self,
        id_estudiante: int | None = None,
        id_materia: int | None = None,
        id_periodo: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotaOut]:
        items = await self.repo.get_with_filters(
            id_estudiante=id_estudiante, id_materia=id_materia, id_periodo=id_periodo, skip=skip, limit=limit
        )
        return [NotaOut.model_validate(n) for n in items]

    async def get(self, id_nota: int) -> NotaOut:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        return NotaOut.model_validate(item)

    async def create(self, data: NotaCreate) -> NotaOut:
        if await self.repo.exists(data.id_estudiante, data.id_materia, data.id_periodo):
            raise ConflictException("Ya existe una nota para este estudiante, materia y período")
        item = await self.repo.create(data.model_dump())
        return NotaOut.model_validate(item)

    async def update(self, id_nota: int, data: NotaUpdate) -> NotaOut:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return NotaOut.model_validate(updated)

    async def delete(self, id_nota: int) -> None:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        await self.repo.delete(item)

    async def get_promedio(self, id_estudiante: int) -> float | None:
        return await self.repo.get_promedio_estudiante(id_estudiante)
