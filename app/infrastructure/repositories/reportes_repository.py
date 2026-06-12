from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.reportes import EstudianteIPSModel, ReporteModel
from app.infrastructure.repositories.base_repository import BaseRepository


class ReporteRepository(BaseRepository[ReporteModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(ReporteModel, session)

    async def get_by_administrador(self, id_administrador: int, skip: int = 0, limit: int = 100) -> list[ReporteModel]:
        result = await self.session.execute(
            select(ReporteModel)
            .where(ReporteModel.id_administrador == id_administrador)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class EstudianteIPSRepository(BaseRepository[EstudianteIPSModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(EstudianteIPSModel, session)

    async def get_by_estudiante(self, id_estudiante: int) -> list[EstudianteIPSModel]:
        result = await self.session.execute(
            select(EstudianteIPSModel).where(
                EstudianteIPSModel.id_estudiante == id_estudiante,
                EstudianteIPSModel.activo == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_one(self, id_estudiante: int, id_ips: int) -> EstudianteIPSModel | None:
        result = await self.session.execute(
            select(EstudianteIPSModel).where(
                EstudianteIPSModel.id_estudiante == id_estudiante,
                EstudianteIPSModel.id_ips == id_ips,
            )
        )
        return result.scalar_one_or_none()
