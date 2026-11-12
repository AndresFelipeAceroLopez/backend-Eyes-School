from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dashboard.schemas import (
    AdminDashboard,
    DocenteDashboard,
    EstudianteDashboard,
    PadreDashboard,
)
from app.core.exceptions import ForbiddenException, NotFoundException
from app.infrastructure.models.academico import AsignacionModel, CursoModel
from app.infrastructure.models.actores import EstudianteModel, ProfesorModel
from app.infrastructure.models.asistencia import AsistenciaModel
from app.infrastructure.models.notas import NotaModel
from app.infrastructure.models.novedades import NovedadModel
from app.infrastructure.repositories.actores_repository import (
    EstudianteRepository,
    PadreRepository,
)


class DashboardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def resolver_estudiante(self, current_user, id_estudiante: int | None = None) -> int:
        """¿De qué estudiante son los datos que pide este usuario?

        - estudiante: el suyo.
        - padre: `id_estudiante` si es uno de sus hijos (si no, 403); sin indicarlo, el primero.
        """
        if current_user.nombre_rol == "padre":
            repo = PadreRepository(self.session)
            if id_estudiante is not None:
                if id_estudiante not in await repo.ids_estudiantes(current_user.id_usuario):
                    raise ForbiddenException(
                        "Solo puede consultar la información del estudiante asociado"
                    )
                return id_estudiante
            padre = await repo.get_by_usuario(current_user.id_usuario)
            if not padre:
                raise NotFoundException("Perfil padre no encontrado")
            return padre.id_estudiante
        est = await EstudianteRepository(self.session).get_by_usuario(current_user.id_usuario)
        if not est:
            raise NotFoundException("Perfil estudiante no encontrado")
        return est.id_estudiante

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

    async def get_docente_dashboard(self, id_profesor: int, id_usuario: int) -> DocenteDashboard:
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
        # registrado_por es el id_usuario del que registró (FK a usuario), NO el
        # id_profesor: comparar contra id_profesor daba siempre 0.
        notas_hoy = (await self.session.execute(
            select(func.count()).select_from(NotaModel)
            .where(
                NotaModel.registrado_por == id_usuario,
                func.date(NotaModel.fecha_registro) == today,
            )
        )).scalar_one()

        asistencias_hoy = (await self.session.execute(
            select(func.count()).select_from(AsistenciaModel)
            .where(
                AsistenciaModel.registrado_por == id_usuario,
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

    async def get_padre_dashboard(
        self, id_usuario: int, id_estudiante: int | None = None
    ) -> PadreDashboard:
        from app.core.dependencies import CurrentUser
        from app.infrastructure.models.usuario import UsuarioModel

        id_estudiante = await self.resolver_estudiante(
            CurrentUser(id_usuario, 4, "padre"), id_estudiante
        )
        estudiante = await self.session.get(EstudianteModel, id_estudiante)
        usuario = await self.session.get(UsuarioModel, estudiante.id_usuario)

        promedio = (await self.session.execute(
            select(func.avg(NotaModel.nota)).where(NotaModel.id_estudiante == id_estudiante)
        )).scalar_one()

        asistencia_pct = await self._get_porcentaje_asistencia(id_estudiante)

        novedades = (await self.session.execute(
            select(func.count()).select_from(NovedadModel)
            .where(NovedadModel.id_estudiante == id_estudiante, NovedadModel.estado == "Pendiente")
        )).scalar_one()

        return PadreDashboard(
            id_estudiante=id_estudiante,
            nombre_estudiante=f"{usuario.primer_nombre} {usuario.primer_apellido}",
            promedio_general=round(float(promedio), 2) if promedio else None,
            porcentaje_asistencia=asistencia_pct,
            novedades_pendientes=novedades,
        )

    async def _get_porcentaje_asistencia(self, id_estudiante: int) -> float | None:
        return await self._porcentaje_asistencia_de(
            AsistenciaModel.id_estudiante == id_estudiante
        )

    async def _get_porcentaje_asistencia_global(self) -> float | None:
        return await self._porcentaje_asistencia_de()

    async def _porcentaje_asistencia_de(self, *condiciones) -> float | None:
        """Una sola consulta sobre los registros activos (N-04): antes el total contaba solo
        los activos y los «Presente» contaban también los borrados (borrado lógico), así que
        el porcentaje podía pasar de 100."""
        filas = (await self.session.execute(
            select(AsistenciaModel.estado, func.count())
            .where(AsistenciaModel.activo == True, *condiciones)  # noqa: E712
            .group_by(AsistenciaModel.estado)
        )).all()
        return porcentaje_asistencia({estado: cantidad for estado, cantidad in filas})


# Estados que cuentan como asistencia: una llegada tarde es asistencia (mismo criterio que la
# app móvil y el panel web, N-20).
ESTADOS_QUE_ASISTEN = frozenset({"Presente", "Tarde"})


def porcentaje_asistencia(conteos: dict[str, int]) -> float | None:
    """Porcentaje de asistencia a partir de los registros activos agrupados por estado.

    Devuelve `None` sin registros. Nunca pasa de 100: numerador y denominador salen del
    mismo conjunto.
    """
    total = sum(conteos.values())
    if not total:
        return None
    asistio = sum(c for estado, c in conteos.items() if estado in ESTADOS_QUE_ASISTEN)
    return round(asistio / total * 100, 2)
