from datetime import datetime

from sqlalchemy import delete, exists, func, literal_column, or_, select, update
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
            .where(func.lower(UsuarioModel.correo) == correo.strip().lower())
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
        query = select(UsuarioModel.id_usuario).where(
            func.lower(UsuarioModel.correo) == correo.strip().lower()
        )
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

    async def registrar_fallo(self, id_usuario: int) -> int:
        """Suma un intento de inicio de sesión fallido y devuelve el total acumulado."""
        result = await self.session.execute(
            update(UsuarioModel)
            .where(UsuarioModel.id_usuario == id_usuario)
            .values(intentos_fallidos=UsuarioModel.intentos_fallidos + 1)
            .returning(UsuarioModel.intentos_fallidos)
            .execution_options(synchronize_session=False)
        )
        return result.scalar_one()

    async def bloquear(self, id_usuario: int, hasta: datetime) -> None:
        """Bloquea el inicio de sesión hasta `hasta` y reinicia el contador."""
        await self.session.execute(
            update(UsuarioModel)
            .where(UsuarioModel.id_usuario == id_usuario)
            .values(bloqueado_hasta=hasta, intentos_fallidos=0)
            .execution_options(synchronize_session=False)
        )

    async def reiniciar_fallos(self, id_usuario: int) -> None:
        await self.session.execute(
            update(UsuarioModel)
            .where(UsuarioModel.id_usuario == id_usuario)
            .values(intentos_fallidos=0, bloqueado_hasta=None)
            .execution_options(synchronize_session=False)
        )

    async def delete_cascade(self, id_usuario: int) -> None:
        """Elimina el usuario y TODO lo que lo referencia por FK, en UNA sola sentencia.

        Antes eran ~20 DELETE seguidos; con la base a 160–300 ms por viaje, `DELETE /usuarios/{id}`
        tardaba 7 s en QA (CP-INT-025). Ahora cada tabla es un CTE que modifica datos y el usuario
        es el DELETE final: PostgreSQL ejecuta todo en un viaje. Las FK del esquema son NO ACTION
        (ninguna RESTRICT), y esas se comprueban al TERMINAR la sentencia, cuando ya no queda nada
        que apunte al usuario; por eso el orden interno da igual. Las sesiones y los dispositivos
        caen solos (ON DELETE CASCADE).
        """
        prof = select(ProfesorModel.id_profesor).where(ProfesorModel.id_usuario == id_usuario)
        est = select(EstudianteModel.id_estudiante).where(EstudianteModel.id_usuario == id_usuario)
        adm = select(AdministradorModel.id_administrador).where(
            AdministradorModel.id_usuario == id_usuario
        )
        borrados = [
            # Registros que creó el usuario o que son de su estudiante (una sola pasada por tabla)
            delete(AsistenciaModel).where(or_(
                AsistenciaModel.registrado_por == id_usuario, AsistenciaModel.id_estudiante.in_(est)
            )),
            delete(AsistenciaAulaModel).where(or_(
                AsistenciaAulaModel.registrado_por == id_usuario,
                AsistenciaAulaModel.id_estudiante.in_(est),
            )),
            delete(NotaModel).where(or_(
                NotaModel.registrado_por == id_usuario, NotaModel.id_estudiante.in_(est)
            )),
            delete(NovedadModel).where(or_(
                NovedadModel.registrado_por == id_usuario, NovedadModel.id_estudiante.in_(est)
            )),
            # Profesor
            delete(ProfesorEspecializacionModel).where(
                ProfesorEspecializacionModel.id_profesor.in_(prof)
            ),
            delete(ProfesorHorarioModel).where(ProfesorHorarioModel.id_profesor.in_(prof)),
            delete(AsignacionModel).where(AsignacionModel.id_profesor.in_(prof)),
            delete(ProfesorModel).where(ProfesorModel.id_usuario == id_usuario),
            # Estudiante
            delete(EstudianteIPSModel).where(EstudianteIPSModel.id_estudiante.in_(est)),
            delete(EstudianteModel).where(EstudianteModel.id_usuario == id_usuario),
            # Padre: como acudiente del estudiante o cuando el usuario ES el acudiente
            delete(PadreModel).where(or_(
                PadreModel.id_estudiante.in_(est), PadreModel.id_usuario == id_usuario
            )),
            # Administrador
            delete(ReporteModel).where(ReporteModel.id_administrador.in_(adm)),
            delete(AdministradorModel).where(AdministradorModel.id_usuario == id_usuario),
        ]
        ctes = [
            sentencia.returning(literal_column("1")).cte(f"borrado_{i}")
            for i, sentencia in enumerate(borrados)
        ]
        await self.session.execute(
            delete(UsuarioModel).where(UsuarioModel.id_usuario == id_usuario).add_cte(*ctes)
            .execution_options(synchronize_session=False)
        )
        await self.session.flush()

    async def duplicados(self, correo: str | None, numero: str, tipo: str) -> tuple[bool, bool]:
        """(¿correo ya usado?, ¿documento ya usado?) en una sola consulta (antes eran dos)."""
        correo_usado = (
            exists().where(func.lower(UsuarioModel.correo) == correo.strip().lower())
            if correo else literal_column("false")
        )
        documento_usado = exists().where(
            UsuarioModel.numero_documento == numero, UsuarioModel.tipo_documento == tipo
        )
        fila = (await self.session.execute(select(correo_usado, documento_usado))).one()
        return bool(fila[0]), bool(fila[1])

    async def crear_con_rol(self, data: dict) -> UsuarioModel:
        """Inserta y carga el rol: 2 consultas (antes, insert + refresh + relectura con rol = 3).

        Los valores por defecto del servidor (`fechaRegistro`) llegan con el RETURNING del INSERT.
        """
        usuario = UsuarioModel(**data)
        self.session.add(usuario)
        await self.session.flush()
        await self.session.refresh(usuario, attribute_names=["rol"])
        return usuario


class RolRepository(BaseRepository[RolModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(RolModel, session)
