from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.horarios.schemas import AsignarProfesorHorarioRequest, HorarioCreate, HorarioOut, HorarioUpdate
from app.core.exceptions import NotFoundException
from app.infrastructure.repositories.academico_repository import HorarioRepository


class HorarioService:
    def __init__(self, session: AsyncSession):
        self.repo = HorarioRepository(session)

    async def list(self, id_curso: int | None = None, skip: int = 0, limit: int = 100) -> list[HorarioOut]:
        if id_curso:
            items = await self.repo.get_by_curso(id_curso)
        else:
            items = await self.repo.get_all(skip=skip, limit=limit)
        return [HorarioOut.model_validate(h) for h in items]

    async def get(self, id_horario: int) -> HorarioOut:
        item = await self.repo.get_by_id(id_horario)
        if not item:
            raise NotFoundException("Horario no encontrado")
        return HorarioOut.model_validate(item)

    async def create(self, data: HorarioCreate) -> HorarioOut:
        item = await self.repo.create(data.model_dump())
        return HorarioOut.model_validate(item)

    async def update(self, id_horario: int, data: HorarioUpdate) -> HorarioOut:
        item = await self.repo.get_by_id(id_horario)
        if not item:
            raise NotFoundException("Horario no encontrado")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return HorarioOut.model_validate(updated)

    async def delete(self, id_horario: int) -> None:
        item = await self.repo.get_by_id(id_horario)
        if not item:
            raise NotFoundException("Horario no encontrado")
        await self.repo.update(item, {"activo": False})

    async def asignar_profesor(self, id_horario: int, data: AsignarProfesorHorarioRequest) -> None:
        from app.infrastructure.models.academico import ProfesorHorarioModel
        from app.infrastructure.repositories.base_repository import BaseRepository
        repo = BaseRepository(ProfesorHorarioModel, self.repo.session)
        await repo.create({"id_profesor": data.id_profesor, "id_horario": id_horario})
