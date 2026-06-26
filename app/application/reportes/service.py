from __future__ import annotations

import os
import uuid
from datetime import date

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.reportes.schemas import ReporteCreate, ReporteEstadoUpdate, ReporteOut
from app.core.exceptions import ConflictException, NotFoundException
from app.infrastructure.repositories.reportes_repository import ReporteRepository

# Carpeta (servida en /static) y formatos/tamaño permitidos para los archivos de reporte.
UPLOAD_DIR = "static/reportes"
ALLOWED_EXT = {"pdf", "xlsx", "xls", "doc", "docx"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


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

    async def delete(self, id_reporte: int) -> None:
        """Elimina el reporte y, si lo tiene, su archivo físico en disco."""
        item = await self.repo.get_by_id(id_reporte)
        if not item:
            raise NotFoundException("Reporte no encontrado")
        if item.archivo_generado:
            rel_path = item.archivo_generado.lstrip("/")  # "static/reportes/<uuid>.<ext>"
            if os.path.isfile(rel_path):
                try:
                    os.remove(rel_path)
                except OSError:
                    pass  # el registro se borra igual aunque el archivo ya no exista
        await self.repo.delete(item)

    async def upload_archivo(self, file: UploadFile) -> str:
        """Guarda el archivo en static/reportes y devuelve su ruta relativa (cabe en varchar)."""
        ext = (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "").lower()
        if ext not in ALLOWED_EXT:
            raise ConflictException("Formato de archivo no permitido")

        content = await file.read()
        if len(content) > MAX_BYTES:
            raise ConflictException("El archivo excede el tamaño máximo de 10 MB")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid.uuid4()}.{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            f.write(content)
        return f"/static/reportes/{filename}"

    async def get_archivo_path(self, id_reporte: int) -> tuple[str, str]:
        """Devuelve (ruta_en_disco, nombre_de_descarga) del archivo de un reporte."""
        item = await self.repo.get_by_id(id_reporte)
        if not item:
            raise NotFoundException("Reporte no encontrado")
        if not item.archivo_generado:
            raise NotFoundException("El reporte no tiene archivo adjunto")

        rel_path = item.archivo_generado.lstrip("/")  # "static/reportes/<uuid>.<ext>"
        if not os.path.isfile(rel_path):
            raise NotFoundException("Archivo no encontrado en el servidor")

        ext = rel_path.rsplit(".", 1)[-1]
        safe = "".join(c for c in item.nombre_reporte if c.isalnum() or c in " -_").strip()
        return rel_path, f"{safe or 'reporte'}.{ext}"
