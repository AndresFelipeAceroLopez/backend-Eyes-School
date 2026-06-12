import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class RolModel(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "public"}

    id_rol: Mapped[int] = mapped_column("idRol", Integer, primary_key=True, autoincrement=True)
    nombre_rol: Mapped[str] = mapped_column("nombreRol", String(30), nullable=False)

    usuarios: Mapped[list["UsuarioModel"]] = relationship(back_populates="rol")


class UsuarioModel(Base):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "public"}

    id_usuario: Mapped[int] = mapped_column("idUsuario", Integer, primary_key=True, autoincrement=True)
    tipo_documento: Mapped[str] = mapped_column("tipoDocumento", String(10), nullable=False)
    numero_documento: Mapped[str] = mapped_column("numeroDocumento", String(20), nullable=False)
    primer_nombre: Mapped[str] = mapped_column("primerNombre", String(50), nullable=False)
    segundo_nombre: Mapped[str | None] = mapped_column("segundoNombre", String(50))
    primer_apellido: Mapped[str] = mapped_column("primerApellido", String(50), nullable=False)
    segundo_apellido: Mapped[str | None] = mapped_column("segundoApellido", String(50))
    genero: Mapped[str | None] = mapped_column("genero", String(1))
    direccion: Mapped[str | None] = mapped_column("direccion", String(200))
    correo: Mapped[str | None] = mapped_column("correo", String(45))
    password: Mapped[str | None] = mapped_column("password", String(255))
    telefono: Mapped[str | None] = mapped_column("telefono", String(20))
    estado: Mapped[bool] = mapped_column("estado", Boolean, nullable=False, default=True)
    fecha_registro: Mapped[datetime] = mapped_column("fechaRegistro", DateTime, nullable=False, default=func.now())
    ultimo_acceso: Mapped[datetime | None] = mapped_column("ultimoAcceso", DateTime)
    id_rol: Mapped[int] = mapped_column("idRol", Integer, ForeignKey("public.roles.idRol"), nullable=False)
    auth_id: Mapped[uuid.UUID | None] = mapped_column("auth_id", UUID(as_uuid=True))
    id_usuario_uuid: Mapped[uuid.UUID] = mapped_column("idUsuario_uuid", UUID(as_uuid=True), default=uuid.uuid4)

    rol: Mapped["RolModel"] = relationship(back_populates="usuarios")
    administrador: Mapped["AdministradorModel | None"] = relationship(back_populates="usuario")
    profesor: Mapped["ProfesorModel | None"] = relationship(back_populates="usuario")
    estudiante: Mapped["EstudianteModel | None"] = relationship(back_populates="usuario")
    padre: Mapped["PadreModel | None"] = relationship(back_populates="usuario")


from app.infrastructure.models.actores import AdministradorModel, EstudianteModel, PadreModel, ProfesorModel  # noqa: E402
