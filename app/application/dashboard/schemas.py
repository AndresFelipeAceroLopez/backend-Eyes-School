from pydantic import BaseModel


class AdminDashboard(BaseModel):
    total_estudiantes: int
    total_profesores: int
    total_cursos: int
    promedio_general: float | None
    tasa_aprobacion: float | None
    porcentaje_asistencia: float | None
    total_novedades_activas: int


class DocenteDashboard(BaseModel):
    total_cursos_asignados: int
    total_estudiantes: int
    notas_registradas_hoy: int
    asistencias_registradas_hoy: int


class EstudianteDashboard(BaseModel):
    promedio_general: float | None
    porcentaje_asistencia: float | None
    novedades_pendientes: int
    periodo_actual: int


class PadreDashboard(BaseModel):
    id_estudiante: int
    nombre_estudiante: str
    promedio_general: float | None
    porcentaje_asistencia: float | None
    novedades_pendientes: int
