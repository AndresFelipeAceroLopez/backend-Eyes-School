import mimetypes

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import FileResponse

from app.application.common.tipos import ENTERO32_MAX, Entero32
from app.application.reportes.schemas import ReporteCreate, ReporteEstadoUpdate, ReporteOut
from app.application.reportes.service import ReporteService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("", response_model=list[ReporteOut], dependencies=[require_roles("admin")])
async def list_reportes(
    db: DbSession,
    id_administrador: Entero32 | None = None,
    skip: int = Query(0, ge=0, le=ENTERO32_MAX),
    limit: int = Query(100, ge=1, le=500),
):
    return await ReporteService(db).list(id_administrador=id_administrador, skip=skip, limit=limit)


@router.post("", response_model=ReporteOut, status_code=201, dependencies=[require_roles("admin")])
async def create_reporte(data: ReporteCreate, db: DbSession):
    return await ReporteService(db).create(data)


@router.post("/archivo", response_model=str, dependencies=[require_roles("admin")])
async def upload_archivo(db: DbSession, file: UploadFile = File(...)):
    """Sube el archivo de un reporte y devuelve su ruta (/static/reportes/...)."""
    return await ReporteService(db).upload_archivo(file)


@router.get("/{id_reporte}", response_model=ReporteOut, dependencies=[require_roles("admin")])
async def get_reporte(id_reporte: Entero32, db: DbSession):
    return await ReporteService(db).get(id_reporte)


_TIPOS_DE_ARCHIVO = {
    "application/pdf": {},
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {},
    "application/vnd.ms-excel": {},
    "application/msword": {},
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {},
    "application/octet-stream": {},
}


@router.get(
    "/{id_reporte}/archivo",
    dependencies=[require_roles("admin")],
    response_class=FileResponse,
    responses={200: {"description": "Archivo del reporte", "content": _TIPOS_DE_ARCHIVO}},
)
async def download_archivo(id_reporte: Entero32, db: DbSession):
    """Descarga el archivo del reporte forzando el nombre (Content-Disposition: attachment)."""
    path, filename = await ReporteService(db).get_archivo_path(id_reporte)
    media_type, _ = mimetypes.guess_type(filename)
    return FileResponse(path, media_type=media_type or "application/octet-stream", filename=filename)


@router.patch("/{id_reporte}/estado", response_model=ReporteOut, dependencies=[require_roles("admin")])
async def update_estado(id_reporte: Entero32, data: ReporteEstadoUpdate, db: DbSession):
    return await ReporteService(db).update_estado(id_reporte, data)


@router.delete("/{id_reporte}", status_code=204, dependencies=[require_roles("admin")])
async def delete_reporte(id_reporte: Entero32, db: DbSession):
    await ReporteService(db).delete(id_reporte)
