from fastapi import APIRouter, Query, Response

from app.application.usuarios.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.application.usuarios.service import UsuarioService
from app.core.dependencies import AuthUser, DbSession, require_roles
from app.core.exceptions import ForbiddenException

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# Directorio completo de usuarios = SOLO admin. El docente NO lo consume: los
# nombres de estudiante/profesor vienen embebidos en /estudiantes y /profesores.
@router.get("", response_model=list[UsuarioOut], dependencies=[require_roles("admin")])
async def list_usuarios(
    db: DbSession,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    id_rol: int | None = None,
    estado: bool | None = None,
    search: str | None = None,
):
    return await UsuarioService(db).list(skip=skip, limit=limit, id_rol=id_rol, estado=estado, search=search)


@router.post("", response_model=UsuarioOut, status_code=201, dependencies=[require_roles("admin")])
async def create_usuario(data: UsuarioCreate, db: DbSession):
    return await UsuarioService(db).create(data)


# El admin consulta cualquier usuario; los demás roles SOLO su propio perfil
# (lo usa la página de Perfil de docente/estudiante/padre).
@router.get("/{id_usuario}", response_model=UsuarioOut)
async def get_usuario(id_usuario: int, db: DbSession, current_user: AuthUser):
    if current_user.nombre_rol != "admin" and current_user.id_usuario != id_usuario:
        raise ForbiddenException()
    return await UsuarioService(db).get(id_usuario)


# El admin edita cualquier usuario; los demás roles SOLO su propio perfil. Un
# no-admin NO puede cambiar su propio rol (se ignora id_rol para evitar escalada).
@router.put("/{id_usuario}", response_model=UsuarioOut)
async def update_usuario(id_usuario: int, data: UsuarioUpdate, db: DbSession, current_user: AuthUser):
    if current_user.nombre_rol != "admin":
        if current_user.id_usuario != id_usuario:
            raise ForbiddenException()
        data.id_rol = None
    return await UsuarioService(db).update(id_usuario, data)


@router.patch("/{id_usuario}/estado", response_model=UsuarioOut, dependencies=[require_roles("admin")])
async def toggle_estado(id_usuario: int, estado: bool, db: DbSession):
    return await UsuarioService(db).toggle_estado(id_usuario, estado)


@router.delete("/{id_usuario}", status_code=204, dependencies=[require_roles("admin")])
async def delete_usuario(id_usuario: int, db: DbSession):
    await UsuarioService(db).delete(id_usuario)
