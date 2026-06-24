from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.novedades.schemas import (
    NovedadCreate,
    NovedadOut,
    NovedadUpdate,
    TipoNovedadCreate,
    TipoNovedadOut,
)
from app.core.exceptions import NotFoundException
from app.infrastructure.repositories.novedades_repository import NovedadRepository, TipoNovedadRepository


class NovedadService:
    def __init__(self, session: AsyncSession):
        self.repo = NovedadRepository(session)
        self.tipo_repo = TipoNovedadRepository(session)

    async def list_tipos(self) -> list[TipoNovedadOut]:
        items = await self.tipo_repo.get_activos()
        return [TipoNovedadOut.model_validate(t) for t in items]

    async def create_tipo(self, data: TipoNovedadCreate) -> TipoNovedadOut:
        item = await self.tipo_repo.create(data.model_dump())
        return TipoNovedadOut.model_validate(item)

    async def update_tipo(self, id_tipo: int, data: TipoNovedadCreate) -> TipoNovedadOut:
        item = await self.tipo_repo.get_by_id(id_tipo)
        if not item:
            raise NotFoundException("Tipo de novedad no encontrado")
        updated = await self.tipo_repo.update(item, data.model_dump())
        return TipoNovedadOut.model_validate(updated)

    async def delete_tipo(self, id_tipo: int) -> None:
        item = await self.tipo_repo.get_by_id(id_tipo)
        if not item:
            raise NotFoundException("Tipo de novedad no encontrado")
        await self.tipo_repo.update(item, {"activo": False})

    async def list(
        self,
        id_estudiante: int | None = None,
        id_tipo: int | None = None,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NovedadOut]:
        items = await self.repo.get_with_filters(
            id_estudiante=id_estudiante, id_tipo_novedad=id_tipo, estado=estado, skip=skip, limit=limit
        )
        return [NovedadOut.model_validate(n) for n in items]

    async def get(self, id_novedad: int) -> NovedadOut:
        item = await self.repo.get_by_id(id_novedad)
        if not item:
            raise NotFoundException("Novedad no encontrada")
        return NovedadOut.model_validate(item)

    async def create(self, data: NovedadCreate) -> NovedadOut:
        item = await self.repo.create(data.model_dump())
        return NovedadOut.model_validate(item)

    async def update(self, id_novedad: int, data: NovedadUpdate) -> NovedadOut:
        item = await self.repo.get_by_id(id_novedad)
        if not item:
            raise NotFoundException("Novedad no encontrada")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return NovedadOut.model_validate(updated)

    async def delete(self, id_novedad: int) -> None:
        item = await self.repo.get_by_id(id_novedad)
        if not item:
            raise NotFoundException("Novedad no encontrada")
        await self.repo.delete(item)
