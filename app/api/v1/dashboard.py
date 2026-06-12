from fastapi import APIRouter

from app.application.dashboard.schemas import AdminDashboard, DocenteDashboard, EstudianteDashboard, PadreDashboard
from app.application.dashboard.service import DashboardService
from app.core.dependencies import AuthUser, DbSession, require_roles

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/admin", response_model=AdminDashboard, dependencies=[require_roles("admin")])
async def admin_dashboard(db: DbSession):
    return await DashboardService(db).get_admin_dashboard()


@router.get("/docente", response_model=DocenteDashboard, dependencies=[require_roles("docente")])
async def docente_dashboard(current_user: AuthUser, db: DbSession):
    from app.infrastructure.repositories.actores_repository import ProfesorRepository
    profesor = await ProfesorRepository(db).get_by_usuario(current_user.id_usuario)
    if not profesor:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Perfil docente no encontrado")
    return await DashboardService(db).get_docente_dashboard(profesor.id_profesor)


@router.get("/estudiante", response_model=EstudianteDashboard, dependencies=[require_roles("estudiante")])
async def estudiante_dashboard(current_user: AuthUser, db: DbSession):
    from app.infrastructure.repositories.actores_repository import EstudianteRepository
    est = await EstudianteRepository(db).get_by_usuario(current_user.id_usuario)
    if not est:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("Perfil estudiante no encontrado")
    return await DashboardService(db).get_estudiante_dashboard(est.id_estudiante)


@router.get("/padre", response_model=PadreDashboard, dependencies=[require_roles("padre")])
async def padre_dashboard(current_user: AuthUser, db: DbSession):
    return await DashboardService(db).get_padre_dashboard(current_user.id_usuario)
