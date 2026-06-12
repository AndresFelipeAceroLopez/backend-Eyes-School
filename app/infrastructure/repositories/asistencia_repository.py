from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.asistencia import AsistenciaAulaModel, AsistenciaModel
from app.infrastructure.repositories.base_repository import BaseRepository


class AsistenciaRepository(BaseRepository[AsistenciaModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(AsistenciaModel, session)

    async def get_by_estudiante(
        self,
        id_estudiante: int,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsistenciaModel]:
        query = select(AsistenciaModel).where(
            AsistenciaModel.id_estudiante == id_estudiante,
            AsistenciaModel.activo == True,  # noqa: E712
        )
        if fecha_inicio:
            query = query.where(AsistenciaModel.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.where(AsistenciaModel.fecha <= fecha_fin)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_with_filters(
        self,
        id_estudiante: int | None = None,
        fecha: date | None = None,
        tipo: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsistenciaModel]:
        query = select(AsistenciaModel).options(selectinload(AsistenciaModel.estudiante))
        if id_estudiante:
            query = query.where(AsistenciaModel.id_estudiante == id_estudiante)
        if fecha:
            query = query.where(AsistenciaModel.fecha == fecha)
        if tipo:
            query = query.where(AsistenciaModel.tipo == tipo)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_by_codigo_qr(self, codigo_qr: str, fecha: date) -> AsistenciaModel | None:
        result = await self.session.execute(
            select(AsistenciaModel).where(
                AsistenciaModel.codigo_qr == codigo_qr,
                AsistenciaModel.fecha == fecha,
            )
        )
        return result.scalar_one_or_none()


class AsistenciaAulaRepository(BaseRepository[AsistenciaAulaModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(AsistenciaAulaModel, session)

    async def get_by_horario_fecha(self, id_horario: int, fecha: date) -> list[AsistenciaAulaModel]:
        result = await self.session.execute(
            select(AsistenciaAulaModel)
            .options(selectinload(AsistenciaAulaModel.estudiante))
            .where(
                AsistenciaAulaModel.id_horario == id_horario,
                AsistenciaAulaModel.fecha == fecha,
            )
        )
        return list(result.scalars().all())

    async def get_by_estudiante(self, id_estudiante: int, skip: int = 0, limit: int = 100) -> list[AsistenciaAulaModel]:
        result = await self.session.execute(
            select(AsistenciaAulaModel)
            .options(selectinload(AsistenciaAulaModel.horario))
            .where(AsistenciaAulaModel.id_estudiante == id_estudiante)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
