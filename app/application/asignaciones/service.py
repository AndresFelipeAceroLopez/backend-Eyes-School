from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.asignaciones.schemas import AsignacionCreate, AsignacionOut, AsignacionUpdate
from app.core.exceptions import NotFoundException
from app.infrastructure.repositories.academico_repository import AsignacionRepository


class AsignacionService:
    def __init__(self, session: AsyncSession):
        self.repo = AsignacionRepository(session)

    async def list(
        self,
        id_profesor: int | None = None,
        id_curso: int | None = None,
        id_materia: int | None = None,
        activo: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsignacionOut]:
        items = await self.repo.get_with_filters(
            id_profesor=id_profesor, id_curso=id_curso, id_materia=id_materia, activo=activo, skip=skip, limit=limit
        )
        return [AsignacionOut.model_validate(a) for a in items]

    async def get(self, id_asignacion: int) -> AsignacionOut:
        item = await self.repo.get_by_id(id_asignacion)
        if not item:
            raise NotFoundException("Asignación no encontrada")
        return AsignacionOut.model_validate(item)

    async def create(self, data: AsignacionCreate) -> AsignacionOut:
        item = await self.repo.create(data.model_dump())
        return AsignacionOut.model_validate(item)

    async def update(self, id_asignacion: int, data: AsignacionUpdate) -> AsignacionOut:
        item = await self.repo.get_by_id(id_asignacion)
        if not item:
            raise NotFoundException("Asignación no encontrada")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return AsignacionOut.model_validate(updated)

    async def delete(self, id_asignacion: int) -> None:
        item = await self.repo.get_by_id(id_asignacion)
        if not item:
            raise NotFoundException("Asignación no encontrada")
        await self.repo.update(item, {"activo": False})
