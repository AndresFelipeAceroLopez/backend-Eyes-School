from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.schemas import AdminDashboard, DocenteDashboard, EstudianteDashboard, PadreDashboard
from app.core.exceptions import NotFoundException
from app.infrastructure.models.actores import EstudianteModel, ProfesorModel
from app.infrastructure.models.academico import AsignacionModel, CursoModel
from app.infrastructure.models.asistencia import AsistenciaModel
from app.infrastructure.models.notas import NotaModel
from app.infrastructure.models.novedades import NovedadModel
from app.infrastructure.repositories.actores_repository import EstudianteRepository, PadreRepository


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_admin_dashboard(self) -> AdminDashboard:
        total_est = (await self.session.execute(
            select(func.count()).select_from(EstudianteModel).where(EstudianteModel.estado == "Activo")
        )).scalar_one()

        total_prof = (await self.session.execute(
            select(func.count()).select_from(ProfesorModel).where(ProfesorModel.estado == "Activo")
        )).scalar_one()

        total_cursos = (await self.session.execute(
            select(func.count()).select_from(CursoModel).where(CursoModel.activo == True)  # noqa: E712
        )).scalar_one()

        promedio = (await self.session.execute(
            select(func.avg(NotaModel.nota))
        )).scalar_one()

        total_novedades = (await self.session.execute(
            select(func.count()).select_from(NovedadModel).where(NovedadModel.estado.in_(["Pendiente", "En Proceso"]))
        )).scalar_one()

        tasa_aprobacion = None
        if promedio is not None:
            tasa_aprobacion = round((float(promedio) / 10.0) * 100, 2)

        asistencia_pct = await self._get_porcentaje_asistencia_global()

        return AdminDashboard(
            total_estudiantes=total_est,
            total_profesores=total_prof,
            total_cursos=total_cursos,
            promedio_general=round(float(promedio), 2) if promedio else None,
            tasa_aprobacion=tasa_aprobacion,
            porcentaje_asistencia=asistencia_pct,
            total_novedades_activas=total_novedades,
        )

    async def get_docente_dashboard(self, id_profesor: int) -> DocenteDashboard:
        asignaciones = (await self.session.execute(
            select(func.count(AsignacionModel.id_curso.distinct()))
            .where(AsignacionModel.id_profesor == id_profesor, AsignacionModel.activo == True)  # noqa: E712
        )).scalar_one()

        estudiantes = (await self.session.execute(
            select(func.count(EstudianteModel.id_estudiante.distinct()))
            .join(AsignacionModel, AsignacionModel.id_curso == EstudianteModel.id_curso_actual)
            .where(AsignacionModel.id_profesor == id_profesor, AsignacionModel.activo == True)  # noqa: E712
        )).scalar_one()

        today = date.today()
        notas_hoy = (await self.session.execute(
            select(func.count()).select_from(NotaModel)
            .where(
                NotaModel.registrado_por == id_profesor,
                func.date(NotaModel.fecha_registro) == today,
            )
        )).scalar_one()

        asistencias_hoy = (await self.session.execute(
            select(func.count()).select_from(AsistenciaModel)
            .where(
                AsistenciaModel.registrado_por == id_profesor,
                AsistenciaModel.fecha == today,
            )
        )).scalar_one()

        return DocenteDashboard(
            total_cursos_asignados=asignaciones,
            total_estudiantes=estudiantes,
            notas_registradas_hoy=notas_hoy,
            asistencias_registradas_hoy=asistencias_hoy,
        )

    async def get_estudiante_dashboard(self, id_estudiante: int) -> EstudianteDashboard:
        promedio = (await self.session.execute(
            select(func.avg(NotaModel.nota)).where(NotaModel.id_estudiante == id_estudiante)
        )).scalar_one()

        asistencia_pct = await self._get_porcentaje_asistencia(id_estudiante)

        novedades = (await self.session.execute(
            select(func.count()).select_from(NovedadModel)
            .where(NovedadModel.id_estudiante == id_estudiante, NovedadModel.estado == "Pendiente")
        )).scalar_one()

        return EstudianteDashboard(
            promedio_general=round(float(promedio), 2) if promedio else None,
            porcentaje_asistencia=asistencia_pct,
            novedades_pendientes=novedades,
            periodo_actual=1,
        )

    async def get_padre_dashboard(self, id_usuario: int) -> PadreDashboard:
        from app.infrastructure.models.actores import PadreModel
        from app.infrastructure.models.usuario import UsuarioModel
        padre = (await self.session.execute(
            select(PadreModel).where(PadreModel.id_usuario == id_usuario)
        )).scalar_one_or_none()
        if not padre:
            raise NotFoundException("Perfil de padre no encontrado")

        estudiante = await self.session.get(EstudianteModel, padre.id_estudiante)
        usuario = await self.session.get(UsuarioModel, estudiante.id_usuario)

        promedio = (await self.session.execute(
            select(func.avg(NotaModel.nota)).where(NotaModel.id_estudiante == padre.id_estudiante)
        )).scalar_one()

        asistencia_pct = await self._get_porcentaje_asistencia(padre.id_estudiante)

        novedades = (await self.session.execute(
            select(func.count()).select_from(NovedadModel)
            .where(NovedadModel.id_estudiante == padre.id_estudiante, NovedadModel.estado == "Pendiente")
        )).scalar_one()

        return PadreDashboard(
            id_estudiante=padre.id_estudiante,
            nombre_estudiante=f"{usuario.primer_nombre} {usuario.primer_apellido}",
            promedio_general=round(float(promedio), 2) if promedio else None,
            porcentaje_asistencia=asistencia_pct,
            novedades_pendientes=novedades,
        )

    async def _get_porcentaje_asistencia(self, id_estudiante: int) -> float | None:
        total = (await self.session.execute(
            select(func.count()).select_from(AsistenciaModel)
            .where(AsistenciaModel.id_estudiante == id_estudiante, AsistenciaModel.activo == True)  # noqa: E712
        )).scalar_one()
        if not total:
            return None
        presentes = (await self.session.execute(
            select(func.count()).select_from(AsistenciaModel)
            .where(AsistenciaModel.id_estudiante == id_estudiante, AsistenciaModel.estado == "Presente")
        )).scalar_one()
        return round((presentes / total) * 100, 2)

    async def _get_porcentaje_asistencia_global(self) -> float | None:
        total = (await self.session.execute(
            select(func.count()).select_from(AsistenciaModel).where(AsistenciaModel.activo == True)  # noqa: E712
        )).scalar_one()
        if not total:
            return None
        presentes = (await self.session.execute(
            select(func.count()).select_from(AsistenciaModel).where(AsistenciaModel.estado == "Presente")
        )).scalar_one()
        return round((presentes / total) * 100, 2)
