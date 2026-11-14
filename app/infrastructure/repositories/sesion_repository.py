from datetime import datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.reloj import ahora_utc
from app.infrastructure.models.sesiones import SesionRefrescoModel
from app.infrastructure.repositories.base_repository import BaseRepository


class SesionRepository(BaseRepository[SesionRefrescoModel]):
    """Sesiones de refresco guardadas en PostgreSQL para poder revocarlas."""

    def __init__(self, session: AsyncSession):
        super().__init__(SesionRefrescoModel, session)

    async def crear(self, jti: str, id_usuario: int, expira: datetime) -> SesionRefrescoModel:
        return await self.create({"jti": jti, "id_usuario": id_usuario, "expira": expira})

    async def obtener_activa(self, jti: str) -> SesionRefrescoModel | None:
        """La sesión solo si no está revocada ni vencida."""
        result = await self.session.execute(
            select(SesionRefrescoModel).where(
                SesionRefrescoModel.jti == jti,
                SesionRefrescoModel.revocado == False,  # noqa: E712
                SesionRefrescoModel.expira > ahora_utc(),
            )
        )
        return result.scalar_one_or_none()

    async def revocar(self, jti: str) -> None:
        await self.session.execute(
            update(SesionRefrescoModel).where(SesionRefrescoModel.jti == jti).values(revocado=True)
        )
        await self.session.flush()

    async def revocar_todas(self, id_usuario: int) -> None:
        await self.session.execute(
            update(SesionRefrescoModel)
            .where(SesionRefrescoModel.id_usuario == id_usuario)
            .values(revocado=True)
        )
        await self.session.flush()

    async def limpiar_vencidas(self, dias: int = 30) -> None:
        """Borra las sesiones vencidas hace más de `dias` días."""
        limite = ahora_utc() - timedelta(days=dias)
        await self.session.execute(
            delete(SesionRefrescoModel).where(SesionRefrescoModel.expira < limite)
        )
