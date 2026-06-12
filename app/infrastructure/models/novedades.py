from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class TipoNovedadModel(Base):
    __tablename__ = "tiposnovedad"
    __table_args__ = {"schema": "public"}

    id_tipo_novedad: Mapped[int] = mapped_column("idTipoNovedad", Integer, primary_key=True, autoincrement=True)
    nombre_tipo: Mapped[str] = mapped_column("nombreTipo", String(50), nullable=False)
    descripcion: Mapped[str | None] = mapped_column("descripcion", Text)
    nivel_gravedad: Mapped[str] = mapped_column("nivelGravedad", String(10), nullable=False, default="Bajo")
    requiere_accion: Mapped[bool] = mapped_column("requiereAccion", Boolean, nullable=False, default=False)
    activo: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, default=True)

    novedades: Mapped[list["NovedadModel"]] = relationship(back_populates="tipo_novedad")


class NovedadModel(Base):
    __tablename__ = "novedades"
    __table_args__ = {"schema": "public"}

    id_novedad: Mapped[int] = mapped_column("idNovedad", Integer, primary_key=True, autoincrement=True)
    id_estudiante: Mapped[int] = mapped_column("idEstudiante", Integer, ForeignKey("public.estudiantes.idEstudiante"), nullable=False)
    id_tipo_novedad: Mapped[int] = mapped_column("idTipoNovedad", Integer, ForeignKey("public.tiposnovedad.idTipoNovedad"), nullable=False)
    fecha: Mapped[date] = mapped_column("fecha", Date, nullable=False)
    descripcion: Mapped[str] = mapped_column("descripcion", Text, nullable=False)
    accion_tomada: Mapped[str | None] = mapped_column("accionTomada", Text)
    registrado_por: Mapped[int] = mapped_column("registradoPor", Integer, ForeignKey("public.usuario.idUsuario"), nullable=False)
    fecha_resolucion: Mapped[date | None] = mapped_column("fechaResolucion", Date)
    estado: Mapped[str] = mapped_column("estado", String(15), nullable=False, default="Pendiente")

    estudiante: Mapped["EstudianteModel"] = relationship(back_populates="novedades")
    tipo_novedad: Mapped["TipoNovedadModel"] = relationship(back_populates="novedades")
    registrado_por_usuario: Mapped["UsuarioModel"] = relationship(foreign_keys=[registrado_por])


from app.infrastructure.models.actores import EstudianteModel  # noqa: E402
from app.infrastructure.models.usuario import UsuarioModel  # noqa: E402
