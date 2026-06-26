from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.actores import EstudianteModel
from app.infrastructure.models.notas import NotaModel
from app.infrastructure.repositories.base_repository import BaseRepository


class NotaRepository(BaseRepository[NotaModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(NotaModel, session)

    async def get_estudiante_con_usuario(self, id_estudiante: int) -> EstudianteModel | None:
        result = await self.session.execute(
            select(EstudianteModel)
            .options(selectinload(EstudianteModel.usuario))
            .where(EstudianteModel.id_estudiante == id_estudiante)
        )
        return result.scalar_one_or_none()

    async def get_with_filters(
        self,
        id_estudiante: int | None = None,
        id_materia: int | None = None,
        id_periodo: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotaModel]:
        query = select(NotaModel).options(
            selectinload(NotaModel.materia),
            selectinload(NotaModel.estudiante),
        )
        if id_estudiante:
            query = query.where(NotaModel.id_estudiante == id_estudiante)
        if id_materia:
            query = query.where(NotaModel.id_materia == id_materia)
        if id_periodo:
            query = query.where(NotaModel.id_periodo == id_periodo)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_promedio_estudiante(self, id_estudiante: int) -> float | None:
        result = await self.session.execute(
            select(func.avg(NotaModel.nota)).where(NotaModel.id_estudiante == id_estudiante)
        )
        return result.scalar_one_or_none()

    async def exists(self, id_estudiante: int, id_materia: int, id_periodo: int) -> bool:
        result = await self.session.execute(
            select(NotaModel.id_nota).where(
                NotaModel.id_estudiante == id_estudiante,
                NotaModel.id_materia == id_materia,
                NotaModel.id_periodo == id_periodo,
            )
        )
        return result.scalar_one_or_none() is not None
