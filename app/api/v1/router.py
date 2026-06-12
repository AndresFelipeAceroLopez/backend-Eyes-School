from fastapi import APIRouter

from app.api.v1 import (
    administradores,
    asignaciones,
    asistencia,
    auth,
    cursos,
    dashboard,
    especializaciones,
    estudiantes,
    horarios,
    materias,
    notas,
    novedades,
    padres,
    profesores,
    reportes,
    roles,
    usuarios,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(usuarios.router)
api_router.include_router(roles.router)
api_router.include_router(administradores.router)
api_router.include_router(profesores.router)
api_router.include_router(estudiantes.router)
api_router.include_router(padres.router)
api_router.include_router(cursos.router)
api_router.include_router(materias.router)
api_router.include_router(especializaciones.router)
api_router.include_router(asignaciones.router)
api_router.include_router(horarios.router)
api_router.include_router(asistencia.router)
api_router.include_router(notas.router)
api_router.include_router(novedades.router)
api_router.include_router(reportes.router)
api_router.include_router(dashboard.router)
