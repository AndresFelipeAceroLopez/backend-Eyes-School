from fastapi import APIRouter, Query, Response

from app.application.common.authz import assert_acceso_estudiante
from app.application.notas.schemas import NotaCreate, NotaOut, NotaUpdate
from app.application.notas.service import NotaService
from app.core.dependencies import AuthUser, DbSession, require_roles

router = APIRouter(prefix="/notas", tags=["Notas"])


# Listado global = vista de gestión (docente/admin). Estudiantes y padres NO lo
# consumen: leen las notas del estudiante asociado vía /estudiantes/{id}/notas.
# El docente solo ve las notas de los cursos que dicta.
@router.get("", response_model=list[NotaOut], dependencies=[require_roles("admin", "docente")])
async def list_notas(
    db: DbSession,
    current_user: AuthUser,
    id_estudiante: int | None = None,
    id_materia: int | None = None,
    id_periodo: int | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await NotaService(db).list(
        id_estudiante=id_estudiante, id_materia=id_materia, id_periodo=id_periodo,
        skip=skip, limit=limit, actor=current_user,
    )


@router.post("", response_model=NotaOut, status_code=201, dependencies=[require_roles("docente")])
async def create_nota(data: NotaCreate, db: DbSession, current_user: AuthUser):
    return await NotaService(db).create(data, current_user)


@router.get("/{id_nota}", response_model=NotaOut, dependencies=[require_roles("admin", "docente")])
async def get_nota(id_nota: int, db: DbSession, current_user: AuthUser):
    return await NotaService(db).get(id_nota, current_user)


@router.put("/{id_nota}", response_model=NotaOut, dependencies=[require_roles("docente")])
async def update_nota(id_nota: int, data: NotaUpdate, db: DbSession, current_user: AuthUser):
    return await NotaService(db).update(id_nota, data, current_user)


# Notas = recurso exclusivo del docente (CRUD completo). El borrado físico que
# hace el admin al eliminar un usuario va por la cascada de DELETE /usuarios/{id}.
@router.delete("/{id_nota}", status_code=204, dependencies=[require_roles("docente")])
async def delete_nota(id_nota: int, db: DbSession, current_user: AuthUser):
    await NotaService(db).delete(id_nota, current_user)


@router.get("/estudiantes/{id_estudiante}/boletin/pdf", dependencies=[require_roles("admin", "docente", "estudiante", "padre")])
async def download_boletin_pdf(id_estudiante: int, db: DbSession, current_user: AuthUser):
    await assert_acceso_estudiante(db, current_user, id_estudiante)
    contenido = await NotaService(db).generate_boletin_pdf(id_estudiante)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="boletin_{id_estudiante}.pdf"'},
    )
