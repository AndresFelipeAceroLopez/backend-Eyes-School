from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class NotaModel(Base):
    __tablename__ = "notas"
    __table_args__ = {"schema": "public"}

    id_nota: Mapped[int] = mapped_column("idNota", Integer, primary_key=True, autoincrement=True)
    id_estudiante: Mapped[int] = mapped_column("idEstudiante", Integer, ForeignKey("public.estudiantes.idEstudiante"), nullable=False)
    id_materia: Mapped[int] = mapped_column("idMateria", Integer, ForeignKey("public.materias.idMateria"), nullable=False)
    id_periodo: Mapped[int] = mapped_column("idPeriodo", Integer, nullable=False)
    nota: Mapped[float] = mapped_column("nota", Numeric(4, 2), nullable=False)
    observacion: Mapped[str | None] = mapped_column("observacion", Text)
    fecha_registro: Mapped[datetime] = mapped_column("fechaRegistro", DateTime, nullable=False, default=func.now())
    registrado_por: Mapped[int] = mapped_column("registradoPor", Integer, ForeignKey("public.usuario.idUsuario"), nullable=False)

    estudiante: Mapped["EstudianteModel"] = relationship(back_populates="notas")
    materia: Mapped["MateriaModel"] = relationship(back_populates="notas")
    registrado_por_usuario: Mapped["UsuarioModel"] = relationship(foreign_keys=[registrado_por])


from app.infrastructure.models.actores import EstudianteModel  # noqa: E402
from app.infrastructure.models.academico import MateriaModel  # noqa: E402
from app.infrastructure.models.usuario import UsuarioModel  # noqa: E402
