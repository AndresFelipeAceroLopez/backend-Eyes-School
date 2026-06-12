from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.models.base import Base


class CursoModel(Base):
    __tablename__ = "cursos"
    __table_args__ = {"schema": "public"}

    id_curso: Mapped[int] = mapped_column("idCurso", Integer, primary_key=True, autoincrement=True)
    nombre_curso: Mapped[str] = mapped_column("nombreCurso", String(30), nullable=False)
    grado: Mapped[str] = mapped_column("grado", String(20), nullable=False)
    jornada: Mapped[str] = mapped_column("jornada", String(10), nullable=False)
    ano: Mapped[int] = mapped_column("ano", Integer, nullable=False)
    area: Mapped[str | None] = mapped_column("area", String(50))
    intensidad_horaria: Mapped[int | None] = mapped_column("intensidadHoraria", Integer)
    descripcion: Mapped[str | None] = mapped_column("descripcion", String)
    activo: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column("fechaCreacion", DateTime, nullable=False, default=func.now())

    estudiantes: Mapped[list["EstudianteModel"]] = relationship(back_populates="curso_actual")
    horarios: Mapped[list["HorarioModel"]] = relationship(back_populates="curso")
    asignaciones: Mapped[list["AsignacionModel"]] = relationship(back_populates="curso")


class MateriaModel(Base):
    __tablename__ = "materias"
    __table_args__ = {"schema": "public"}

    id_materia: Mapped[int] = mapped_column("idMateria", Integer, primary_key=True, autoincrement=True)
    nombre_materia: Mapped[str] = mapped_column("nombreMateria", String(100), nullable=False)
    codigo_materia: Mapped[str] = mapped_column("codigoMateria", String(20), nullable=False)
    activa: Mapped[bool] = mapped_column("activa", Boolean, nullable=False, default=True)

    horarios: Mapped[list["HorarioModel"]] = relationship(back_populates="materia")
    asignaciones: Mapped[list["AsignacionModel"]] = relationship(back_populates="materia")
    notas: Mapped[list["NotaModel"]] = relationship(back_populates="materia")


class EspecializacionModel(Base):
    __tablename__ = "especializaciones"
    __table_args__ = {"schema": "public"}

    id_especializacion: Mapped[int] = mapped_column("idEspecializacion", Integer, primary_key=True, autoincrement=True)
    nombre_especializacion: Mapped[str] = mapped_column("nombreEspecializacion", String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column("descripcion", String)
    activo: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, default=True)

    profesores: Mapped[list["ProfesorEspecializacionModel"]] = relationship(back_populates="especializacion")


class AsignacionModel(Base):
    __tablename__ = "asignaciones"
    __table_args__ = {"schema": "public"}

    id_asignacion: Mapped[int] = mapped_column("idAsignacion", Integer, primary_key=True, autoincrement=True)
    id_profesor: Mapped[int] = mapped_column("idProfesor", Integer, ForeignKey("public.profesores.idProfesor"), nullable=False)
    id_curso: Mapped[int] = mapped_column("idCurso", Integer, ForeignKey("public.cursos.idCurso"), nullable=False)
    id_materia: Mapped[int] = mapped_column("idMateria", Integer, ForeignKey("public.materias.idMateria"), nullable=False)
    fecha_asignacion: Mapped[datetime] = mapped_column("fechaAsignacion", DateTime, nullable=False, default=func.now())
    fecha_finalizacion: Mapped[date | None] = mapped_column("fechaFinalizacion", Date)
    activo: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, default=True)

    profesor: Mapped["ProfesorModel"] = relationship(back_populates="asignaciones")
    curso: Mapped["CursoModel"] = relationship(back_populates="asignaciones")
    materia: Mapped["MateriaModel"] = relationship(back_populates="asignaciones")


class HorarioModel(Base):
    __tablename__ = "Horario"
    __table_args__ = {"schema": "public"}

    id_horario: Mapped[int] = mapped_column("idHorario", Integer, primary_key=True, autoincrement=True)
    id_curso: Mapped[int] = mapped_column("idCurso", Integer, ForeignKey("public.cursos.idCurso"), nullable=False)
    id_materia: Mapped[int] = mapped_column("idMateria", Integer, ForeignKey("public.materias.idMateria"), nullable=False)
    dia: Mapped[str] = mapped_column("dia", String(10), nullable=False)
    hora_inicio: Mapped[time] = mapped_column("horaInicio", Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column("horaFin", Time, nullable=False)
    salon: Mapped[str] = mapped_column("salon", String(20), nullable=False)
    activo: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, default=True)

    curso: Mapped["CursoModel"] = relationship(back_populates="horarios")
    materia: Mapped["MateriaModel"] = relationship(back_populates="horarios")
    profesores_horario: Mapped[list["ProfesorHorarioModel"]] = relationship(back_populates="horario")
    asistencias_aula: Mapped[list["AsistenciaAulaModel"]] = relationship(back_populates="horario")


class ProfesorHorarioModel(Base):
    __tablename__ = "profesores_horario"
    __table_args__ = {"schema": "public"}

    id_profesor: Mapped[int] = mapped_column("idProfesor", Integer, ForeignKey("public.profesores.idProfesor"), primary_key=True)
    id_horario: Mapped[int] = mapped_column("idHorario", Integer, ForeignKey("public.Horario.idHorario"), primary_key=True)
    fecha_asignacion: Mapped[datetime] = mapped_column("fechaAsignacion", DateTime, nullable=False, default=func.now())
    activo: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, default=True)

    profesor: Mapped["ProfesorModel"] = relationship(back_populates="profesores_horario")
    horario: Mapped["HorarioModel"] = relationship(back_populates="profesores_horario")


class ProfesorEspecializacionModel(Base):
    __tablename__ = "profesorespecializacion"
    __table_args__ = {"schema": "public"}

    id_profesor: Mapped[int] = mapped_column("idProfesor", Integer, ForeignKey("public.profesores.idProfesor"), primary_key=True)
    id_especializacion: Mapped[int] = mapped_column("idEspecializacion", Integer, ForeignKey("public.especializaciones.idEspecializacion"), primary_key=True)
    institucion: Mapped[str] = mapped_column("institucion", String(100), nullable=False)

    profesor: Mapped["ProfesorModel"] = relationship(back_populates="especializaciones")
    especializacion: Mapped["EspecializacionModel"] = relationship(back_populates="profesores")


from app.infrastructure.models.actores import EstudianteModel, ProfesorModel  # noqa: E402
from app.infrastructure.models.asistencia import AsistenciaAulaModel  # noqa: E402
from app.infrastructure.models.notas import NotaModel  # noqa: E402
