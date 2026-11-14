"""Reglas de los servicios CRUD que no estaban cubiertas (estudiantes, profesores, horarios).

Estos servicios concentraban la mayor parte del código sin probar del paquete `app/`: ninguna
prueba unitaria los tocaba y las de integración solo pasaban por sus caminos felices. Lo que se
verifica aquí no es «que el CRUD llame al repositorio», sino **las decisiones del servicio**: qué
responde cuando el recurso no existe, cuándo hay conflicto, qué campos arma para el cliente y qué
se le pasa al repositorio.

Todo con repositorios dobles: estas pruebas no tocan la base de datos.
"""

from datetime import date, datetime

import pytest

from app.application.estudiantes.schemas import EstudianteCreate, EstudianteUpdate
from app.application.estudiantes.service import EstudianteService
from app.application.horarios.service import HorarioService
from app.application.profesores.service import ProfesorService
from app.core.exceptions import ConflictException, NotFoundException


class _Fila:
    """Objeto con atributos, como una fila del ORM."""

    def __init__(self, **campos):
        self.__dict__.update(campos)


def _estudiante(**extra):
    base = dict(
        id_estudiante=1, id_usuario=10, codigo_estudiante="EST-001",
        fecha_ingreso=date(2026, 1, 15), fecha_egreso=None, estado="Activo",
        id_curso_actual=3, fecha_registro=datetime(2026, 1, 15, 8, 0),
    )
    base.update(extra)
    return _Fila(**base)


class _RepoEstudiantes:
    def __init__(self, filas=None, codigo_existe=False):
        self.filas = filas if filas is not None else []
        self.codigo_existe = codigo_existe
        self.filtros = None
        self.creado = None
        self.actualizado = None

    async def get_all_with_filters(self, **filtros):
        self.filtros = filtros
        return self.filas

    async def get_by_id(self, id_):
        return next((f for f in self.filas if f.id_estudiante == id_), None)

    async def codigo_exists(self, codigo, exclude_id=None):
        return self.codigo_existe

    async def create(self, datos):
        self.creado = datos
        return _estudiante(**{k: v for k, v in datos.items() if k != "id_estudiante"})

    async def update(self, item, datos):
        self.actualizado = datos
        for k, v in datos.items():
            setattr(item, k, v)
        return item


def _servicio_estudiantes(repo):
    s = EstudianteService.__new__(EstudianteService)
    s.repo = repo
    s.ips_repo = None
    return s


# --- EstudianteService ---------------------------------------------------------------------


async def test_el_listado_adjunta_el_nombre_del_usuario_para_no_pedir_usuarios():
    """El front no puede leer /usuarios (es solo-admin), así que el nombre viaja en el listado."""
    fila = _estudiante()
    fila.usuario = _Fila(primer_nombre="Ana", segundo_nombre="María",
                         primer_apellido="Pérez", segundo_apellido="Gómez")
    servicio = _servicio_estudiantes(_RepoEstudiantes([fila]))

    salida = await servicio.list(id_curso=3, estado="Activo")

    assert salida[0].primer_nombre == "Ana"
    assert salida[0].primer_apellido == "Pérez"


async def test_el_listado_sin_usuario_precargado_no_falla():
    """Si la relación no viene precargada, los nombres quedan vacíos en vez de romper."""
    servicio = _servicio_estudiantes(_RepoEstudiantes([_estudiante()]))

    salida = await servicio.list()

    assert salida[0].primer_nombre is None


async def test_los_filtros_del_listado_llegan_al_repositorio():
    repo = _RepoEstudiantes([])
    await _servicio_estudiantes(repo).list(skip=5, limit=20, id_curso=7, estado="Inactivo")

    assert repo.filtros == {"skip": 5, "limit": 20, "id_curso": 7, "estado": "Inactivo"}


async def test_pedir_un_estudiante_que_no_existe_da_404():
    with pytest.raises(NotFoundException):
        await _servicio_estudiantes(_RepoEstudiantes([])).get(99)


async def test_crear_con_un_codigo_repetido_da_409():
    repo = _RepoEstudiantes(codigo_existe=True)
    datos = EstudianteCreate(id_usuario=10, codigo_estudiante="EST-001", fecha_ingreso=date(2026, 1, 15))

    with pytest.raises(ConflictException):
        await _servicio_estudiantes(repo).create(datos)

    assert repo.creado is None, "no debe guardarse nada cuando el código ya existe"


async def test_crear_con_un_codigo_libre_guarda():
    repo = _RepoEstudiantes()
    datos = EstudianteCreate(id_usuario=10, codigo_estudiante="EST-002", fecha_ingreso=date(2026, 1, 15))

    salida = await _servicio_estudiantes(repo).create(datos)

    assert repo.creado["codigo_estudiante"] == "EST-002"
    assert salida.codigo_estudiante == "EST-002"


async def test_actualizar_uno_que_no_existe_da_404():
    with pytest.raises(NotFoundException):
        await _servicio_estudiantes(_RepoEstudiantes([])).update(99, EstudianteUpdate(estado="Inactivo"))


async def test_actualizar_a_un_codigo_de_otro_estudiante_da_409():
    repo = _RepoEstudiantes([_estudiante()], codigo_existe=True)

    with pytest.raises(ConflictException):
        await _servicio_estudiantes(repo).update(1, EstudianteUpdate(codigo_estudiante="EST-999"))


async def test_actualizar_no_manda_los_campos_vacios_al_repositorio():
    """`exclude_none`: un PUT parcial no debe borrar lo que no viene en el cuerpo."""
    repo = _RepoEstudiantes([_estudiante()])

    await _servicio_estudiantes(repo).update(1, EstudianteUpdate(estado="Graduado"))

    assert repo.actualizado == {"estado": "Graduado"}


async def test_borrar_un_estudiante_lo_desactiva_en_vez_de_eliminarlo():
    """Es borrado lógico: el histórico académico del menor no se pierde."""
    repo = _RepoEstudiantes([_estudiante()])

    await _servicio_estudiantes(repo).delete(1)

    assert repo.actualizado == {"estado": "Inactivo"}


async def test_borrar_uno_que_no_existe_da_404():
    with pytest.raises(NotFoundException):
        await _servicio_estudiantes(_RepoEstudiantes([])).delete(99)


# --- HorarioService ------------------------------------------------------------------------


class _RepoHorarios:
    def __init__(self, filas=None):
        self.filas = filas or []
        self.borrado = None

    async def get_all_with_filters(self, **_):
        return self.filas

    async def get_by_id(self, id_):
        return next((f for f in self.filas if f.id_horario == id_), None)

    async def delete(self, item):
        self.borrado = item


def _horario(**extra):
    base = dict(id_horario=1, id_curso=2, id_materia=3, dia_semana="Lunes",
                hora_inicio="07:00", hora_fin="08:00", aula="201", activo=True)
    base.update(extra)
    return _Fila(**base)


async def test_pedir_un_horario_que_no_existe_da_404():
    servicio = HorarioService.__new__(HorarioService)
    servicio.repo = _RepoHorarios([])

    with pytest.raises(NotFoundException):
        await servicio.get(99)


async def test_borrar_un_horario_que_no_existe_da_404():
    servicio = HorarioService.__new__(HorarioService)
    servicio.repo = _RepoHorarios([])

    with pytest.raises(NotFoundException):
        await servicio.delete(99)


# --- ProfesorService -----------------------------------------------------------------------


class _RepoProfesores:
    def __init__(self, filas=None, documento_existe=False):
        self.filas = filas or []
        self.documento_existe = documento_existe
        self.actualizado = None

    async def get_all_with_filters(self, **_):
        return self.filas

    async def get_by_id(self, id_):
        return next((f for f in self.filas if f.id_profesor == id_), None)

    async def update(self, item, datos):
        self.actualizado = datos
        for k, v in datos.items():
            setattr(item, k, v)
        return item


async def test_pedir_un_profesor_que_no_existe_da_404():
    servicio = ProfesorService.__new__(ProfesorService)
    servicio.repo = _RepoProfesores([])
    servicio.esp_repo = None

    with pytest.raises(NotFoundException):
        await servicio.get(99)


# --- ProfesorService: el resto de las reglas -----------------------------------------------


class _RepoProfesoresCompleto(_RepoProfesores):
    def __init__(self, filas=None, codigo_existe=False):
        super().__init__(filas)
        self.codigo_existe = codigo_existe
        self.creado = None

    async def get_all_with_usuario(self, **filtros):
        self.filtros = filtros
        return self.filas

    async def codigo_exists(self, codigo, exclude_id=None):
        return self.codigo_existe

    async def create(self, datos):
        self.creado = datos
        return _profesor(**{k: v for k, v in datos.items()})


def _profesor(**extra):
    base = dict(id_profesor=1, id_usuario=20, codigo_profesor="PRO-001", titulo="Licenciado",
                nivel_estudios="Pregrado", fecha_vinculacion=date(2026, 1, 10), estado="Activo",
                fecha_registro=datetime(2026, 1, 10, 8, 0))
    base.update(extra)
    return _Fila(**base)


def _servicio_profesores(repo, esp_repo=None):
    s = ProfesorService.__new__(ProfesorService)
    s.repo = repo
    s.esp_repo = esp_repo
    return s


async def test_crear_un_profesor_con_codigo_repetido_da_409():
    repo = _RepoProfesoresCompleto(codigo_existe=True)
    from app.application.profesores.schemas import ProfesorCreate

    with pytest.raises(ConflictException):
        await _servicio_profesores(repo).create(
            ProfesorCreate(id_usuario=20, codigo_profesor="PRO-001", titulo="Licenciado",
                           nivel_estudios="Pregrado", fecha_vinculacion=date(2026, 1, 10))
        )
    assert repo.creado is None


async def test_borrar_un_profesor_lo_desactiva():
    repo = _RepoProfesoresCompleto([_profesor()])

    await _servicio_profesores(repo).delete(1)

    assert repo.actualizado == {"estado": "Inactivo"}


async def test_actualizar_un_profesor_que_no_existe_da_404():
    from app.application.profesores.schemas import ProfesorUpdate

    with pytest.raises(NotFoundException):
        await _servicio_profesores(_RepoProfesoresCompleto([])).update(99, ProfesorUpdate(estado="Inactivo"))


async def test_borrar_un_profesor_que_no_existe_da_404():
    with pytest.raises(NotFoundException):
        await _servicio_profesores(_RepoProfesoresCompleto([])).delete(99)


class _RepoEspecializaciones:
    def __init__(self, existente=None):
        self.existente = existente
        self.creado = None
        self.borrado = None

    async def get_by_profesor(self, id_profesor):
        return []

    async def get_one(self, id_profesor, id_especializacion):
        return self.existente

    async def create(self, datos):
        self.creado = datos
        return _Fila(**datos)

    async def delete(self, item):
        self.borrado = item


async def test_agregar_una_especializacion_repetida_da_409():
    from app.application.profesores.schemas import AgregarEspecializacionRequest

    esp = _RepoEspecializaciones(existente=_Fila(id_profesor=1, id_especializacion=2))
    servicio = _servicio_profesores(_RepoProfesoresCompleto([_profesor()]), esp)

    with pytest.raises(ConflictException):
        await servicio.agregar_especializacion(1, AgregarEspecializacionRequest(id_especializacion=2, institucion="Universidad X"))

    assert esp.creado is None


# --- ReporteService: validación de archivos ------------------------------------------------


class _ArchivoFalso:
    """Imita lo que FastAPI entrega en un UploadFile, sin tocar el disco al construirlo."""

    def __init__(self, filename, contenido=b"x"):
        self.filename = filename
        self._contenido = contenido

    async def read(self):
        return self._contenido


@pytest.mark.parametrize("nombre", ["informe.exe", "script.sh", "pagina.html", "sin_extension"])
async def test_subir_un_reporte_con_formato_no_permitido_da_409(nombre):
    """Lista blanca: solo documentos. Un .html servido desde /static sería XSS almacenado."""
    from app.application.reportes.service import ReporteService

    servicio = ReporteService.__new__(ReporteService)

    with pytest.raises(ConflictException):
        await servicio.upload_archivo(_ArchivoFalso(nombre))


async def test_subir_un_reporte_de_mas_de_10_mb_da_409():
    from app.application.reportes.service import MAX_BYTES, ReporteService

    servicio = ReporteService.__new__(ReporteService)

    with pytest.raises(ConflictException):
        await servicio.upload_archivo(_ArchivoFalso("informe.pdf", b"x" * (MAX_BYTES + 1)))


async def test_subir_un_pdf_valido_lo_guarda_y_devuelve_su_ruta(tmp_path, monkeypatch):
    from app.application.reportes import service as modulo

    monkeypatch.setattr(modulo, "UPLOAD_DIR", str(tmp_path / "reportes"))
    servicio = modulo.ReporteService.__new__(modulo.ReporteService)

    ruta = await servicio.upload_archivo(_ArchivoFalso("informe.PDF", b"%PDF-1.4 contenido"))

    assert ruta.startswith("/static/reportes/")
    assert ruta.endswith(".pdf"), "la extensión se normaliza a minúsculas"
    guardados = list((tmp_path / "reportes").iterdir())
    assert len(guardados) == 1 and guardados[0].read_bytes() == b"%PDF-1.4 contenido"


class _RepoReportes:
    def __init__(self, filas=None):
        self.filas = filas or []
        self.borrado = None

    async def get_by_id(self, id_):
        return next((f for f in self.filas if f.id_reporte == id_), None)

    async def get_all(self, **_):
        return self.filas

    async def get_by_administrador(self, id_admin, **_):
        return [f for f in self.filas if f.id_administrador == id_admin]

    async def delete(self, item):
        self.borrado = item


async def test_borrar_un_reporte_que_no_existe_da_404():
    from app.application.reportes.service import ReporteService

    servicio = ReporteService.__new__(ReporteService)
    servicio.repo = _RepoReportes([])

    with pytest.raises(NotFoundException):
        await servicio.delete(99)


async def test_borrar_un_reporte_tambien_borra_su_archivo_del_disco(tmp_path, monkeypatch):
    """Si no, los PDF se acumulan en el disco efímero de Azure (BE-15)."""
    from app.application.reportes.service import ReporteService

    monkeypatch.chdir(tmp_path)
    carpeta = tmp_path / "static" / "reportes"
    carpeta.mkdir(parents=True)
    archivo = carpeta / "abc.pdf"
    archivo.write_bytes(b"pdf")

    fila = _Fila(id_reporte=1, id_administrador=1, archivo_generado="/static/reportes/abc.pdf")
    servicio = ReporteService.__new__(ReporteService)
    servicio.repo = _RepoReportes([fila])

    await servicio.delete(1)

    assert not archivo.exists(), "el archivo debe desaparecer del disco"
    assert servicio.repo.borrado is fila
