from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.models.academico import (
    AsignacionModel,
    ProfesorEspecializacionModel,
    ProfesorHorarioModel,
)
from app.infrastructure.models.actores import (
    AdministradorModel,
    EstudianteModel,
    PadreModel,
    ProfesorModel,
)
from app.infrastructure.models.asistencia import AsistenciaAulaModel, AsistenciaModel
from app.infrastructure.models.notas import NotaModel
from app.infrastructure.models.novedades import NovedadModel
from app.infrastructure.models.reportes import EstudianteIPSModel, ReporteModel
from app.infrastructure.models.usuario import RolModel, UsuarioModel
from app.infrastructure.repositories.base_repository import BaseRepository


class UsuarioRepository(BaseRepository[UsuarioModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(UsuarioModel, session)

    async def get_by_correo(self, correo: str) -> UsuarioModel | None:
        result = await self.session.execute(
            select(UsuarioModel)
            .options(selectinload(UsuarioModel.rol))
            .where(UsuarioModel.correo == correo)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_rol(self, id_usuario: int) -> UsuarioModel | None:
        result = await self.session.execute(
            select(UsuarioModel)
            .options(selectinload(UsuarioModel.rol))
            .where(UsuarioModel.id_usuario == id_usuario)
        )
        return result.scalar_one_or_none()

    async def get_all_with_filters(
        self,
        skip: int = 0,
        limit: int = 100,
        id_rol: int | None = None,
        estado: bool | None = None,
        search: str | None = None,
    ) -> list[UsuarioModel]:
        query = select(UsuarioModel).options(selectinload(UsuarioModel.rol))
        if id_rol is not None:
            query = query.where(UsuarioModel.id_rol == id_rol)
        if estado is not None:
            query = query.where(UsuarioModel.estado == estado)
        if search:
            query = query.where(
                UsuarioModel.primer_nombre.ilike(f"%{search}%")
                | UsuarioModel.primer_apellido.ilike(f"%{search}%")
                | UsuarioModel.numero_documento.ilike(f"%{search}%")
            )
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def correo_exists(self, correo: str, exclude_id: int | None = None) -> bool:
        query = select(UsuarioModel.id_usuario).where(UsuarioModel.correo == correo)
        if exclude_id:
            query = query.where(UsuarioModel.id_usuario != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def documento_exists(self, numero_documento: str, tipo_documento: str, exclude_id: int | None = None) -> bool:
        query = select(UsuarioModel.id_usuario).where(
            UsuarioModel.numero_documento == numero_documento,
            UsuarioModel.tipo_documento == tipo_documento,
        )
        if exclude_id:
            query = query.where(UsuarioModel.id_usuario != exclude_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None

    async def delete_cascade(self, id_usuario: int) -> None:
        """Elimina el usuario y TODO lo que lo referencia por FK, en orden de
        dependencia y dentro de la misma transacción de la petición.

        Usa DELETEs por subconsulta (no carga objetos en la sesión) para no
        disparar lazy-loads en contexto async. El backend NO tenía cascade ni a
        nivel ORM ni de BD, por eso un `DELETE /usuarios/{id}` reventaba con 500
        cuando el usuario tenía fila de rol o registros asociados.
        """
        s = self.session

        async def run(stmt) -> None:
            # synchronize_session=False: no necesitamos sincronizar la sesión en
            # memoria (la petición termina tras el borrado) y así los DELETE por
            # subconsulta no fallan al intentar evaluarse en Python.
            await s.execute(stmt.execution_options(synchronize_session=False))

        prof_ids = select(ProfesorModel.id_profesor).where(ProfesorModel.id_usuario == id_usuario)
        est_ids = select(EstudianteModel.id_estudiante).where(EstudianteModel.id_usuario == id_usuario)
        admin_ids = select(AdministradorModel.id_administrador).where(AdministradorModel.id_usuario == id_usuario)

        # 1) Registros creados por el usuario (FK registradoPor → usuario)
        await run(delete(AsistenciaModel).where(AsistenciaModel.registrado_por == id_usuario))
        await run(delete(AsistenciaAulaModel).where(AsistenciaAulaModel.registrado_por == id_usuario))
        await run(delete(NotaModel).where(NotaModel.registrado_por == id_usuario))
        await run(delete(NovedadModel).where(NovedadModel.registrado_por == id_usuario))

        # 2) Profesor → especializaciones, horarios, asignaciones y su fila
        await run(delete(ProfesorEspecializacionModel).where(ProfesorEspecializacionModel.id_profesor.in_(prof_ids)))
        await run(delete(ProfesorHorarioModel).where(ProfesorHorarioModel.id_profesor.in_(prof_ids)))
        await run(delete(AsignacionModel).where(AsignacionModel.id_profesor.in_(prof_ids)))
        await run(delete(ProfesorModel).where(ProfesorModel.id_usuario == id_usuario))

        # 3) Estudiante → sus registros académicos, IPS, vínculos de padre y su fila
        await run(delete(AsistenciaModel).where(AsistenciaModel.id_estudiante.in_(est_ids)))
        await run(delete(AsistenciaAulaModel).where(AsistenciaAulaModel.id_estudiante.in_(est_ids)))
        await run(delete(NotaModel).where(NotaModel.id_estudiante.in_(est_ids)))
        await run(delete(NovedadModel).where(NovedadModel.id_estudiante.in_(est_ids)))
        await run(delete(EstudianteIPSModel).where(EstudianteIPSModel.id_estudiante.in_(est_ids)))
        await run(delete(PadreModel).where(PadreModel.id_estudiante.in_(est_ids)))
        await run(delete(EstudianteModel).where(EstudianteModel.id_usuario == id_usuario))

        # 4) Administrador → reportes y su fila
        await run(delete(ReporteModel).where(ReporteModel.id_administrador.in_(admin_ids)))
        await run(delete(AdministradorModel).where(AdministradorModel.id_usuario == id_usuario))

        # 5) Padre (cuando el usuario ES el acudiente)
        await run(delete(PadreModel).where(PadreModel.id_usuario == id_usuario))

        # 6) Usuario
        await run(delete(UsuarioModel).where(UsuarioModel.id_usuario == id_usuario))
        await s.flush()


class RolRepository(BaseRepository[RolModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(RolModel, session)
