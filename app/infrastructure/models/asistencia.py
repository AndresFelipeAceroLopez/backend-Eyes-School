from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class AsistenciaModel(Base):
    __tablename__ = "Asistencia"
    __table_args__ = {"schema": "public"}

    id_asistencia: Mapped[int] = mapped_column("idAsistencia", Integer, primary_key=True, autoincrement=True)
    id_estudiante: Mapped[int] = mapped_column("idEstudiante", Integer, ForeignKey("public.estudiantes.idEstudiante"), nullable=False)
    fecha: Mapped[date] = mapped_column("fecha", Date, nullable=False)
    estado: Mapped[str] = mapped_column("estado", String(15), nullable=False)
    observacion: Mapped[str | None] = mapped_column("observacion", Text)
    registrado_por: Mapped[int] = mapped_column("registradoPor", Integer, ForeignKey("public.usuario.idUsuario"), nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column("fechaRegistro", DateTime, nullable=False, default=func.now())
    tipo: Mapped[str | None] = mapped_column("tipo", Text)
    codigo_qr: Mapped[str | None] = mapped_column("codigo_qr", Text)
    activo: Mapped[bool] = mapped_column("activo", Boolean, default=True)

    estudiante: Mapped["EstudianteModel"] = relationship(back_populates="asistencias")
    registrado_por_usuario: Mapped["UsuarioModel"] = relationship(foreign_keys=[registrado_por])


class AsistenciaAulaModel(Base):
    __tablename__ = "Asistencia_Aula"
    __table_args__ = {"schema": "public"}

    id_asistencia_aula: Mapped[int] = mapped_column("idAsistenciaAula", Integer, primary_key=True, autoincrement=True)
    id_estudiante: Mapped[int] = mapped_column("idEstudiante", Integer, ForeignKey("public.estudiantes.idEstudiante"), nullable=False)
    id_horario: Mapped[int] = mapped_column("idHorario", Integer, ForeignKey("public.Horario.idHorario"), nullable=False)
    fecha: Mapped[date] = mapped_column("fecha", Date, nullable=False)
    estado: Mapped[str] = mapped_column("estado", String(15), nullable=False)
    observacion: Mapped[str] = mapped_column("observacion", Text, nullable=False)
    registrado_por: Mapped[int] = mapped_column("registradoPor", Integer, ForeignKey("public.usuario.idUsuario"), nullable=False)
    fecha_registro: Mapped[datetime] = mapped_column("fechaRegistro", DateTime, nullable=False, default=func.now())

    estudiante: Mapped["EstudianteModel"] = relationship(back_populates="asistencias_aula")
    horario: Mapped["HorarioModel"] = relationship(back_populates="asistencias_aula")
    registrado_por_usuario: Mapped["UsuarioModel"] = relationship(foreign_keys=[registrado_por])


from app.infrastructure.models.actores import EstudianteModel  # noqa: E402
from app.infrastructure.models.academico import HorarioModel  # noqa: E402
from app.infrastructure.models.usuario import UsuarioModel  # noqa: E402
