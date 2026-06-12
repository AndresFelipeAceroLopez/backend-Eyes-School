from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class EstudianteIPSModel(Base):
    __tablename__ = "estudianteips"
    __table_args__ = {"schema": "public"}

    id_estudiante: Mapped[int] = mapped_column("idEstudiante", Integer, ForeignKey("public.estudiantes.idEstudiante"), primary_key=True)
    id_ips: Mapped[int] = mapped_column("idIPS", Integer, primary_key=True)
    nombre_ips: Mapped[str] = mapped_column("nombreIPS", String(100), nullable=False)
    fecha_afiliacion: Mapped[date] = mapped_column("fechaAfiliacion", Date, nullable=False)
    fecha_vencimiento: Mapped[date | None] = mapped_column("fechaVencimiento", Date)
    tipo_afiliacion: Mapped[str] = mapped_column("tipoAfiliacion", String(20), nullable=False)
    activo: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, default=True)

    estudiante: Mapped["EstudianteModel"] = relationship(back_populates="ips")


class ReporteModel(Base):
    __tablename__ = "Reportes"
    __table_args__ = {"schema": "public"}

    id_reporte: Mapped[int] = mapped_column("idReporte", Integer, primary_key=True, autoincrement=True)
    nombre_reporte: Mapped[str] = mapped_column("nombreReporte", Text, nullable=False)
    tipo_reporte: Mapped[str] = mapped_column("tipoReporte", Text, nullable=False)
    fecha_generacion: Mapped[date] = mapped_column("fechaGeneracion", Date, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column("fechaInicio", Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column("fechaFin", Date, nullable=False)
    estado: Mapped[str] = mapped_column("estado", Text, nullable=False)
    id_administrador: Mapped[int] = mapped_column("idAdministrador", Integer, ForeignKey("public.administrador.idAdministrador"), nullable=False)
    parametros: Mapped[str] = mapped_column("parametros", String(1), nullable=False)
    archivo_generado: Mapped[str | None] = mapped_column("archivoGenerado", String(255))

    administrador: Mapped["AdministradorModel"] = relationship(back_populates="reportes")


from app.infrastructure.models.actores import AdministradorModel, EstudianteModel  # noqa: E402
