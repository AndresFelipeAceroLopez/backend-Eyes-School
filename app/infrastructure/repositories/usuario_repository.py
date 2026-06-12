from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.usuario import RolModel, UsuarioModel
from app.infrastructure.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository[UsuarioModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(UsuarioModel, session)

    async def get_by_correo(self, correo: str) -> UsuarioModel | None:
        result = await self.session.execute(
            select(UsuarioModel)
            .options(selectinload(UsuarioModel.rol))
            .where(UsuarioModel.correo == correo)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_rol(self, id_usuario: int) -> UsuarioModel | None:
        result = await self.session.execute(
            select(UsuarioModel)
            .options(selectinload(UsuarioModel.rol))
            .where(UsuarioModel.id_usuario == id_usuario)
        )
        return result.scalar_one_or_none()

    async def get_all_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        id_rol: int | None = None,
        estado: bool | None = None,
        search: str | None = None,
    ) -> list[UsuarioModel]:
        query = select(UsuarioModel).options(selectinload(UsuarioModel.rol))
        if id_rol is not None:
            query = query.where(UsuarioModel.id_rol == id_rol)
        if estado is not None:
            query = query.where(UsuarioModel.estado == estado)
        if search:
            query = query.where(
                UsuarioModel.primer_nombre.ilike(f"%{search}%")
                | UsuarioModel.primer_apellido.ilike(f"%{search}%")
                | UsuarioModel.numero_documento.ilike(f"%{search}%")
            )
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def correo_exists(self, correo: str, exclude_id: int | None = None) -> bool:
        query = select(UsuarioModel.id_usuario).where(UsuarioModel.correo == correo)
        if exclude_id:
            query = query.where(UsuarioModel.id_usuario != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def documento_exists(self, numero_documento: str, tipo_documento: str, exclude_id: int | None = None) -> bool:
        query = select(UsuarioModel.id_usuario).where(
            UsuarioModel.numero_documento == numero_documento,
            UsuarioModel.tipo_documento == tipo_documento,
        )
        if exclude_id:
            query = query.where(UsuarioModel.id_usuario != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None


class RolRepository(BaseRepository[RolModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(RolModel, session)
