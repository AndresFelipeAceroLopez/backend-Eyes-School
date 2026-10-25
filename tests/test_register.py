"""El registro crea el perfil del rol elegido.

Antes se comparaba el nombre del rol contra 'profesor'/'administrador', pero
en la base se llaman 'docente'/'admin': los docentes y administradores quedaban
sin perfil y la app móvil les mostraba "tu cuenta no tiene un perfil de docente".
"""

from types import SimpleNamespace

import pytest

from app.application.auth import service as auth_service
from app.application.auth.schemas import RegisterRequest


class _Recorder:
    """Repositorio falso que guarda lo que se le pide crear."""

    created: dict[str, list[dict]] = {}

    def __init__(self, name):
        self.name = name

    def __call__(self, session):
        return self

    async def create(self, data):
        _Recorder.created.setdefault(self.name, []).append(data)
        return SimpleNamespace(**{"id_profesor": 99, **data})


class _FakeSession:
    def __init__(self):
        self.commits = 0

    async def commit(self):
        self.commits += 1


@pytest.fixture
def registro(monkeypatch):
    _Recorder.created = {}
    usuario_model = SimpleNamespace(estado=True)

    class FakeUsuarioService:
        def __init__(self, session):
            pass

        async def create(self, data):
            return SimpleNamespace(id_usuario=50, id_rol=data.id_rol, estado=True, rol=None)

    class FakeUsuarioRepository:
        def __init__(self, session):
            pass

        async def get_by_id(self, id_usuario):
            return usuario_model

    monkeypatch.setattr(auth_service, "UsuarioService", FakeUsuarioService)
    monkeypatch.setattr(auth_service, "UsuarioRepository", FakeUsuarioRepository)
    for name in [
        "EstudianteRepository",
        "ProfesorRepository",
        "PadreRepository",
        "AdministradorRepository",
        "ProfesorEspecializacionRepository",
    ]:
        monkeypatch.setattr(auth_service, name, _Recorder(name))

    async def run(**fields):
        session = _FakeSession()
        data = RegisterRequest(
            tipo_documento="CC",
            numero_documento="1012",
            primer_nombre="Ana",
            primer_apellido="Gómez",
            **fields,
        )
        user = await auth_service.AuthService(session).register(data)
        return user, usuario_model, session

    return run


async def test_un_docente_registrado_tiene_perfil_de_profesor_y_queda_inactivo(registro):
    user, model, session = await registro(
        id_rol=1, titulo="Licenciada", id_especializacion=3, institucion="UPN"
    )

    profesor = _Recorder.created["ProfesorRepository"][0]
    assert profesor["codigo_profesor"] == "1012"
    assert profesor["titulo"] == "Licenciada"
    assert _Recorder.created["ProfesorEspecializacionRepository"][0]["id_profesor"] == 99
    assert user.estado is False
    assert model.estado is False
    assert session.commits == 1


async def test_un_administrador_registrado_tiene_perfil_y_queda_inactivo(registro):
    user, _, _ = await registro(id_rol=3, cargo="Coordinadora")

    assert _Recorder.created["AdministradorRepository"][0]["cargo"] == "Coordinadora"
    assert user.estado is False


async def test_un_estudiante_registrado_queda_activo_en_su_curso(registro):
    user, _, _ = await registro(id_rol=2, id_curso_actual=4)

    estudiante = _Recorder.created["EstudianteRepository"][0]
    assert estudiante["id_curso_actual"] == 4
    assert estudiante["codigo_estudiante"] == "1012"
    assert user.estado is True


async def test_un_padre_se_vincula_solo_si_indica_estudiante_y_parentesco(registro):
    await registro(id_rol=4, id_estudiante_vinculado=7, parentesco="Madre")
    await registro(id_rol=4)

    assert _Recorder.created["PadreRepository"] == [
        {"id_usuario": 50, "id_estudiante": 7, "parentesco": "Madre", "ocupacion": None}
    ]
