from collections.abc import Iterable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.models.dispositivos import DispositivoModel
from app.infrastructure.repositories.base_repository import BaseRepository


class DispositivoRepository(BaseRepository[DispositivoModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(DispositivoModel, session)

    async def get_by_token(self, token_fcm: str) -> DispositivoModel | None:
        result = await self.session.execute(
            select(DispositivoModel).where(DispositivoModel.token_fcm == token_fcm)
        )
        return result.scalar_one_or_none()

    async def registrar(self, id_usuario: int, token_fcm: str, plataforma: str) -> DispositivoModel:
        """Crea el dispositivo; si el token ya existe lo reasigna al usuario actual."""
        existente = await self.get_by_token(token_fcm)
        if existente is None:
            return await self.create(
                {"id_usuario": id_usuario, "token_fcm": token_fcm, "plataforma": plataforma}
            )
        return await self.update(existente, {"id_usuario": id_usuario, "plataforma": plataforma})

    async def eliminar_token(self, token_fcm: str, id_usuario: int) -> None:
        await self.session.execute(
            delete(DispositivoModel).where(
                DispositivoModel.token_fcm == token_fcm, DispositivoModel.id_usuario == id_usuario
            )
        )
        await self.session.flush()

    async def tokens_de_usuarios(self, ids_usuario: Iterable[int]) -> list[str]:
        ids = list(ids_usuario)
        if not ids:
            return []
        result = await self.session.execute(
            select(DispositivoModel.token_fcm).where(DispositivoModel.id_usuario.in_(ids))
        )
        return list(result.scalars().all())
