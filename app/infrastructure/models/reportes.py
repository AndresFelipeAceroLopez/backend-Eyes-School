from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, LargeBinary, String, Text, func
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
    # Text (no varchar(255)): guarda el archivo del reporte como data URL base64.
    archivo_generado: Mapped[str | None] = mapped_column("archivoGenerado", Text)

    administrador: Mapped["AdministradorModel"] = relationship(back_populates="reportes")


class ReporteArchivoModel(Base):
    """N-23: el contenido de los archivos de reporte, guardado en la base.

    Antes se escribían en `static/reportes` del App Service, que Oryx recrea en cada despliegue:
    todo archivo subido se perdía en el siguiente. La clave es la misma ruta que la API devuelve
    al subir (`/static/reportes/<uuid>.<ext>`), así el contrato con la web no cambia.
    """

    __tablename__ = "reporte_archivos"
    __table_args__ = {"schema": "public"}

    ruta: Mapped[str] = mapped_column("ruta", Text, primary_key=True)
    contenido: Mapped[bytes] = mapped_column("contenido", LargeBinary, nullable=False)
    tipo: Mapped[str] = mapped_column("tipo", String(120), nullable=False)
    tamano: Mapped[int] = mapped_column("tamano", Integer, nullable=False)
    creado: Mapped[datetime] = mapped_column(
        "creado", DateTime, nullable=False, server_default=func.now()
    )


from app.infrastructure.models.actores import AdministradorModel, EstudianteModel  # noqa: E402
