from fastapi import APIRouter

from app.application.usuarios.schemas import RolOut
from app.application.usuarios.service import UsuarioService
from app.core.dependencies import DbSession, require_roles

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RolOut], dependencies=[require_roles("admin")])
async def list_roles(db: DbSession):
    roles = await UsuarioService(db).list_roles()
    return [RolOut.model_validate(r) for r in roles]
