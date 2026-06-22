# CLAUDE.md — Eyes School Backend

## Resumen del Proyecto

**Eyes School** es una API REST para gestión escolar construida con **FastAPI** (Python ≥ 3.11).
Gestiona usuarios, estudiantes, profesores, padres, administradores, cursos, materias, asignaciones, horarios, asistencia, notas, novedades, reportes y dashboard.

---

## Arquitectura

El proyecto sigue **Clean Architecture** con 4 capas bien definidas:

```
app/
├── api/            → Capa de presentación (endpoints FastAPI)
├── application/    → Capa de aplicación (servicios + schemas Pydantic)
├── domain/         → Capa de dominio (entidades + interfaces de repositorio)
├── infrastructure/ → Capa de infraestructura (modelos SQLAlchemy + repositorios concretos)
└── core/           → Transversal (config, seguridad, DB, Redis, dependencias, excepciones)
```

### Flujo de una petición

```
Request → api/v1/{recurso}.py (router)
       → application/{recurso}/service.py (lógica de negocio)
       → infrastructure/repositories/{repo}.py (acceso a datos)
       → infrastructure/models/{modelo}.py (SQLAlchemy ORM)
       → PostgreSQL
```

### Dirección de dependencias

```
api → application → infrastructure
              ↑
           domain (interfaces abstractas)
```

- `domain/repositories/base.py` define la interfaz abstracta `BaseRepository[T]` (ABC).
- `infrastructure/repositories/base_repository.py` proporciona la implementación genérica con SQLAlchemy.
- Los servicios en `application/` instancian directamente los repositorios concretos (no se usa inyección de dependencias formal aún).

### Stack tecnológico

| Componente       | Tecnología                         |
|------------------|------------------------------------|
| Framework        | FastAPI 0.137+                     |
| ORM              | SQLAlchemy 2.0+ (async)            |
| Base de datos    | PostgreSQL (asyncpg)               |
| Migraciones      | Alembic                            |
| Cache/Sesiones   | Redis (redis-py async)             |
| Auth             | JWT (python-jose) + bcrypt         |
| Validación       | Pydantic v2                        |
| Config           | pydantic-settings + .env           |
| Linter           | Ruff                               |
| Tests            | pytest + pytest-asyncio            |
| CI/CD            | GitHub Actions → Azure Web App     |

---

## Comandos de Desarrollo

### Configuración inicial

```bash
# Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# O con dependencias de desarrollo
pip install -e ".[dev]"

# Copiar variables de entorno
copy .env.example .env         # Windows
cp .env.example .env           # Linux/Mac
```

### Servidor de desarrollo

```bash
# Iniciar con recarga automática
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# La documentación interactiva está disponible en:
#   http://localhost:8000/docs     (Swagger UI)
#   http://localhost:8000/redoc    (ReDoc)
```

### Base de datos y migraciones

```bash
# Ver migración actual
alembic current

# Crear nueva migración
alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar migraciones pendientes
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Crear primer administrador (script interactivo, una sola vez)
python create_admin.py
```

### Linting y formateo

```bash
# Verificar código
ruff check .

# Corregir automáticamente
ruff check --fix .

# Formatear código
ruff format .
```

### Tests

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app

# Tests verbosos
pytest -v
```

---

## Convenciones de Código

### Generales

- **Python ≥ 3.11** — Usar type hints modernos (`int | None` en lugar de `Optional[int]`)
- **Línea máxima**: 100 caracteres (configurado en Ruff)
- **Ruff rules**: `E`, `F`, `I`, `N`, `W` — errores, imports ordenados, naming
- **Idioma del código**: español para nombres de dominio (entidades, campos), inglés para código técnico (funciones de utilidad, infraestructura)
- **Async todo**: Todas las operaciones de I/O son async (`async def`, `await`)

### Nombres

| Elemento               | Convención                              | Ejemplo                          |
|------------------------|-----------------------------------------|----------------------------------|
| Modelos SQLAlchemy     | `{Entidad}Model` (PascalCase)           | `EstudianteModel`, `CursoModel`  |
| Repositorios           | `{Entidad}Repository`                   | `UsuarioRepository`              |
| Servicios              | `{Entidad}Service`                      | `AuthService`, `NotaService`     |
| Schemas Pydantic       | `{Entidad}{Accion}` (Create/Update/Out) | `EstudianteCreate`, `NotaOut`    |
| Endpoints (archivos)   | `snake_case.py` en español              | `estudiantes.py`, `novedades.py` |
| Tags de router         | PascalCase en español                   | `tags=["Estudiantes"]`           |
| Columnas DB            | camelCase en la DB, snake_case en Python | `"idUsuario"` → `id_usuario`    |

### Patrón de columnas en modelos

Los modelos SQLAlchemy mapean nombres camelCase de la DB a snake_case en Python:

```python
id_usuario: Mapped[int] = mapped_column("idUsuario", Integer, primary_key=True)
```

### Estructura de un módulo de aplicación

Cada módulo en `app/application/{recurso}/` tiene:
- `__init__.py` — vacío
- `schemas.py` — Schemas Pydantic (`Create`, `Update`, `Out`)
- `service.py` — Clase de servicio con lógica de negocio

### Patrón de servicio

```python
class MiService:
    def __init__(self, session: AsyncSession):
        self.repo = MiRepository(session)

    async def list(self, **filters) -> list[MiOut]:
        items = await self.repo.get_all_with_filters(**filters)
        return [MiOut.model_validate(e) for e in items]

    async def get(self, id: int) -> MiOut:
        item = await self.repo.get_by_id(id)
        if not item:
            raise NotFoundException("Recurso no encontrado")
        return MiOut.model_validate(item)
```

### Patrón de endpoint

```python
router = APIRouter(prefix="/recurso", tags=["Recurso"])

@router.get("", response_model=list[RecursoOut], dependencies=[require_roles("admin")])
async def list_recursos(db: DbSession, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    return await RecursoService(db).list(skip=skip, limit=limit)
```

### Schemas Pydantic

- Todos los schemas `Out` usan `model_config = {"from_attributes": True}` para serializar desde modelos ORM.
- Usar `Literal[...]` para campos con valores acotados (estados, tipos).
- `model_dump(exclude_none=True)` para updates parciales.

---

## Estructura de Carpetas

```
backend-Eyes-School-1/
│
├── main.py                          # Punto de entrada: create_app() + factory FastAPI
├── create_admin.py                  # Script para crear el primer admin
├── alembic.ini                      # Configuración de Alembic
├── pyproject.toml                   # Metadatos del proyecto, deps, config de ruff/pytest
├── requirements.txt                 # Dependencias fijadas (pip freeze)
├── schema.sql                       # Dump completo del esquema SQL
├── .env / .env.example              # Variables de entorno
│
├── alembic/
│   ├── env.py                       # Config de migraciones async
│   └── versions/                    # Archivos de migración
│
├── app/
│   ├── __init__.py
│   │
│   ├── core/                        # ← Transversal
│   │   ├── config.py                #    Pydantic Settings (DATABASE_URL, SECRET_KEY, etc.)
│   │   ├── database.py              #    Engine async + sessionmaker + get_db()
│   │   ├── redis.py                 #    Cliente Redis async singleton
│   │   ├── security.py              #    Hash/verify password, create/decode JWT
│   │   ├── dependencies.py          #    DI: DbSession, AuthUser, require_roles()
│   │   └── exceptions.py            #    Excepciones HTTP reutilizables
│   │
│   ├── domain/                      # ← Capa de dominio
│   │   ├── entities/                #    (vacío — sin dataclasses de dominio aún)
│   │   └── repositories/
│   │       └── base.py              #    ABC BaseRepository[T] (interfaz abstracta)
│   │
│   ├── infrastructure/              # ← Capa de infraestructura
│   │   ├── models/                  #    Modelos SQLAlchemy ORM
│   │   │   ├── base.py              #      DeclarativeBase
│   │   │   ├── usuario.py           #      RolModel, UsuarioModel
│   │   │   ├── actores.py           #      Administrador, Profesor, Estudiante, Padre
│   │   │   ├── academico.py         #      Curso, Materia, Especialización, Asignación, Horario
│   │   │   ├── asistencia.py        #      Asistencia, AsistenciaAula
│   │   │   ├── notas.py             #      Nota, Periodo
│   │   │   ├── novedades.py         #      Novedad
│   │   │   └── reportes.py          #      Reporte, EstudianteIPS, IPS
│   │   │
│   │   └── repositories/            #    Implementaciones concretas
│   │       ├── base_repository.py   #      BaseRepository genérico (CRUD)
│   │       ├── usuario_repository.py
│   │       ├── actores_repository.py
│   │       ├── academico_repository.py
│   │       ├── asistencia_repository.py
│   │       ├── notas_repository.py
│   │       ├── novedades_repository.py
│   │       └── reportes_repository.py
│   │
│   ├── application/                 # ← Capa de aplicación (servicios + schemas)
│   │   ├── auth/                    #    Login, refresh, logout, /me
│   │   ├── usuarios/                #    CRUD usuarios
│   │   ├── estudiantes/             #    CRUD estudiantes + IPS
│   │   ├── profesores/              #    CRUD profesores
│   │   ├── cursos/                  #    CRUD cursos
│   │   ├── materias/                #    CRUD materias
│   │   ├── asignaciones/            #    Profesor ↔ Curso ↔ Materia
│   │   ├── horarios/                #    CRUD horarios
│   │   ├── asistencia/              #    Registro de asistencia
│   │   ├── notas/                   #    Gestión de notas
│   │   ├── novedades/               #    Observaciones/novedades
│   │   ├── reportes/                #    Generación de reportes
│   │   └── dashboard/               #    Estadísticas del panel
│   │
│   └── api/                         # ← Capa de presentación
│       └── v1/
│           ├── router.py            #    Registra todos los sub-routers
│           ├── auth.py
│           ├── usuarios.py
│           ├── estudiantes.py
│           ├── profesores.py
│           ├── padres.py
│           ├── administradores.py
│           ├── cursos.py
│           ├── materias.py
│           ├── especializaciones.py
│           ├── asignaciones.py
│           ├── horarios.py
│           ├── asistencia.py
│           ├── notas.py
│           ├── novedades.py
│           ├── reportes.py
│           ├── roles.py
│           └── dashboard.py
│
├── docs/                            # Documentación de arquitectura
│   ├── backend-architecture.md
│   ├── database-analysis.md
│   └── domain-analysis.md
│
└── .github/workflows/
    └── main_apieyeschool.yml        # CI/CD: Build → Deploy a Azure Web App
```

---

## Flujo de Trabajo para Agentes

### Antes de escribir código

1. **Entiende la capa** — Identifica en qué capa trabajarás (api, application, infrastructure, core).
2. **Revisa los patrones existentes** — Mira un módulo similar (ej: `estudiantes/` tiene service + schemas + endpoint + repository).
3. **Consulta `docs/`** — `backend-architecture.md`, `database-analysis.md` y `domain-analysis.md` contienen contexto clave.
4. **Revisa el `schema.sql`** — Es el dump completo de la DB. Úsalo para verificar nombres de tablas/columnas.

### Crear un nuevo recurso (checklist)

1. **Modelo SQLAlchemy** → `app/infrastructure/models/{nombre}.py`
   - Hereda de `Base`
   - Usa `__table_args__ = {"schema": "public"}`
   - Mapea columnas camelCase de la DB a snake_case
2. **Repositorio** → `app/infrastructure/repositories/{nombre}_repository.py`
   - Hereda de `BaseRepository[MiModel]`
   - Agrega métodos personalizados de consulta
3. **Schemas Pydantic** → `app/application/{nombre}/schemas.py`
   - `Create`, `Update`, `Out` (con `from_attributes = True`)
4. **Servicio** → `app/application/{nombre}/service.py`
   - Instancia el repositorio en `__init__`
   - Valida reglas de negocio, lanza excepciones HTTP
5. **Endpoint** → `app/api/v1/{nombre}.py`
   - Router con `prefix` y `tags`
   - Usa `DbSession`, `AuthUser`, `require_roles()`
6. **Registrar router** → Agregar import + `api_router.include_router()` en `app/api/v1/router.py`
7. **Migración** → `alembic revision --autogenerate -m "add_{nombre}"`

### Reglas críticas para agentes

- **NO crear archivos de test fuera de `tests/`** (el directorio no existe aún pero está configurado en pytest).
- **NO modificar `.env`** — solo `.env.example` para documentar nuevas variables.
- **NO cambiar la estructura de capas** — Respetar la separación api/application/domain/infrastructure.
- **SIEMPRE usar async** — Todo acceso a DB/Redis debe ser async.
- **SIEMPRE validar permisos** — Usar `require_roles()` en cada endpoint.
- **SIEMPRE manejar errores** — Usar las excepciones de `core/exceptions.py`.
- **Schemas `Out` siempre con `from_attributes = True`** para serializar modelos ORM.

---

## Autenticación y Autorización

### Sistema de auth

- **JWT Bearer** — Access token (30 min) + Refresh token (7 días).
- **Refresh tokens** almacenados en Redis con TTL para revocación.
- **Roles**: `admin`, `docente`, `estudiante`, `padre`.
- **Protección**: `require_roles("admin", "docente")` en `dependencies` del endpoint.

### Flujo de autenticación

```
POST /api/v1/auth/login        → Devuelve access_token + refresh_token
POST /api/v1/auth/refresh      → Nuevo access_token con refresh_token válido
POST /api/v1/auth/logout       → Revoca el refresh_token en Redis
GET  /api/v1/auth/me           → Info del usuario autenticado
```

### Dependencias de inyección

```python
DbSession    = Annotated[AsyncSession, Depends(get_db)]         # Sesión de DB
RedisClient  = Annotated[Redis, Depends(get_redis)]              # Cliente Redis
AuthUser     = Annotated[CurrentUser, Depends(get_current_user)] # Usuario actual
require_roles("admin", "docente")                                # Verificación de rol
```

---

## Seguridad

### Variables sensibles

- `SECRET_KEY` — **DEBE** cambiarse en producción. Nunca commitear el valor real.
- `DATABASE_URL` — Credenciales de PostgreSQL. Solo en `.env`, nunca en código.
- `REDIS_URL` — URL de conexión a Redis.
- `.env` está en `.gitignore` (solo `.env.example` se versiona).

### Passwords

- Hash con **bcrypt** (`bcrypt.hashpw` + `gensalt`).
- Nunca almacenar passwords en texto plano.
- Nunca retornar el campo `password` en schemas `Out`.

### CORS

- Actualmente `allow_origins=["*"]` — **Restringir en producción** al dominio del frontend.
- `allow_credentials=True` + `allow_methods=["*"]` + `allow_headers=["*"]`.

### Principios

- Nunca exponer stack traces en producción.
- Validar todos los inputs con Pydantic.
- Usar query parameters con `ge`, `le` para paginación segura.
- Redis es degradable: si falla, la app sigue funcionando (refresh token revocation se salta).

---

## Despliegue

### CI/CD (GitHub Actions)

El archivo `.github/workflows/main_apieyeschool.yml` define:

1. **Build** (en push a `main`):
   - Python 3.11
   - Crea virtualenv + instala dependencias
   - Sube artefacto (sin `antenv/`)

2. **Deploy**:
   - Login a Azure con credenciales OIDC (client-id, tenant-id, subscription-id como secrets)
   - Deploy a **Azure Web App** `ApiEyeSchool` en slot `Production`
   - Oryx build habilitado (`SCM_DO_BUILD_DURING_DEPLOYMENT=true`)

### Variables de entorno en producción

Configurar en Azure App Service > Configuration:

| Variable                      | Descripción                          |
|-------------------------------|--------------------------------------|
| `DATABASE_URL`                | PostgreSQL de producción             |
| `REDIS_URL`                   | Redis de producción                  |
| `SECRET_KEY`                  | Clave secreta fuerte y única         |
| `ALGORITHM`                   | `HS256` (no cambiar sin migrar JWTs) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` (ajustar según necesidad)       |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                                  |
| `ENVIRONMENT`                 | `production`                         |

### Checklist pre-deploy

- [ ] `SECRET_KEY` cambiada y segura
- [ ] CORS restringido al dominio del frontend
- [ ] `ENVIRONMENT=production` (desactiva SQL echo)
- [ ] Migraciones aplicadas (`alembic upgrade head`)
- [ ] Redis accesible desde el servidor
- [ ] Secrets de GitHub configurados para Azure OIDC

---

## Base de Datos

- **Motor**: PostgreSQL (async via asyncpg)
- **Schema**: `public` (todos los modelos usan `__table_args__ = {"schema": "public"}`)
- **Pool**: `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`
- **Sesiones**: Auto-commit en éxito, rollback en excepción (ver `get_db()`)
- **Convención de nombres DB**: camelCase en columnas, snake_case en tablas (inconsistente en la DB legacy)
- **Archivo de referencia**: `schema.sql` contiene el dump completo del esquema

### Tablas principales

| Tabla                    | Descripción                        |
|--------------------------|------------------------------------|
| `roles`                  | Roles del sistema                  |
| `usuario`                | Usuarios base (auth + perfil)      |
| `administrador`          | Perfil de administrador            |
| `profesores`             | Perfil de profesor                 |
| `estudiantes`            | Perfil de estudiante               |
| `padres`                 | Padres/acudientes                  |
| `cursos`                 | Cursos académicos                  |
| `materias`               | Materias/asignaturas               |
| `asignaciones`           | Profesor ↔ Curso ↔ Materia         |
| `Horario`                | Horarios de clase                  |
| `profesores_horario`     | Profesor ↔ Horario                 |
| `especializaciones`      | Especializaciones de profesores    |
| `profesorespecializacion` | Pivot profesor ↔ especialización  |
| `asistencia`             | Registros de asistencia            |
| `notas`                  | Notas/calificaciones               |
| `periodos`               | Periodos académicos                |
| `novedades`              | Observaciones de estudiantes       |
| `reportes`               | Reportes generados                 |
| `ips` / `estudiante_ips` | Afiliaciones de salud              |
