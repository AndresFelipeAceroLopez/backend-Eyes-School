"""Dobles de prueba reutilizables: repositorios y servicios externos falsos.

Cada doble guarda lo que recibe para que la prueba lo inspeccione. Se reemplazan en el módulo
del servicio con `monkeypatch.setattr(modulo, "NombreRepository", Doble)`.
"""

from datetime import date, datetime
from types import SimpleNamespace

from app.application.common.notificador import Notificador


class RepoNotas:
    existe = False
    creadas: list[dict] = []
    por_id: dict[int, SimpleNamespace] = {}
    filtros: list[dict] = []

    def __init__(self, session):
        pass

    @classmethod
    def reiniciar(cls):
        cls.existe, cls.creadas, cls.por_id, cls.filtros = False, [], {}, []

    async def exists(self, id_estudiante, id_materia, id_periodo):
        return RepoNotas.existe

    async def create(self, data):
        RepoNotas.creadas.append(data)
        return SimpleNamespace(**{
            "id_nota": 1, "fecha_registro": datetime(2026, 11, 2), "observacion": None, **data
        })

    async def get_by_id(self, id_nota):
        return RepoNotas.por_id.get(id_nota)

    async def update(self, item, data):
        for k, v in data.items():
            setattr(item, k, v)
        return item

    async def delete(self, item):
        pass

    async def get_with_filters(self, **filtros):
        RepoNotas.filtros.append(filtros)
        return []


class RepoProfesores:
    profesor: SimpleNamespace | None = SimpleNamespace(id_profesor=3)

    def __init__(self, session):
        pass

    async def get_by_usuario(self, id_usuario):
        return RepoProfesores.profesor


class RepoEstudiantes:
    estudiante: SimpleNamespace | None = SimpleNamespace(
        id_estudiante=10, id_curso_actual=5,
        usuario=SimpleNamespace(primer_nombre="Ana", primer_apellido="Gómez"),
    )

    def __init__(self, session):
        pass

    async def get_by_id(self, id_estudiante):
        return RepoEstudiantes.estudiante

    async def get_con_usuario(self, id_estudiante):
        return RepoEstudiantes.estudiante


class RepoAsignaciones:
    dicta = True
    consultas: list[tuple] = []

    def __init__(self, session):
        pass

    async def docente_dicta(self, id_profesor, id_materia, id_curso):
        RepoAsignaciones.consultas.append((id_profesor, id_materia, id_curso))
        return RepoAsignaciones.dicta


class RepoNovedades:
    creadas: list[dict] = []
    por_id: dict[int, SimpleNamespace] = {}
    borradas: list[int] = []

    def __init__(self, session):
        pass

    @classmethod
    def reiniciar(cls):
        cls.creadas, cls.por_id, cls.borradas = [], {}, []

    async def create(self, data):
        RepoNovedades.creadas.append(data)
        return novedad(id_novedad=1, **data)

    async def get_by_id(self, id_novedad):
        return RepoNovedades.por_id.get(id_novedad)

    async def update(self, item, data):
        for k, v in data.items():
            setattr(item, k, v)
        return item

    async def delete(self, item):
        RepoNovedades.borradas.append(item.id_novedad)


def novedad(**campos):
    base = {
        "id_novedad": 1, "id_estudiante": 10, "id_tipo_novedad": 1, "fecha": date(2026, 11, 2),
        "descripcion": "Llegó tarde", "accion_tomada": None, "registrado_por": 7,
        "fecha_resolucion": None, "estado": "Pendiente",
    }
    base.update(campos)
    return SimpleNamespace(**base)


class RepoTiposNovedad:
    def __init__(self, session):
        pass


class RepoPadres:
    padres: list[SimpleNamespace] = []

    def __init__(self, session):
        pass

    async def get_by_estudiante(self, id_estudiante):
        return RepoPadres.padres


class RepoDispositivos:
    tokens_por_usuario: dict[int, list[str]] = {}

    def __init__(self, session):
        pass

    async def tokens_de_usuarios(self, ids_usuario):
        return [t for i in ids_usuario for t in RepoDispositivos.tokens_por_usuario.get(i, [])]


class NotificadorFalso(Notificador):
    """Guarda los envíos en lugar de llamar a Firebase; con `falla=True` lanza un error."""

    def __init__(self, falla: bool = False):
        self.envios: list[dict] = []
        self.falla = falla

    async def enviar(self, tokens, titulo, cuerpo, datos=None):
        if self.falla:
            raise RuntimeError("Firebase no disponible")
        self.envios.append({"tokens": tokens, "titulo": titulo, "cuerpo": cuerpo, "datos": datos})


# --- Sesiones y usuarios (autenticación) -----------------------------------------------------


class RepoSesiones:
    """Sesiones de refresco en memoria: `activas` es el conjunto de `jti` vigentes."""

    activas: set[str] = set()
    creadas: list[tuple] = []
    revocadas: list[str] = []
    revocadas_de_usuario: list[int] = []

    def __init__(self, session):
        pass

    @classmethod
    def reiniciar(cls):
        cls.activas, cls.creadas, cls.revocadas, cls.revocadas_de_usuario = set(), [], [], []

    async def crear(self, jti, id_usuario, expira):
        RepoSesiones.creadas.append((jti, id_usuario, expira))
        RepoSesiones.activas.add(jti)

    async def obtener_activa(self, jti):
        return SimpleNamespace(jti=jti) if jti in RepoSesiones.activas else None

    async def revocar(self, jti):
        RepoSesiones.revocadas.append(jti)
        RepoSesiones.activas.discard(jti)

    async def revocar_todas(self, id_usuario):
        RepoSesiones.revocadas_de_usuario.append(id_usuario)
        RepoSesiones.activas.clear()

    async def limpiar_vencidas(self, dias=30):
        pass


def usuario_auth(**campos):
    """Usuario falso con todo lo que lee `AuthService` (contraseña «Actual#2026»)."""
    from app.core.security import hash_password

    base = {
        "id_usuario": 7, "id_rol": 1, "rol": SimpleNamespace(id_rol=1, nombre_rol="docente"),
        "correo": "ana@x.com", "primer_nombre": "Ana", "password": hash_password("Actual#2026"),
        "tipo_documento": "CC", "numero_documento": "1", "primer_apellido": "Gómez",
        "segundo_nombre": None, "segundo_apellido": None, "genero": None, "direccion": None,
        "telefono": None, "fecha_registro": datetime(2026, 1, 1), "foto_perfil": None,
        "estado": True, "bloqueado_hasta": None, "intentos_fallidos": 0,
        "password_actualizada": None, "ultimo_acceso": None,
    }
    base.update(campos)
    return SimpleNamespace(**base)


class RepoUsuariosAuth:
    """Repositorio de usuarios con estado: cuenta fallos y bloqueos como lo hace la base."""

    usuario: SimpleNamespace | None = None
    bloqueos: list = []

    def __init__(self, session):
        pass

    @classmethod
    def reiniciar(cls, usuario=None):
        cls.usuario, cls.bloqueos = usuario, []

    async def get_by_correo(self, correo):
        u = RepoUsuariosAuth.usuario
        return u if u and u.correo == correo.strip().lower() else None

    async def get_by_id(self, id_usuario):
        return RepoUsuariosAuth.usuario

    async def get_by_id_with_rol(self, id_usuario):
        return RepoUsuariosAuth.usuario

    async def update(self, user, data):
        for k, v in data.items():
            setattr(user, k, v)
        return user

    async def registrar_fallo(self, id_usuario):
        RepoUsuariosAuth.usuario.intentos_fallidos += 1
        return RepoUsuariosAuth.usuario.intentos_fallidos

    async def bloquear(self, id_usuario, hasta):
        RepoUsuariosAuth.bloqueos.append(hasta)
        RepoUsuariosAuth.usuario.bloqueado_hasta = hasta
        RepoUsuariosAuth.usuario.intentos_fallidos = 0

    async def reiniciar_fallos(self, id_usuario):
        RepoUsuariosAuth.usuario.intentos_fallidos = 0
        RepoUsuariosAuth.usuario.bloqueado_hasta = None
