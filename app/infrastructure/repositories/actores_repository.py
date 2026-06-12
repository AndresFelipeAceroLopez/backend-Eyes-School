from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.actores import AdministradorModel, EstudianteModel, PadreModel, ProfesorModel
from app.infrastructure.repositories.base_repository import BaseRepository


class AdministradorRepository(BaseRepository[AdministradorModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(AdministradorModel, session)

    async def get_by_usuario(self, id_usuario: int) -> AdministradorModel | None:
        result = await self.session.execute(
            select(AdministradorModel).where(AdministradorModel.id_usuario == id_usuario)
        )
        return result.scalar_one_or_none()

    async def get_all_with_usuario(self, skip: int = 0, limit: int = 100) -> list[AdministradorModel]:
        result = await self.session.execute(
            select(AdministradorModel)
            .options(selectinload(AdministradorModel.usuario))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class ProfesorRepository(BaseRepository[ProfesorModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(ProfesorModel, session)

    async def get_by_usuario(self, id_usuario: int) -> ProfesorModel | None:
        result = await self.session.execute(
            select(ProfesorModel).where(ProfesorModel.id_usuario == id_usuario)
        )
        return result.scalar_one_or_none()

    async def get_all_with_usuario(self, skip: int = 0, limit: int = 100, estado: str | None = None) -> list[ProfesorModel]:
        query = select(ProfesorModel).options(selectinload(ProfesorModel.usuario))
        if estado:
            query = query.where(ProfesorModel.estado == estado)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_by_id_with_details(self, id_profesor: int) -> ProfesorModel | None:
        result = await self.session.execute(
            select(ProfesorModel)
            .options(
                selectinload(ProfesorModel.usuario),
                selectinload(ProfesorModel.especializaciones).selectinload("especializacion"),
                selectinload(ProfesorModel.asignaciones),
            )
            .where(ProfesorModel.id_profesor == id_profesor)
        )
        return result.scalar_one_or_none()

    async def codigo_exists(self, codigo: str, exclude_id: int | None = None) -> bool:
        query = select(ProfesorModel.id_profesor).where(ProfesorModel.codigo_profesor == codigo)
        if exclude_id:
            query = query.where(ProfesorModel.id_profesor != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None


class EstudianteRepository(BaseRepository[EstudianteModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(EstudianteModel, session)

    async def get_by_usuario(self, id_usuario: int) -> EstudianteModel | None:
        result = await self.session.execute(
            select(EstudianteModel).where(EstudianteModel.id_usuario == id_usuario)
        )
        return result.scalar_one_or_none()

    async def get_all_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        id_curso: int | None = None,
        estado: str | None = None,
    ) -> list[EstudianteModel]:
        query = select(EstudianteModel).options(
            selectinload(EstudianteModel.usuario),
            selectinload(EstudianteModel.curso_actual),
        )
        if id_curso is not None:
            query = query.where(EstudianteModel.id_curso_actual == id_curso)
        if estado:
            query = query.where(EstudianteModel.estado == estado)
        result = await self.session.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def codigo_exists(self, codigo: str, exclude_id: int | None = None) -> bool:
        query = select(EstudianteModel.id_estudiante).where(EstudianteModel.codigo_estudiante == codigo)
        if exclude_id:
            query = query.where(EstudianteModel.id_estudiante != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None


class PadreRepository(BaseRepository[PadreModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(PadreModel, session)

    async def get_by_usuario(self, id_usuario: int) -> PadreModel | None:
        result = await self.session.execute(
            select(PadreModel).where(PadreModel.id_usuario == id_usuario)
        )
        return result.scalar_one_or_none()

    async def get_by_estudiante(self, id_estudiante: int) -> list[PadreModel]:
        result = await self.session.execute(
            select(PadreModel)
            .options(selectinload(PadreModel.usuario))
            .where(PadreModel.id_estudiante == id_estudiante)
        )
        return list(result.scalars().all())
