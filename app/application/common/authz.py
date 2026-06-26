from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import ForbiddenException
from app.infrastructure.repositories.actores_repository import (
    EstudianteRepository,
    PadreRepository,
)


async def assert_acceso_estudiante(
    db: AsyncSession, current_user: CurrentUser, id_estudiante: int
) -> None:
    """Autoriza el acceso a los datos de UN estudiante.

    - admin / docente: acceso completo (gestión de cualquier estudiante).
    - estudiante: solo a su propio expediente.
    - padre: solo al estudiante asociado a su cuenta.

    Cualquier otro caso (incluido un padre/estudiante pidiendo otro id) → 403.
    """
    rol = current_user.nombre_rol
    if rol in ("admin", "docente"):
        return
    if rol == "estudiante":
        est = await EstudianteRepository(db).get_by_usuario(current_user.id_usuario)
        if est is not None and est.id_estudiante == id_estudiante:
            return
    elif rol == "padre":
        padre = await PadreRepository(db).get_by_usuario(current_user.id_usuario)
        if padre is not None and padre.id_estudiante == id_estudiante:
            return
    raise ForbiddenException("Solo puede consultar la información del estudiante asociado")
