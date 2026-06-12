from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.profesores.schemas import (
    AgregarEspecializacionRequest,
    ProfesorCreate,
    ProfesorEspecializacionOut,
    ProfesorOut,
    ProfesorUpdate,
)
from app.core.exceptions import ConflictException, NotFoundException
from app.infrastructure.repositories.academico_repository import ProfesorEspecializacionRepository
from app.infrastructure.repositories.actores_repository import ProfesorRepository


class ProfesorService:
    def __init__(self, session: AsyncSession):
        self.repo = ProfesorRepository(session)
        self.esp_repo = ProfesorEspecializacionRepository(session)

    async def list(self, skip: int = 0, limit: int = 100, estado: str | None = None) -> list[ProfesorOut]:
        items = await self.repo.get_all_with_usuario(skip=skip, limit=limit, estado=estado)
        return [ProfesorOut.model_validate(p) for p in items]

    async def get(self, id_profesor: int) -> ProfesorOut:
        item = await self.repo.get_by_id(id_profesor)
        if not item:
            raise NotFoundException("Profesor no encontrado")
        return ProfesorOut.model_validate(item)

    async def create(self, data: ProfesorCreate) -> ProfesorOut:
        if await self.repo.codigo_exists(data.codigo_profesor):
            raise ConflictException("El código de profesor ya existe")
        item = await self.repo.create(data.model_dump())
        return ProfesorOut.model_validate(item)

    async def update(self, id_profesor: int, data: ProfesorUpdate) -> ProfesorOut:
        item = await self.repo.get_by_id(id_profesor)
        if not item:
            raise NotFoundException("Profesor no encontrado")
        if data.codigo_profesor and await self.repo.codigo_exists(data.codigo_profesor, exclude_id=id_profesor):
            raise ConflictException("El código de profesor ya existe")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return ProfesorOut.model_validate(updated)

    async def get_especializaciones(self, id_profesor: int) -> list[ProfesorEspecializacionOut]:
        items = await self.esp_repo.get_by_profesor(id_profesor)
        return [ProfesorEspecializacionOut.model_validate(e) for e in items]

    async def agregar_especializacion(self, id_profesor: int, data: AgregarEspecializacionRequest) -> ProfesorEspecializacionOut:
        existing = await self.esp_repo.get_one(id_profesor, data.id_especializacion)
        if existing:
            raise ConflictException("El profesor ya tiene esta especialización")
        item = await self.esp_repo.create({
            "id_profesor": id_profesor,
            "id_especializacion": data.id_especializacion,
            "institucion": data.institucion,
        })
        return ProfesorEspecializacionOut.model_validate(item)

    async def quitar_especializacion(self, id_profesor: int, id_especializacion: int) -> None:
        item = await self.esp_repo.get_one(id_profesor, id_especializacion)
        if not item:
            raise NotFoundException("Especialización no encontrada")
        await self.esp_repo.delete(item)
