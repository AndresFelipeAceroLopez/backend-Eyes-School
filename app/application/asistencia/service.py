from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.asistencia.schemas import (
    AsistenciaAulaCreate,
    AsistenciaAulaOut,
    AsistenciaCreate,
    AsistenciaOut,
    AsistenciaQRCreate,
    AsistenciaUpdate,
)
from app.core.exceptions import NotFoundException
from app.infrastructure.repositories.asistencia_repository import AsistenciaAulaRepository, AsistenciaRepository
from app.infrastructure.repositories.actores_repository import EstudianteRepository


class AsistenciaService:
    def __init__(self, session: AsyncSession):
        self.repo = AsistenciaRepository(session)
        self.aula_repo = AsistenciaAulaRepository(session)
        self.est_repo = EstudianteRepository(session)

    async def list(
        self,
        id_estudiante: int | None = None,
        fecha: date | None = None,
        tipo: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsistenciaOut]:
        items = await self.repo.get_with_filters(
            id_estudiante=id_estudiante, fecha=fecha, tipo=tipo, skip=skip, limit=limit
        )
        return [AsistenciaOut.model_validate(a) for a in items]

    async def get(self, id_asistencia: int) -> AsistenciaOut:
        item = await self.repo.get_by_id(id_asistencia)
        if not item:
            raise NotFoundException("Asistencia no encontrada")
        return AsistenciaOut.model_validate(item)

    async def create(self, data: AsistenciaCreate) -> AsistenciaOut:
        item = await self.repo.create(data.model_dump())
        return AsistenciaOut.model_validate(item)

    async def register_qr(self, data: AsistenciaQRCreate) -> AsistenciaOut:
        from sqlalchemy import select
        from app.infrastructure.models.actores import EstudianteModel
        result = await self.est_repo.session.execute(
            select(EstudianteModel).where(EstudianteModel.codigo_estudiante == data.codigo_qr)
        )
        estudiante = result.scalar_one_or_none()
        if not estudiante:
            raise NotFoundException(f"Estudiante con QR '{data.codigo_qr}' no encontrado")

        today = date.today()
        payload = {
            "id_estudiante": estudiante.id_estudiante,
            "fecha": today,
            "estado": "Presente",
            "registrado_por": data.registrado_por,
            "tipo": data.tipo,
            "codigo_qr": data.codigo_qr,
        }
        item = await self.repo.create(payload)
        return AsistenciaOut.model_validate(item)

    async def update(self, id_asistencia: int, data: AsistenciaUpdate) -> AsistenciaOut:
        item = await self.repo.get_by_id(id_asistencia)
        if not item:
            raise NotFoundException("Asistencia no encontrada")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return AsistenciaOut.model_validate(updated)

    async def list_aula(self, id_horario: int | None = None, id_estudiante: int | None = None, skip: int = 0, limit: int = 100) -> list[AsistenciaAulaOut]:
        if id_horario and id_estudiante is None:
            items = await self.aula_repo.get_by_horario_fecha(id_horario, date.today())
        elif id_estudiante:
            items = await self.aula_repo.get_by_estudiante(id_estudiante, skip=skip, limit=limit)
        else:
            items = await self.aula_repo.get_all(skip=skip, limit=limit)
        return [AsistenciaAulaOut.model_validate(a) for a in items]

    async def create_aula(self, data: AsistenciaAulaCreate) -> AsistenciaAulaOut:
        item = await self.aula_repo.create(data.model_dump())
        return AsistenciaAulaOut.model_validate(item)
