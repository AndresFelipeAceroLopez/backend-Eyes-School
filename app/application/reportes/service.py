from __future__ import annotations

import mimetypes
import os
import uuid
from dataclasses import dataclass
from datetime import date

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.reportes.schemas import ReporteCreate, ReporteEstadoUpdate, ReporteOut
from app.core.exceptions import ConflictException, NotFoundException
from app.infrastructure.repositories.reportes_repository import (
    ReporteArchivoRepository,
    ReporteRepository,
)

# Prefijo de las rutas que devuelve la subida (y carpeta de los archivos anteriores a N-23).
UPLOAD_DIR = "static/reportes"
ALLOWED_EXT = {"pdf", "xlsx", "xls", "doc", "docx"}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


@dataclass
class ArchivoDeReporte:
    """Lo que descarga `GET /reportes/{id}/archivo`: el contenido o, si es anterior a N-23, la
    ruta en disco donde quedó (solo existe si no hubo un despliegue desde que se subió)."""

    nombre: str
    tipo: str
    contenido: bytes | None = None
    ruta_en_disco: str | None = None


class ReporteService:
    def __init__(self, session: AsyncSession):
        self.repo = ReporteRepository(session)
        self.archivos = ReporteArchivoRepository(session)

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
        """Elimina el reporte y su archivo (de la base y, si quedó alguno, del disco)."""
        item = await self.repo.get_by_id(id_reporte)
        if not item:
            raise NotFoundException("Reporte no encontrado")
        if item.archivo_generado:
            await self.archivos.eliminar(item.archivo_generado)
            rel_path = item.archivo_generado.lstrip("/")
            if os.path.isfile(rel_path):
                try:
                    os.remove(rel_path)
                except OSError:
                    pass  # el registro se borra igual aunque el archivo ya no exista
        await self.repo.delete(item)

    async def upload_archivo(self, file: UploadFile) -> str:
        """Guarda el archivo en la base y devuelve su ruta (`/static/reportes/<uuid>.<ext>`).

        N-23: antes se escribía en el disco del App Service y se perdía en cada despliegue. La
        ruta que se devuelve es la misma de antes, así la web no cambia: ahora es la clave con la
        que se busca el contenido en `reporte_archivos`.
        """
        ext = (file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "").lower()
        if ext not in ALLOWED_EXT:
            raise ConflictException("Formato de archivo no permitido")

        content = await file.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ConflictException("El archivo excede el tamaño máximo de 10 MB")

        ruta = f"/{UPLOAD_DIR}/{uuid.uuid4()}.{ext}"
        tipo = mimetypes.guess_type(ruta)[0] or "application/octet-stream"
        await self.archivos.guardar(ruta, content, tipo)
        return ruta

    async def get_archivo(self, id_reporte: int) -> ArchivoDeReporte:
        """El archivo de un reporte, para descargarlo con su nombre."""
        item = await self.repo.get_by_id(id_reporte)
        if not item:
            raise NotFoundException("Reporte no encontrado")
        if not item.archivo_generado:
            raise NotFoundException("El reporte no tiene archivo adjunto")

        ext = item.archivo_generado.rsplit(".", 1)[-1] if "." in item.archivo_generado else "pdf"
        safe = "".join(c for c in item.nombre_reporte if c.isalnum() or c in " -_").strip()
        nombre = f"{safe or 'reporte'}.{ext}"

        guardado = await self.archivos.obtener(item.archivo_generado)
        if guardado:
            return ArchivoDeReporte(nombre=nombre, tipo=guardado.tipo, contenido=guardado.contenido)

        # Archivos subidos antes de N-23: solo existen si no hubo un despliegue desde entonces.
        rel_path = item.archivo_generado.lstrip("/")
        if os.path.isfile(rel_path):
            tipo = mimetypes.guess_type(nombre)[0] or "application/octet-stream"
            return ArchivoDeReporte(nombre=nombre, tipo=tipo, ruta_en_disco=rel_path)
        raise NotFoundException("Archivo no encontrado en el servidor")
