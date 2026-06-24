from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.academico import (
    AsignacionModel,
    CursoModel,
    EspecializacionModel,
    HorarioModel,
    MateriaModel,
    ProfesorEspecializacionModel,
    ProfesorHorarioModel,
)
from app.infrastructure.repositories.base_repository import BaseRepository


class CursoRepository(BaseRepository[CursoModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(CursoModel, session)

    async def get_activos(self, skip: int = 0, limit: int = 100) -> list[CursoModel]:
        result = await self.session.execute(
            select(CursoModel).where(CursoModel.activo == True).offset(skip).limit(limit)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_id_with_horarios(self, id_curso: int) -> CursoModel | None:
        result = await self.session.execute(
            select(CursoModel)
            .options(selectinload(CursoModel.horarios))
            .where(CursoModel.id_curso == id_curso)
        )
        return result.scalar_one_or_none()


class MateriaRepository(BaseRepository[MateriaModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(MateriaModel, session)

    async def get_activas(self) -> list[MateriaModel]:
        result = await self.session.execute(
            select(MateriaModel).where(MateriaModel.activa == True)  # noqa: E712
        )
        return list(result.scalars().all())


class EspecializacionRepository(BaseRepository[EspecializacionModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(EspecializacionModel, session)


class AsignacionRepository(BaseRepository[AsignacionModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(AsignacionModel, session)

    async def get_by_profesor(self, id_profesor: int) -> list[AsignacionModel]:
        result = await self.session.execute(
            select(AsignacionModel)
            .options(
                selectinload(AsignacionModel.curso),
                selectinload(AsignacionModel.materia),
            )
            .where(AsignacionModel.id_profesor == id_profesor, AsignacionModel.activo == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_with_filters(
        self,
        id_profesor: int | None = None,
        id_curso: int | None = None,
        id_materia: int | None = None,
        activo: bool | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsignacionModel]:
        query = select(AsignacionModel).options(
            selectinload(AsignacionModel.profesor),
            selectinload(AsignacionModel.curso),
            selectinload(AsignacionModel.materia),
        )
        if id_profesor is not None:
            query = query.where(AsignacionModel.id_profesor == id_profesor)
        if id_curso is not None:
            query = query.where(AsignacionModel.id_curso == id_curso)
        if id_materia is not None:
            query = query.where(AsignacionModel.id_materia == id_materia)
        if activo is not None:
            query = query.where(AsignacionModel.activo == activo)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())


class HorarioRepository(BaseRepository[HorarioModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(HorarioModel, session)

    async def get_by_curso(self, id_curso: int) -> list[HorarioModel]:
        result = await self.session.execute(
            select(HorarioModel)
            .options(selectinload(HorarioModel.materia))
            .where(HorarioModel.id_curso == id_curso, HorarioModel.activo == True)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_by_profesor(self, id_profesor: int) -> list[HorarioModel]:
        result = await self.session.execute(
            select(HorarioModel)
            .join(ProfesorHorarioModel, ProfesorHorarioModel.id_horario == HorarioModel.id_horario)
            .options(selectinload(HorarioModel.materia), selectinload(HorarioModel.curso))
            .where(ProfesorHorarioModel.id_profesor == id_profesor, ProfesorHorarioModel.activo == True)  # noqa: E712
        )
        return list(result.scalars().all())


class ProfesorEspecializacionRepository(BaseRepository[ProfesorEspecializacionModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(ProfesorEspecializacionModel, session)

    async def get_by_profesor(self, id_profesor: int) -> list[ProfesorEspecializacionModel]:
        result = await self.session.execute(
            select(ProfesorEspecializacionModel)
            .options(selectinload(ProfesorEspecializacionModel.especializacion))
            .where(ProfesorEspecializacionModel.id_profesor == id_profesor)
        )
        return list(result.scalars().all())

    async def get_one(self, id_profesor: int, id_especializacion: int) -> ProfesorEspecializacionModel | None:
        result = await self.session.execute(
            select(ProfesorEspecializacionModel)
            .options(selectinload(ProfesorEspecializacionModel.especializacion))
            .where(
                ProfesorEspecializacionModel.id_profesor == id_profesor,
                ProfesorEspecializacionModel.id_especializacion == id_especializacion,
            )
        )
        return result.scalar_one_or_none()
