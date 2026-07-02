from fastapi import APIRouter

from app.application.dashboard.schemas import DocenteDashboard, EstudianteDashboard, PadreDashboard
from app.application.dashboard.service import DashboardService
from app.core.dependencies import AuthUser, DbSession, require_roles

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/docente", response_model=DocenteDashboard, dependencies=[require_roles("docente")])
async def docente_dashboard(current_user: AuthUser, db: DbSession):
    from app.infrastructure.repositories.actores_repository import ProfesorRepository
    profesor = await ProfesorRepository(db).get_by_usuario(current_user.id_usuario)
    if not profesor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Perfil docente no encontrado")
    # id_profesor = cursos/estudiantes (vía asignaciones); id_usuario = notas y
    # asistencias registradas (registrado_por es FK a usuario, NO a profesor).
    return await DashboardService(db).get_docente_dashboard(profesor.id_profesor, current_user.id_usuario)


@router.get("/estudiante", response_model=EstudianteDashboard, dependencies=[require_roles("estudiante", "padre")])
async def estudiante_dashboard(current_user: AuthUser, db: DbSession):
    if "padre" in current_user.roles:
        from app.infrastructure.models.actores import PadreModel
        from sqlalchemy import select
        padre = await db.execute(select(PadreModel).where(PadreModel.id_usuario == current_user.id_usuario))
        padre = padre.scalar_one_or_none()
        if not padre:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Perfil padre no encontrado")
        id_estudiante = padre.id_estudiante
    else:
        from app.infrastructure.repositories.actores_repository import EstudianteRepository
        est = await EstudianteRepository(db).get_by_usuario(current_user.id_usuario)
        if not est:
            from app.core.exceptions import NotFoundException
            raise NotFoundException("Perfil estudiante no encontrado")
        id_estudiante = est.id_estudiante
    return await DashboardService(db).get_estudiante_dashboard(id_estudiante)


@router.get("/padre", response_model=PadreDashboard, dependencies=[require_roles("padre")])
async def padre_dashboard(current_user: AuthUser, db: DbSession):
    return await DashboardService(db).get_padre_dashboard(current_user.id_usuario)
