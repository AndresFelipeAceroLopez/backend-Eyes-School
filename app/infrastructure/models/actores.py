from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class AdministradorModel(Base):
    __tablename__ = "administrador"
    __table_args__ = {"schema": "public"}

    id_administrador: Mapped[int] = mapped_column("idAdministrador", Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column("idUsuario", Integer, ForeignKey("public.usuario.idUsuario"), nullable=False)
    cargo: Mapped[str] = mapped_column("cargo", String(100), nullable=False)
    nivel_acceso: Mapped[str] = mapped_column("nivelAcceso", String(10), nullable=False, default="Bajo")
    estado: Mapped[str] = mapped_column("estado", String(10), nullable=False, default="Activo")
    fecha_asignacion: Mapped[date] = mapped_column("fechaAsignacion", Date, nullable=False)
    fecha_fin: Mapped[date | None] = mapped_column("fechaFin", Date)

    usuario: Mapped["UsuarioModel"] = relationship(back_populates="administrador")
    reportes: Mapped[list["ReporteModel"]] = relationship(back_populates="administrador")


class ProfesorModel(Base):
    __tablename__ = "profesores"
    __table_args__ = {"schema": "public"}

    id_profesor: Mapped[int] = mapped_column("idProfesor", Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column("idUsuario", Integer, ForeignKey("public.usuario.idUsuario"), nullable=False)
    codigo_profesor: Mapped[str] = mapped_column("codigoProfesor", String(20), nullable=False)
    titulo: Mapped[str] = mapped_column("titulo", String(100), nullable=False)
    nivel_estudios: Mapped[str] = mapped_column("nivelEstudios", String(50), nullable=False)
    fecha_vinculacion: Mapped[date] = mapped_column("fechaVinculacion", Date, nullable=False)
    estado: Mapped[str] = mapped_column("estado", String(10), nullable=False, default="Activo")
    fecha_registro: Mapped[datetime] = mapped_column("fechaRegistro", DateTime, nullable=False, default=func.now())

    usuario: Mapped["UsuarioModel"] = relationship(back_populates="profesor")
    asignaciones: Mapped[list["AsignacionModel"]] = relationship(back_populates="profesor")
    profesores_horario: Mapped[list["ProfesorHorarioModel"]] = relationship(back_populates="profesor")
    especializaciones: Mapped[list["ProfesorEspecializacionModel"]] = relationship(back_populates="profesor")


class EstudianteModel(Base):
    __tablename__ = "estudiantes"
    __table_args__ = {"schema": "public"}

    id_estudiante: Mapped[int] = mapped_column("idEstudiante", Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column("idUsuario", Integer, ForeignKey("public.usuario.idUsuario"), nullable=False)
    codigo_estudiante: Mapped[str] = mapped_column("codigoEstudiante", String(20), nullable=False)
    fecha_ingreso: Mapped[date] = mapped_column("fechaIngreso", Date, nullable=False)
    fecha_egreso: Mapped[date | None] = mapped_column("fechaEgreso", Date)
    estado: Mapped[str] = mapped_column("estado", String(10), nullable=False, default="Activo")
    id_curso_actual: Mapped[int | None] = mapped_column("idCursoActual", Integer, ForeignKey("public.cursos.idCurso"))
    horario_id_horario: Mapped[int | None] = mapped_column("Horario_idHorario", Integer)
    fecha_registro: Mapped[datetime] = mapped_column("fechaRegistro", DateTime, nullable=False, default=func.now())

    usuario: Mapped["UsuarioModel"] = relationship(back_populates="estudiante")
    curso_actual: Mapped["CursoModel | None"] = relationship(back_populates="estudiantes")
    padres: Mapped[list["PadreModel"]] = relationship(back_populates="estudiante")
    asistencias: Mapped[list["AsistenciaModel"]] = relationship(back_populates="estudiante")
    asistencias_aula: Mapped[list["AsistenciaAulaModel"]] = relationship(back_populates="estudiante")
    notas: Mapped[list["NotaModel"]] = relationship(back_populates="estudiante")
    novedades: Mapped[list["NovedadModel"]] = relationship(back_populates="estudiante")
    ips: Mapped[list["EstudianteIPSModel"]] = relationship(back_populates="estudiante")


class PadreModel(Base):
    __tablename__ = "padres"
    __table_args__ = {"schema": "public"}

    id_padre: Mapped[int] = mapped_column("idPadre", Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column("idUsuario", Integer, ForeignKey("public.usuario.idUsuario"), nullable=False)
    id_estudiante: Mapped[int] = mapped_column("idEstudiante", Integer, ForeignKey("public.estudiantes.idEstudiante"), nullable=False)
    parentesco: Mapped[str] = mapped_column("parentesco", String(30), nullable=False)
    ocupacion: Mapped[str | None] = mapped_column("ocupacion", String(100))

    usuario: Mapped["UsuarioModel"] = relationship(back_populates="padre")
    estudiante: Mapped["EstudianteModel"] = relationship(back_populates="padres")


from app.infrastructure.models.usuario import UsuarioModel  # noqa: E402
from app.infrastructure.models.academico import (  # noqa: E402
    AsignacionModel,
    CursoModel,
    ProfesorEspecializacionModel,
    ProfesorHorarioModel,
)
from app.infrastructure.models.asistencia import AsistenciaAulaModel, AsistenciaModel  # noqa: E402
from app.infrastructure.models.notas import NotaModel  # noqa: E402
from app.infrastructure.models.novedades import NovedadModel  # noqa: E402
from app.infrastructure.models.reportes import EstudianteIPSModel, ReporteModel  # noqa: E402
