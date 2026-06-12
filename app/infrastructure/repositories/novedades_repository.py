from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.novedades import NovedadModel, TipoNovedadModel
from app.infrastructure.repositories.base_repository import BaseRepository


class TipoNovedadRepository(BaseRepository[TipoNovedadModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(TipoNovedadModel, session)

    async def get_activos(self) -> list[TipoNovedadModel]:
        result = await self.session.execute(
            select(TipoNovedadModel).where(TipoNovedadModel.activo == True)  # noqa: E712
        )
        return list(result.scalars().all())


class NovedadRepository(BaseRepository[NovedadModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(NovedadModel, session)

    async def get_with_filters(
        self,
        id_estudiante: int | None = None,
        id_tipo_novedad: int | None = None,
        estado: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NovedadModel]:
        query = select(NovedadModel).options(
            selectinload(NovedadModel.tipo_novedad),
            selectinload(NovedadModel.estudiante),
        )
        if id_estudiante:
            query = query.where(NovedadModel.id_estudiante == id_estudiante)
        if id_tipo_novedad:
            query = query.where(NovedadModel.id_tipo_novedad == id_tipo_novedad)
        if estado:
            query = query.where(NovedadModel.estado == estado)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())
