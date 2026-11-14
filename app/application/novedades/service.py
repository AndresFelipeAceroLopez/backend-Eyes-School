from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.common.notificador import Notificador, NotificadorNulo
from app.application.novedades.schemas import (
    NovedadCreate,
    NovedadOut,
    NovedadUpdate,
    TipoNovedadCreate,
    TipoNovedadOut,
)
from app.core.dependencies import CurrentUser
from app.core.exceptions import ForbiddenException, NotFoundException
from app.infrastructure.repositories.actores_repository import (
    EstudianteRepository,
    PadreRepository,
)
from app.infrastructure.repositories.dispositivo_repository import DispositivoRepository
from app.infrastructure.repositories.novedades_repository import (
    NovedadRepository,
    TipoNovedadRepository,
)

logger = logging.getLogger(__name__)


class NovedadService:
    def __init__(self, session: AsyncSession, notificador: Notificador | None = None):
        self.repo = NovedadRepository(session)
        self.tipo_repo = TipoNovedadRepository(session)
        self.padre_repo = PadreRepository(session)
        self.estudiante_repo = EstudianteRepository(session)
        self.dispositivo_repo = DispositivoRepository(session)
        self.notificador = notificador or NotificadorNulo()

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

    async def create(self, data: NovedadCreate, registrado_por: int) -> NovedadOut:
        """`registrado_por` sale del token, nunca del cuerpo de la petición."""
        item = await self.repo.create({**data.model_dump(), "registrado_por": registrado_por})
        out = NovedadOut.model_validate(item)
        await self._notificar_acudientes(out)
        return out

    async def _notificar_acudientes(self, novedad: NovedadOut) -> None:
        """Avisa por push a los acudientes del estudiante. Si falla, la novedad ya está guardada."""
        try:
            padres = await self.padre_repo.get_by_estudiante(novedad.id_estudiante)
            tokens = await self.dispositivo_repo.tokens_de_usuarios(p.id_usuario for p in padres)
            if not tokens:
                return
            estudiante = await self.estudiante_repo.get_con_usuario(novedad.id_estudiante)
            usuario = estudiante.usuario if estudiante else None
            nombre = f"{usuario.primer_nombre} {usuario.primer_apellido}" if usuario else "su hijo"
            await self.notificador.enviar(
                tokens,
                f"Nueva novedad de {nombre}",
                novedad.descripcion[:140],
                {"id_novedad": str(novedad.id_novedad), "id_estudiante": str(novedad.id_estudiante)},
            )
        except Exception:  # noqa: BLE001 — el push es best-effort, no debe romper el registro
            logger.exception("No se pudo notificar la novedad %s", novedad.id_novedad)

    @staticmethod
    def _exigir_autor_o_admin(item, actor: CurrentUser) -> None:
        """Solo quien registró la novedad (o un admin) puede editarla o borrarla."""
        if actor.nombre_rol != "admin" and item.registrado_por != actor.id_usuario:
            raise ForbiddenException("Solo el autor de la novedad o un administrador puede modificarla")

    async def update(self, id_novedad: int, data: NovedadUpdate, actor: CurrentUser) -> NovedadOut:
        item = await self.repo.get_by_id(id_novedad)
        if not item:
            raise NotFoundException("Novedad no encontrada")
        self._exigir_autor_o_admin(item, actor)
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return NovedadOut.model_validate(updated)

    async def delete(self, id_novedad: int, actor: CurrentUser) -> None:
        item = await self.repo.get_by_id(id_novedad)
        if not item:
            raise NotFoundException("Novedad no encontrada")
        self._exigir_autor_o_admin(item, actor)
        await self.repo.delete(item)
