from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.reportes.schemas import ReporteCreate, ReporteEstadoUpdate, ReporteOut
from app.core.exceptions import NotFoundException
from app.infrastructure.repositories.reportes_repository import ReporteRepository


class ReporteService:
    def __init__(self, session: AsyncSession):
        self.repo = ReporteRepository(session)

    async def list(self, id_administrador: int | None = None, skip: int = 0, limit: int = 100) -> list[ReporteOut]:
        if id_administrador:
            items = await self.repo.get_by_administrador(id_administrador, skip=skip, limit=limit)
        else:
            items = await self.repo.get_all(skip=skip, limit=limit)
        return [ReporteOut.model_validate(r) for r in items]

    async def get(self, id_reporte: int) -> ReporteOut:
        item = await self.repo.get_by_id(id_reporte)
        if not item:
            raise NotFoundException("Reporte no encontrado")
        return ReporteOut.model_validate(item)

    async def create(self, data: ReporteCreate) -> ReporteOut:
        payload = data.model_dump()
        payload["fecha_generacion"] = date.today()
        payload["estado"] = "Pendiente"
        item = await self.repo.create(payload)
        return ReporteOut.model_validate(item)

    async def update_estado(self, id_reporte: int, data: ReporteEstadoUpdate) -> ReporteOut:
        item = await self.repo.get_by_id(id_reporte)
        if not item:
            raise NotFoundException("Reporte no encontrado")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return ReporteOut.model_validate(updated)
