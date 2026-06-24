from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.estudiantes.schemas import (
    EstudianteCreate,
    EstudianteIPSCreate,
    EstudianteIPSOut,
    EstudianteOut,
    EstudianteUpdate,
)
from app.core.exceptions import ConflictException, NotFoundException
from app.infrastructure.repositories.actores_repository import EstudianteRepository
from app.infrastructure.repositories.reportes_repository import EstudianteIPSRepository


class EstudianteService:
    def __init__(self, session: AsyncSession):
        self.repo = EstudianteRepository(session)
        self.ips_repo = EstudianteIPSRepository(session)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        id_curso: int | None = None,
        estado: str | None = None,
    ) -> list[EstudianteOut]:
        items = await self.repo.get_all_with_filters(skip=skip, limit=limit, id_curso=id_curso, estado=estado)
        return [EstudianteOut.model_validate(e) for e in items]

    async def get(self, id_estudiante: int) -> EstudianteOut:
        item = await self.repo.get_by_id(id_estudiante)
        if not item:
            raise NotFoundException("Estudiante no encontrado")
        return EstudianteOut.model_validate(item)

    async def create(self, data: EstudianteCreate) -> EstudianteOut:
        if await self.repo.codigo_exists(data.codigo_estudiante):
            raise ConflictException("El código de estudiante ya existe")
        item = await self.repo.create(data.model_dump())
        return EstudianteOut.model_validate(item)

    async def update(self, id_estudiante: int, data: EstudianteUpdate) -> EstudianteOut:
        item = await self.repo.get_by_id(id_estudiante)
        if not item:
            raise NotFoundException("Estudiante no encontrado")
        if data.codigo_estudiante and await self.repo.codigo_exists(data.codigo_estudiante, exclude_id=id_estudiante):
            raise ConflictException("El código ya está en uso")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return EstudianteOut.model_validate(updated)

    async def delete(self, id_estudiante: int) -> None:
        item = await self.repo.get_by_id(id_estudiante)
        if not item:
            raise NotFoundException("Estudiante no encontrado")
        await self.repo.update(item, {"estado": "Inactivo"})

    async def get_ips(self, id_estudiante: int) -> list[EstudianteIPSOut]:
        items = await self.ips_repo.get_by_estudiante(id_estudiante)
        return [EstudianteIPSOut.model_validate(i) for i in items]

    async def create_ips(self, id_estudiante: int, data: EstudianteIPSCreate) -> EstudianteIPSOut:
        existing = await self.ips_repo.get_one(id_estudiante, data.id_ips)
        if existing:
            raise ConflictException("La afiliación IPS ya existe")
        payload = data.model_dump()
        payload["id_estudiante"] = id_estudiante
        item = await self.ips_repo.create(payload)
        return EstudianteIPSOut.model_validate(item)

    async def delete_ips(self, id_estudiante: int, id_ips: int) -> None:
        item = await self.ips_repo.get_one(id_estudiante, id_ips)
        if not item:
            raise NotFoundException("Afiliación IPS no encontrada")
        await self.ips_repo.delete(item)
