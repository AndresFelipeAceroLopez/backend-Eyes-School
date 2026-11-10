# Planeación de correcciones — Backend (API FastAPI) · Eyes School

> **Tipo de documento:** planeación de QA. No contiene el código de las correcciones: define qué cambiar, dónde, con qué diseño para que quede testeable y qué pruebas lo demuestran.
> **Pensado para:** cualquier desarrollador o una IA que no conoce el proyecto. Todas las rutas de archivo y números de línea se verificaron contra el código el 28/10/2026.
> **Elaboró:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> **Plazo:** sprints S7 (29 oct – 6 nov 2026) y S8 (7 – 14 nov 2026). Liberación `v1.1.0` el 14 nov 2026.
> **Actualizado el 09/11/2026:** nueva sección **1.4** (el `.env` local apunta a producción) y nuevo **BE-INF-4** (dejar operativo el entorno de QA, DEF-WEB-01). **BE-01 corregido**: los commits que listaba eran equivocados y el alcance incluye `create_admin.py`, que en `main` —o sea en producción— todavía trae la `DATABASE_URL` con credenciales. La estructura se crea con Alembic, no con `schema.sql`; `CORS_ORIGINS` no la lee el backend (BE-01, punto 4). **Las correcciones BE-03 a BE-19, BE-INF-1, BE-INF-2 y BE-INF-3 ya están implementadas y probadas** en la rama `qa/implementacion-pruebas` (154 pruebas unitarias y 53 de integración, todas en verde: ver [`../Resultados/corrida-2026-11-09.md`](../Resultados/corrida-2026-11-09.md)); lo que sigue abierto es lo que no es código: BE-01 (rotación y limpieza del historial) y BE-INF-4.
> **Aviso:** este archivo del repositorio estaba desactualizado frente a la copia que circulaba por chat. Se le reincorporaron 1.4 y BE-INF-4; **falta todavía** la sección «Estado de las ramas en GitHub al 09/11/2026» y la decisión **D-3** (qué es la Web App `api-eyesschool` y si se retira su workflow), que llegaron cortadas. Al 09/11/2026 `origin` tiene `main`, `developer`, `chore/calidad-seguridad` y `fix-accesos-padre`: **`develop` no existe**, así que el punto 3 de la sección 4 sigue sin hacerse y las ramas `fix/BE-xx` de la sección 10 no tienen de dónde salir.

---

## 1. Contexto técnico

| Dato | Valor |
|---|---|
| Repositorio | `github.com/AndresFelipeAceroLopez/backend-Eyes-School` |
| Rama base | `chore/calidad-seguridad` (25 oct 2026). `main` es del 1 jul 2026, está desactualizada y es la que está en producción |
| Lenguaje y framework | Python 3.11, FastAPI + Uvicorn, Pydantic v2 |
| Datos | SQLAlchemy 2 async + asyncpg sobre PostgreSQL (Render). Esquema en `schema.sql`; migraciones Alembic en `alembic/versions/` |
| Sesiones | JWT (PyJWT): acceso 30 min, refresco 7 días, recuperación 30 min (`app/core/config.py`). Hoy los refrescos se guardan en Redis (`refresh:<jti>`). **Redis se elimina del sistema** por decisión del PO del 30/10/2026 (BE-17) |
| Archivos | Avatares en `static/avatars/`, reportes en `static/reportes/`, boletines PDF en `tmp/`. `main.py` monta `/static` como público |
| Producción | API en Azure App Service; base PostgreSQL en Render; web en Vercel; APK por GitHub Releases |
| Despliegue de la API | Azure App Service vía `.github/workflows/main_apieyeschool.yml` (push a `main`) |
| CI | GitHub Actions `.github/workflows/ci.yml`: `ruff`, `pytest --cov`, `pip-audit` |
| Prefijo | `/api/v1` |

### 1.1 Arquitectura por capas (obligatoria)

| Capa | Carpeta | Qué va ahí |
|---|---|---|
| Presentación | `app/api/v1/<módulo>.py` | Endpoints delgados: `require_roles(...)`, reciben `DbSession`/`AuthUser`, delegan al servicio |
| Aplicación | `app/application/<módulo>/schemas.py`, `service.py` | Validaciones Pydantic y reglas de negocio |
| Autorización de datos | `app/application/common/authz.py` | `assert_acceso_estudiante(db, current_user, id_estudiante)` |
| Infraestructura | `app/infrastructure/models/`, `repositories/` | Modelos SQLAlchemy y repositorios (`BaseRepository`) |
| Núcleo | `app/core/` | `config.py`, `security.py`, `dependencies.py` (`DbSession`, `RedisClient` —se elimina en BE-17—, `AuthUser`, `CurrentUser`, `require_roles`), `exceptions.py` |

- Roles (`app/application/auth/service.py`, líneas 43–46): `docente`=1, `estudiante`=2, `admin`=3, `padre`=4.
- `CurrentUser` (`app/core/dependencies.py`) tiene **solo** `id_usuario`, `id_rol` y `nombre_rol`.
- Errores (`app/core/exceptions.py`): `BusinessRuleException` 400 · `UnauthorizedException` 401 · `ForbiddenException` 403 · `NotFoundException` 404 · `ConflictException` 409. Pydantic responde 422.

### 1.2 Cómo se prueba hoy

- 26 pruebas en `tests/` (`test_app`, `test_authorization`, `test_config`, `test_register`, `test_security`). Cobertura de líneas 61 % (meta MC-01: ≥ 60 %). Todas pasan (verificado el 28/10/2026).
- `tests/conftest.py` apunta `DATABASE_URL` y `REDIS_URL` a servidores inexistentes: ninguna prueba toca datos reales. Fixture `client` con `httpx.ASGITransport`; helper `bearer(rol, id_rol, id_usuario)` para el encabezado de un usuario autenticado.
- No hay pruebas contra base de datos real.

```bash
pip install -r requirements.txt pytest pytest-asyncio pytest-cov httpx ruff
ruff check app main.py tests
pytest -q --cov=app --cov-report=term
```

### 1.3 Patrón para que cada corrección quede testeable

1. La regla de formato va en un esquema Pydantic → se prueba con `Modelo.model_validate(...)` sin base de datos.
2. La regla de negocio va en el servicio y depende de **un método con nombre claro** del repositorio → se prueba reemplazando el repositorio por un doble (clase falsa o `monkeypatch`).
3. La regla de propiedad de datos va en `authz.py` → se prueba por HTTP reemplazando la función con `monkeypatch`.
4. Lo externo (correo, Firebase, disco) se inyecta por dependencia de FastAPI → se reemplaza con `app.dependency_overrides`.
5. La consulta real se prueba aparte contra PostgreSQL (BE-INF-1).

### 1.4 Reglas para no tocar producción por error

El `.env` local del backend apunta a la base de **producción**. Varios scripts (seeds, migraciones y `qa_reset_passwords.py`) escriben en la base a la que se conecten, así que un descuido cambia datos o contraseñas reales.

1. **Ningún seed, migración ni script de QA se corre con el `.env`.** `DATABASE_URL` se fija en la terminal. La variable del proceso le gana al `.env` en `pydantic-settings` y en `load_dotenv()` sin `override`; si un script carga la configuración de otra forma, se revisa antes de correrlo.
2. **Antes de escribir se comprueba la base, no la variable:** `SELECT current_database()` debe devolver `qaeyesschool`. `ENVIRONMENT=qa` no protege: es solo una variable. El host tampoco, porque producción y QA están en el mismo Render.
3. **Mientras se trabaja con QA, el `.env` de producción sale de la carpeta del repositorio** y vuelve al terminar. No se renombra dentro de la carpeta: `.gitignore` ignora `.env`, pero un nombre como `.env.produccion` podría quedar sin ignorar y subirse con un commit.
4. **Nunca `git add -A` en el backend.** Los archivos se agregan por nombre. Antes de cada commit, `git status` y `git ls-files | Select-String "\.env"` deben mostrar solo `.env.example`.
5. Los valores de `DATABASE_URL`, contraseñas, `SECRET_KEY` y `QA_PASSWORD` no se escriben en documentos, commits, chats ni capturas. Se leen con `Read-Host`.
6. Los scripts de QA se corren desde el computador que tiene el backend, no desde la consola SSH de Azure.

**Las pruebas automatizadas ya respetan esta regla por diseño:** `tests/conftest.py` fuerza `DATABASE_URL` a una dirección inexistente antes de importar la app, y solo `TEST_DATABASE_URL` puede reemplazarla. Verificado en la corrida del 09/11/2026: las 154 unitarias corren sin base y las 53 de integración se omiten solas si `TEST_DATABASE_URL` no está definida.

---

## 2. Resumen de hallazgos

| ID | Severidad | Hallazgo | Sprint | Responsable | Antes |
|---|---|---|---|---|---|
| BE-01 | **Crítica** | El historial de git contiene un `.env` con la URL de la base de datos de Render (usuario y contraseña) y la `SECRET_KEY` | S7, día 1 | Andrés Acero | nuevo |
| BE-03 | **Crítica** | `GET /dashboard/estudiante` falla siempre con error 500 (también en producción) | S7, día 1 | Andrés Acero | nuevo |
| BE-04 | **Crítica** | Padre o estudiante pueden leer la asistencia de cualquier estudiante | S7 | Andrés Acero | COR-03 |
| BE-05 | Media | Un padre puede leer el vínculo de cualquier otro padre (`GET /padres/{id}`) | S7 | Andrés Acero | nuevo |
| BE-06 | Alta | La API acepta notas de 0 a 10 | S7 | Andrés Acero | COR-01 |
| BE-07 | Alta | Un padre con dos hijos provoca error 500 | S8 | Andrés Acero | COR-05 |
| BE-08 | Alta | Se pueden registrar dos entradas o dos salidas el mismo día | S7 | Andrés Acero | COR-02 |
| BE-09 | Alta | La API no aplica la política de contraseña | S7 | Andrés Acero | COR-04 |
| BE-10 | Media | Quién registró asistencia, notas y novedades lo manda el cliente (`registrado_por`) | S7 | Andrés Acero | nuevo |
| BE-11 | Media | Un docente puede calificar cualquier materia y editar o borrar novedades de otros | S8 | Andrés Acero | nuevo |
| BE-12 | Media | El correo distingue mayúsculas y no se valida su formato | S7 | Andrés Acero | nuevo |
| BE-13 | Media | Sesión: un usuario desactivado sigue entrando 7 días; el enlace de recuperación se puede reutilizar; no hay prueba del cierre de sesión | S8 | Andrés Acero | COR-06 ampliado |
| BE-14 | Media | Avatares sin validar tipo, extensión ni tamaño, servidos como públicos | S7 | Andrés Acero | nuevo |
| BE-15 | Media | Reportes accesibles por URL pública, boletines PDF que nunca se borran y archivos en disco efímero de Azure | S8 | Andrés Acero | nuevo |
| BE-16 | Media | Sin límite de intentos de inicio de sesión | S8 | Andrés Acero | nuevo |
| BE-INF-1 | Alta | Pruebas contra PostgreSQL real | S7–S8 | Samuel Sierra + Andrés | COR-12 |
| BE-INF-2 | Alta | Datos de QA con contraseñas conocidas | S7 | Samuel Sierra | COR-13 |
| BE-INF-3 | Alta | SonarQube Cloud y detección de secretos en CI | S7 | Samuel Sierra + Andrés | COR-14 |
| BE-17 | Alta | Retirar Redis y guardar las sesiones en PostgreSQL | S7 | Andrés Acero | nuevo (decisión PO) |
| BE-18 | Alta | Las notificaciones push al acudiente no se envían: no existe el emisor | S8 | Andrés Acero | COR-15 |
| BE-19 | Media | El boletín de un estudiante sin notas sale como PDF vacío en vez del mensaje del CA | S8 | Andrés Acero | nuevo (H-03 del PR-02) |

---

## 3. Comportamiento por diseño (no es defecto)

**Registro público de padres.** Cualquier persona puede registrarse como padre o acudiente desde la web o la app y quedar vinculada al estudiante que indique, con acceso inmediato a sus datos. Es el objetivo del registro (decisión del PO del 30/10/2026). Antes figuraba como BE-02 y se retiró de esta planeación. Durante las pruebas no se registra como defecto; se prueba como funcionalidad:

| Prueba (`tests/test_register.py`) | Entrada | Resultado esperado |
|---|---|---|
| Registro de padre | `POST /auth/register` con rol 4, `id_estudiante_vinculado` y `parentesco` válidos (repositorios dobles) | 201; usuario activo y vínculo creado |
| Padre sin vínculo | Rol 4 sin `id_estudiante_vinculado` | 201; usuario creado sin vínculo y las pantallas muestran «Sin estudiante vinculado» |
| Acceso al hijo vinculado | `assert_acceso_estudiante` con el estudiante vinculado | Permitido |
| Acceso a otro estudiante | Otro `id_estudiante` | 403 (lo garantizan BE-04 y BE-07) |

## 4. Acciones del día 1 (29 oct 2026)

Estas no esperan el ciclo normal de PR:

1. **BE-01:** rotar la contraseña de la base de Render y la `SECRET_KEY` de Azure.
2. **BE-03:** corregir el error 500 del inicio del estudiante y el padre, que hoy está roto en producción.
3. Ordenar ramas: crear `develop` desde `developer` si no existe y hacer merge de `chore/calidad-seguridad` a `develop`.

---

## 5. Correcciones

### BE-01 · Secretos en el historial de git — Crítica

**Evidencia (corregida el 09/11/2026 con `gitleaks 8.24.2`; los commits que decía antes este documento —`847a48c` y `c5621f7`— no son los correctos).** El escaneo del historial con la regla propia de BE-SA-2 devuelve **6 hallazgos en 5 commits**:

| Regla | Archivo | Commit | Fecha | Autor |
|---|---|---|---|---|
| `url-conexion-con-credenciales` | `.env` | `6fdf2cc` | 12/06/2026 | NoaTakeshi |
| `secret-key-en-env` | `.env` | `ccaec1c` | 12/06/2026 | NoaTakeshi |
| `url-conexion-con-credenciales` | `.env` | `db5565c` | 22/06/2026 | NoaTakeshi |
| `url-conexion-con-credenciales` | `.env` | `e21775a` | 24/06/2026 | Zharick Rodriguez |
| `url-conexion-con-credenciales` | **`create_admin.py`** | `6fdf2cc` | 12/06/2026 | NoaTakeshi |
| `url-conexion-con-credenciales` | **`create_admin.py`** | `476c0de` | 02/07/2026 | NoaTakeshi |

El `.env` del historial trae `DATABASE_URL` con host de Render **y usuario:contraseña**, y una `SECRET_KEY`. Los valores no se reproducen en este documento (el reporte se genera con `--redact`). Hoy `.env` está en `.gitignore`, pero el historial lo conserva.

**Hallazgo nuevo que amplía BE-01:** el mismo `DATABASE_URL` con credenciales estaba **escrito dentro de `create_admin.py`**, y el commit `476c0de` (2 jul 2026) es el que está en `main`, es decir **el archivo que hoy corre en producción todavía trae la URL embebida**. En la rama de trabajo ya está corregido (línea 17 la lee de `settings`), pero la corrección tiene que llegar a `main`. Los valores no se reproducen aquí.

**Impacto.** Quien tenga acceso al repositorio puede conectarse a la base de datos con datos de menores. Si la `SECRET_KEY` sigue en producción, también puede firmar tokens JWT como administrador.

**Acciones (no es código):**
1. En Render: cambiar la contraseña del usuario de la base y actualizar `DATABASE_URL` en Azure App Service → Configuración.
2. En Azure: generar una `SECRET_KEY` nueva de 64 caracteres o más (`python -c "import secrets; print(secrets.token_urlsafe(64))"`). Esto cierra todas las sesiones activas.
3. Verificar en Azure que `ENVIRONMENT=production`. Con eso la API no arranca con la clave por defecto (`app/core/config.py`, línea 41).
4. Verificar que `CORS_ORIGINS` en Azure sea la lista exacta de dominios de la web y no `*`.
5. Verificar que los usuarios de `seed_data.sql` en producción no conserven las contraseñas escritas en el comentario del archivo (líneas 29–33). Si las conservan, cambiarlas y quitar el comentario del repositorio.
6. **Llevar a `main` la versión de `create_admin.py` que lee la URL de `settings`** (hallazgo del 09/11/2026). Es parte del hotfix de BE-03, que también sale desde `main`.
7. Opcional, coordinado con todo el equipo: limpiar el historial con `git filter-repo --invert-paths --path .env --path create_admin.py` y forzar el push. **Ojo: `--path .env` por sí solo no alcanza**, porque `create_admin.py` también trae credenciales en `6fdf2cc` y `476c0de`; y como ese archivo sigue en uso, hay que volver a agregarlo limpio después del filtrado. Rotar los secretos es lo que protege; limpiar el historial no reemplaza la rotación.

**Prueba que lo protege a futuro.** En `ci.yml`, un paso de `gitleaks` (`gitleaks/gitleaks-action`) que falle si un commit trae secretos (ver BE-INF-3). La prueba existente `tests/test_config.py` debe seguir verificando que en producción no se acepta la clave por defecto.

**Aceptado cuando:** la contraseña vieja de la base ya no conecta, la `SECRET_KEY` cambió, el CI tiene `gitleaks` en verde y queda registro de la rotación en el PR-07.

---

### BE-03 · El inicio del estudiante y del padre falla siempre — Crítica

**Evidencia (verificada en ejecución el 28/10/2026).** `app/api/v1/dashboard.py`, línea 24: `if "padre" in current_user.roles:`. `CurrentUser` no tiene el atributo `roles`, así que `GET /api/v1/dashboard/estudiante` lanza `AttributeError: 'CurrentUser' object has no attribute 'roles'` y la API responde 500. Está igual en `main`, así que la producción tiene este error desde el commit `476c0de` (1 jul 2026). La web (`src/services/dashboard/dashboardService.ts`, líneas 182 y 241) y la app (`lib/features/dashboard/data/dashboard_api.dart`, línea 16) llaman este endpoint en el inicio del estudiante.

**Diseño:** cambiar la condición a `current_user.nombre_rol == "padre"`. Además, sacar la resolución "¿qué estudiante corresponde a este usuario?" a una función del servicio (`DashboardService.resolver_estudiante(current_user)`), que BE-07 extiende para varios hijos.

| Prueba (`tests/test_dashboard.py`) | Entrada | Resultado esperado |
|---|---|---|
| Estudiante | `bearer("estudiante", 2)`, servicio y repositorio dobles | 200 (hoy falla con `AttributeError`) |
| Padre | `bearer("padre", 4)`, vínculo doble | 200 con el estudiante vinculado |
| Docente | `bearer("docente", 1)` | 403 |

**Aceptado cuando:** las 3 pruebas pasan, la corrección llega a producción con un hotfix (`hotfix/BE-03-dashboard-estudiante` desde `main`, también fusionado a `develop`) y el inicio del estudiante carga en la web y en la app.

---

### BE-04 · Padre o estudiante leen la asistencia de cualquier estudiante — Crítica

**Evidencia.** `app/api/v1/asistencia.py`: `GET ""` (línea 16) y `GET "/{id_asistencia}"` (línea 33) permiten los roles `padre` y `estudiante`, pero no reciben `current_user` ni llaman `assert_acceso_estudiante`. `GET /api/v1/asistencia?id_estudiante=<otro>` devuelve la asistencia de un menor ajeno. Los endpoints `/estudiantes/{id}/...` sí la llaman.

**Diseño:**
- Los dos endpoints reciben `current_user: AuthUser`.
- En el listado, si el rol es `padre` o `estudiante`, `id_estudiante` es obligatorio (si falta, `BusinessRuleException` 400) y se llama `assert_acceso_estudiante` antes de consultar.
- En el detalle, se carga el registro y se valida con su `id_estudiante`.
- Admin y docente no cambian.

| Prueba (`tests/test_authorization.py`) | Usuario | Resultado esperado |
|---|---|---|
| Padre pide otro estudiante | `bearer("padre", 4)`, `?id_estudiante=99`, `assert_acceso_estudiante` lanza 403 | 403 |
| Padre sin filtro | `bearer("padre", 4)` sin `id_estudiante` | 400 |
| Estudiante, su propio registro | `assert_acceso_estudiante` no lanza; servicio doble | 200 |
| Detalle ajeno | `GET /asistencia/5` cuyo `id_estudiante` no es del padre | 403 |
| Admin | `bearer("admin", 3)` sin filtro | 200 |

**Aceptado cuando:** pasan las 5 pruebas y el riesgo R-01 del PR-01 queda mitigado en el PR-06.

---

### BE-05 · Un padre lee el vínculo de otro padre — Media

**Evidencia.** `app/api/v1/padres.py`, línea 64: `GET /padres/{id_padre}` permite `admin` y `padre` y devuelve cualquier registro (`id_usuario`, `id_estudiante`, `parentesco`, `ocupacion`) sin comparar con el usuario.

**Diseño:** recibir `current_user`; si el rol es `padre` y `item.id_usuario != current_user.id_usuario`, lanzar `ForbiddenException`.

| Prueba (`tests/test_authorization.py`) | Resultado esperado |
|---|---|
| Padre pide su propio registro | 200 |
| Padre pide el de otro | 403 |
| Admin pide cualquiera | 200 |

---

### BE-06 · Notas fuera de la escala 0.0–5.0 — Alta

**Evidencia.** `app/application/notas/schemas.py`, líneas 11 y 17: `nota: Annotated[float, Field(ge=0, le=10)]` en `NotaCreate` y `NotaUpdate`. La web (`NotasClient.tsx`, línea 443) y la app (`validators.dart`, `gradeScore`) solo permiten 0.0–5.0. Columna `Numeric(4, 2)`.

**Diseño:** constantes `NOTA_MIN = 0.0` y `NOTA_MAX = 5.0` en el mismo archivo, usadas en los dos `Field(ge=..., le=...)`. Es opcional limitar a un decimal con `field_validator`, como la app.

| Prueba (`tests/test_notas_validacion.py`) | Entrada | Resultado esperado |
|---|---|---|
| Límites válidos | 0.0, 0.1, 4.9, 5.0 | Aceptadas |
| Límites inválidos | -0.1, 5.1 | `ValidationError` |
| Actualización | `NotaUpdate(nota=5.1)` | `ValidationError` |
| HTTP | `POST /notas` con `bearer("docente", 1)` y nota 5.1 | 422 |

---

### BE-07 · Padre con varios hijos — Alta

**Evidencia.** La tabla `padres` (`PadreModel`, `app/infrastructure/models/actores.py`, línea 68) guarda una fila por vínculo. Cuatro lugares usan `scalar_one_or_none()` y con dos filas lanzan `MultipleResultsFound` (500):
- `PadreRepository.get_by_usuario` (`actores_repository.py`, líneas 111–115)
- `assert_acceso_estudiante` (`authz.py`, líneas 29–33)
- `GET /padres/me` (`padres.py`, línea 33)
- `DashboardService.get_padre_dashboard` (`dashboard/service.py`, líneas 120–125)

El endpoint `GET /dashboard/estudiante` (BE-03) tiene la misma consulta.

**Diseño:**
- `PadreRepository.list_by_usuario(id_usuario) -> list[PadreModel]` e `ids_estudiantes(id_usuario) -> set[int]`.
- `assert_acceso_estudiante` para padre: permitir si `id_estudiante in ids_estudiantes(...)`.
- Endpoint nuevo `GET /api/v1/padres/me/hijos` (rol padre) → `list[HijoOut]` con `id_estudiante`, `nombre_estudiante`, `documento_estudiante`, `parentesco` y `id_curso_actual`.
- `GET /padres/me`, `GET /dashboard/padre` y `GET /dashboard/estudiante` aceptan el parámetro opcional `id_estudiante`. Si llega, se valida; si no, se usa el primer hijo, para no romper los clientes actuales.
- `get_by_usuario` pasa a devolver el primer vínculo (`.scalars().first()`).

| Prueba (`tests/test_padre_varios_hijos.py`) | Doble | Resultado esperado |
|---|---|---|
| Primer hijo | `ids_estudiantes` → {10, 11}; pide 10 | Permitido |
| Segundo hijo | pide 11 | Permitido |
| Tercero | pide 12 | 403 |
| Lista | `list_by_usuario` → 2 vínculos | `GET /padres/me/hijos` → 200 con 2 |
| Sin vínculos | `[]` | 200 con lista vacía |
| Dashboard ajeno | `GET /dashboard/padre?id_estudiante=12` | 403 |

**Dependencias:** la web (WEB-03) y la app (APP-03) lo consumen. Debe estar en `develop` en los primeros días del S8.

---

### BE-08 · Entradas o salidas duplicadas — Alta

**Evidencia.** `AsistenciaService.create` (`app/application/asistencia/service.py`, líneas 48–50) guarda sin revisar duplicados. Solo la cola de la app deduplica (`attendance_queue.dart`, que ya trata un 409 como entregado). El registro masivo de la web envía y cuenta errores sin saber si fueron duplicados.

**Diseño:**
- Método nuevo `AsistenciaRepository.exists_for_day(id_estudiante, fecha, tipo) -> bool`, que solo cuenta registros con `activo == True`.
- En el servicio, la constante `TIPOS_UNICOS_POR_DIA = ("entrada", "salida")`. Si ya existe, `ConflictException("Ya existe un registro de <tipo> para este estudiante en esta fecha")`. El tipo `clase` no se restringe.
- Opcional, como defensa en la base: índice único parcial con migración Alembic `UNIQUE (idEstudiante, fecha, tipo) WHERE tipo IN ('entrada','salida') AND activo`.

| Prueba (`tests/test_asistencia_duplicados.py`) | Doble | Resultado esperado |
|---|---|---|
| Primera entrada | `exists_for_day` → False | Se guarda |
| Segunda entrada | → True | 409, no se llama `create` |
| Salida tras entrada | `exists_for_day(…, "salida")` → False | Se guarda |
| Dos `clase` | — | Se guardan sin consultar |
| Salida sin entrada | `exists_for_day(…, "entrada")` → False al pedir una salida | 400 «No hay entrada registrada hoy para este estudiante»; no se llama `create` |

**Decisión del PO (30/10/2026):** una salida sin entrada previa ese día se rechaza con `BusinessRuleException` (400). El admin corrige esos casos desde el registro masivo. Se agrega al servicio con el mismo método `exists_for_day`.

---

### BE-09 · La API no aplica la política de contraseña — Alta

**Evidencia.**
- `UsuarioCreate.password` y `UsuarioUpdate.password` (`app/application/usuarios/schemas.py`, líneas 24 y 38) aceptan cualquier texto o `None`. `RegisterRequest` hereda de `UsuarioCreate`.
- `AuthService.reset_password` (líneas 212–213) solo pide 8 caracteres.
- La web exige 5 reglas (`src/lib/utils/password.ts`); la app, 8 caracteres.

**Diseño:**
- Módulo `app/core/password_policy.py` con `validar_password(pwd) -> list[str]`, que devuelve las reglas incumplidas: mínimo 8, mayúscula, minúscula, número, carácter especial. Son las mismas expresiones que la web.
- `field_validator` en `UsuarioCreate.password` y `UsuarioUpdate.password` (si no es `None`) y en `ResetPasswordRequest.new_password` (`app/application/auth/schemas.py`).
- Quitar la comprobación suelta de `reset_password`.
- `PUT /usuarios/{id}` de un no-admin que cambia su propia contraseña debe exigir la contraseña actual (campo `password_actual`). Hoy basta con tener un token válido.

| Prueba (`tests/test_password_policy.py`) | Entrada | Resultado esperado |
|---|---|---|
| Cumple | `Colegio#2026` | Lista vacía |
| Corta | `Ab1#` | Falla longitud |
| Sin mayúscula | `colegio#2026` | Falla mayúscula |
| Sin minúscula | `COLEGIO#2026` | Falla minúscula |
| Sin número | `Colegio#ocho` | Falla número |
| Sin especial | `Colegio2026` | Falla especial |
| Registro HTTP | `POST /auth/register` con `Colegio2026` | 422 |
| Cambio sin contraseña actual | `PUT /usuarios/{propio}` con `password` y sin `password_actual` | 400 |

Son los mismos casos que `tests/password.test.ts` de la web y `validators_test.dart` de la app.

---

### BE-10 · `registrado_por` lo decide el cliente — Media

**Evidencia.** `registrado_por: int` llega en el cuerpo de `AsistenciaCreate` (`asistencia/schemas.py`, líneas 12 y 19), `NotaCreate` (`notas/schemas.py`, línea 13) y `NovedadCreate` (`novedades/schemas.py`, línea 30). Un docente puede registrar una nota o novedad a nombre de otro docente.

**Diseño:** los endpoints `POST` reciben `current_user` y el servicio fija `registrado_por = current_user.id_usuario`. El campo sale de los esquemas de entrada (se mantiene en los de salida). Para no romper clientes, Pydantic ignora el campo si llega (configuración `extra="ignore"`, que es el valor por defecto).

| Prueba | Resultado esperado |
|---|---|
| `POST /notas` con `registrado_por=999` como docente 7 | Se guarda con `registrado_por=7` (servicio doble que captura los datos) |
| Igual para asistencia y novedades | Mismo comportamiento |

---

### BE-11 · Permisos del docente sin límite de asignación — Media

**Evidencia.**
- `NotaService.create`, `update` y `delete` no revisan si el docente tiene asignada la materia y el curso del estudiante. La tabla `asignaciones` (`AsignacionModel`, `academico.py`, líneas 55–65: `id_profesor`, `id_curso`, `id_materia`, `activo`) ya existe.
- `NovedadService.update` y `delete` (`novedades/service.py`, líneas 68–79) permiten a cualquier docente editar o borrar novedades de otros.

**Diseño:**
- Método `AsignacionRepository.docente_dicta(id_profesor, id_materia, id_curso) -> bool`. Antes de crear o modificar una nota, el servicio obtiene el curso del estudiante y valida; si no corresponde, `ForbiddenException`.
- Novedades: solo el autor (`registrado_por`) o un admin pueden editar o borrar.
- **Decisión del PO (30/10/2026):** el docente solo lee las notas de los cursos que dicta. `GET /notas` filtra por sus asignaciones cuando el rol es docente.

| Prueba | Resultado esperado |
|---|---|
| Docente con asignación crea nota | 201 |
| Docente sin asignación crea nota | 403 |
| Docente edita novedad ajena | 403 |
| Admin edita novedad ajena | 200 |

---

### BE-12 · Correo sin normalizar ni validar — Media

**Evidencia.**
- `UsuarioRepository.get_by_correo` y `correo_exists` (`usuario_repository.py`, líneas 28–33 y 67–71) comparan el correo tal cual.
- `forgot_password` usa `correo.strip().lower()`; la web pasa el correo a minúsculas al iniciar sesión y registrarse; la app solo hace `trim()`.
- Resultado: quien se registra desde la app con `Ana@x.com` no puede iniciar sesión desde la web, y pueden existir `ana@x.com` y `Ana@x.com` como cuentas distintas.
- `correo` es `str` sin validar el formato.

**Diseño:**
- `field_validator` que haga `strip().lower()` en `UsuarioCreate.correo`, `UsuarioUpdate.correo`, `LoginRequest.correo` y `ForgotPasswordRequest.correo`.
- Validar formato con `EmailStr` (agregar `email-validator` a `requirements.txt`).
- Script de datos para QA y producción: primero reportar correos que choquen en minúsculas; después pasarlos a minúsculas. Para que no vuelva a pasar, migración Alembic con índice único sobre `lower(correo)`.

| Prueba | Resultado esperado |
|---|---|
| `LoginRequest(correo=" Ana@X.com ")` | `ana@x.com` |
| `UsuarioCreate(correo="no-es-correo")` | `ValidationError` |
| Integración (BE-INF-1): registrar `Ana@x.com` cuando existe `ana@x.com` | 409 |

---

### BE-13 · Sesión y cierre de sesión — Media (depende de BE-17)

**Evidencia en `app/application/auth/service.py`:**
- `refresh` (líneas 149–165) no revisa si el usuario sigue activo. Si un admin desactiva una cuenta, el dueño sigue renovando su acceso hasta 7 días.
- `reset_password` (líneas 203–220) acepta el mismo enlace varias veces durante 30 minutos.
- La revocación de sesiones depende hoy de Redis, que se elimina (BE-17). Ninguna prueba ejecuta `login → refresh → logout → refresh`.

**Diseño (sobre la tabla de sesiones de BE-17):**
- `refresh` exige que el `jti` exista en `sesiones_refresco`, no esté revocado ni vencido, y que el usuario tenga `estado = True`. Si falla cualquiera de las tres, responde 401.
- Al desactivar un usuario (`UsuarioService.toggle_estado` con `estado=False`) se revocan todas sus sesiones con `SesionRepository.revocar_todas(id_usuario)`.
- Enlace de recuperación de un solo uso, sin almacenamiento extra:
    - Columna nueva `password_actualizada` (timestamp) en `usuario`, con migración Alembic.
    - El token de recuperación incluye ese valor (`pwd_ts`) y `reset_password` lo compara con el actual.
    - Al cambiar la contraseña la columna se actualiza, así que un segundo uso del mismo enlace responde 401.
- **Por qué queda testeable:** las tres reglas dependen de métodos de `SesionRepository` y `UsuarioRepository`, que se reemplazan por dobles.

| Prueba (`tests/test_sesion.py`) | Pasos | Resultado esperado |
|---|---|---|
| Refresco válido | Sesión activa en el repositorio doble, `POST /auth/refresh` | 200 con `access_token` |
| Cierre de sesión | `POST /auth/logout`, luego `POST /auth/refresh` con el mismo token | 204 y luego 401 |
| Usuario desactivado | Sesión activa de un usuario con `estado=False` | 401 |
| Desactivación revoca | `PATCH /usuarios/{id}/estado?estado=false` como admin | Se llama `revocar_todas(id)` |
| Enlace reutilizado | `reset-password` dos veces con el mismo token | 200 y luego 401 |
| Integración (BE-INF-1) | Login real → logout → refresh contra PostgreSQL | 401 en el último paso |

---

### BE-14 · Avatares sin validar — Media

**Evidencia.** `AuthService.upload_avatar` (`auth/service.py`, líneas 236–252):
- Confía en `content_type`, que lo envía el cliente.
- Toma la extensión del nombre del archivo, así que se puede subir `.html` o `.svg`.
- No limita el tamaño.
- Guarda en `static/avatars/`, servido públicamente por `main.py` desde el mismo dominio de la API. Un `.html` o `.svg` con script se puede servir como página (XSS almacenado).

**Diseño:**
- Lista blanca de extensiones `{jpg, jpeg, png, webp}` y verificación del contenido real abriéndolo con Pillow (ya instalado por `fpdf2`; agregarlo explícito a `requirements.txt`).
- Máximo 2 MB.
- La extensión se decide por el formato detectado, no por el nombre.

| Prueba (`tests/test_avatar.py`, disco en `tmp_path` con `monkeypatch`) | Resultado esperado |
|---|---|
| PNG real de 10 KB | 200 y archivo `.png` |
| Texto con nombre `foto.png` | 400 |
| `pagina.html` con `content-type: image/png` | 400 |
| 3 MB | 400 |

---

### BE-15 · Archivos públicos, temporales que no se borran y disco efímero — Media

**Evidencia.**
- `main.py` monta `/static` completo. Los reportes (`static/reportes/<uuid>.pdf`) se descargan sin token si alguien tiene la URL, aunque `GET /reportes/{id}/archivo` exige rol admin.
- `NotaService.generate_boletin_pdf` (`notas/service.py`, líneas 136–139) escribe en `tmp/` y nunca borra.
- Azure App Service no garantiza el disco local entre despliegues o reinicios: avatares y reportes se pueden perder.

**Diseño:**
- Montar solo `static/avatars` como público. Los reportes se sirven únicamente por el endpoint autenticado.
- El boletín se genera en memoria (`pdf.output()` devuelve bytes) y se responde con `Response(content=..., media_type="application/pdf")`, o se borra con `BackgroundTask` después de enviarlo.
- **Decisión del equipo (S8 o siguiente versión):** mover archivos a Azure Blob Storage detrás de una interfaz `AlmacenArchivos` con implementación local (pruebas) y Blob (producción).

| Prueba | Resultado esperado |
|---|---|
| `GET /static/reportes/x.pdf` | 404 |
| `GET /notas/estudiantes/{id}/boletin/pdf` con servicio doble | 200 y no queda archivo en `tmp/` |

---

### BE-16 · Sin límite de intentos de inicio de sesión — Media

**Evidencia.** `AuthService.login` (líneas 124–147) no cuenta intentos fallidos. Los requisitos no funcionales piden proteger las credenciales.

**Diseño (sin Redis):**
- Columnas nuevas en `usuario`: `intentos_fallidos` (entero) y `bloqueado_hasta` (timestamp), con migración Alembic.
- Métodos `UsuarioRepository.registrar_fallo(id)` y `reiniciar_fallos(id)`.
- Con 5 fallos en 15 minutos, `bloqueado_hasta = ahora + 15 min` y cualquier intento hasta esa hora responde 429 «Demasiados intentos, espera 15 minutos».
- Un acceso exitoso reinicia el contador. El mensaje de credenciales inválidas sigue siendo genérico.
- La hora llega al servicio como dependencia (`reloj: Callable[[], datetime]`) para que las pruebas la controlen.

| Prueba (repositorio doble y reloj fijo) | Resultado esperado |
|---|---|
| 5 fallos seguidos | El 6.º intento → 429, aunque la contraseña sea correcta |
| Fallo, fallo, éxito | El contador vuelve a 0 |
| Bloqueado y pasan 16 min (reloj adelantado) | Puede volver a intentar |

---

### BE-17 · Retirar Redis — Alta (decisión del PO del 30/10/2026)

**Evidencia de dónde está Redis hoy:**
- `requirements.txt`: `redis==8.0.0` y `hiredis==3.4.0`.
- `app/core/redis.py`: `get_redis`.
- `app/core/dependencies.py`: `RedisClient`.
- `app/api/v1/auth.py`: lo inyecta en login, refresh y logout.
- `app/application/auth/service.py`: lo usa en `login` (guarda `refresh:<jti>`, línea 142 si falla), `refresh` (revisa, línea 162) y `logout` (borra, línea 178).
- `app/core/config.py`: `REDIS_URL`.
- `.env.example` y `tests/conftest.py`.

**Diseño:**
- Tabla nueva `sesiones_refresco` con migración Alembic: `id`, `jti` (único), `id_usuario` (FK), `emitido`, `expira`, `revocado` (booleano, por defecto falso).
- `SesionRepository` en `app/infrastructure/repositories/` con `crear(jti, id_usuario, expira)`, `obtener_activa(jti)`, `revocar(jti)` y `revocar_todas(id_usuario)`.
- `AuthService` recibe `SesionRepository` en lugar de Redis: `login` crea la sesión, `refresh` la consulta (BE-13) y `logout` la revoca.
- Borrar `app/core/redis.py`, `RedisClient`, `REDIS_URL`, las dos dependencias de `requirements.txt`, la variable en `.env.example`, la de `tests/conftest.py` y el ajuste `REDIS_URL` de Azure.
- Limpieza: tarea programada o consulta al iniciar sesión que borre sesiones vencidas hace más de 30 días.
- Actualizar el PR-01: Redis deja de ser un componente del sistema.

| Prueba | Resultado esperado |
|---|---|
| `login` con repositorio doble | Se llama `crear` con el `jti` del token emitido |
| `refresh` con sesión revocada | 401 |
| `logout` | Se llama `revocar(jti)` |
| Integración (BE-INF-1) | Login, refresh y logout funcionan contra PostgreSQL sin ningún Redis |
| Búsqueda de restos | `grep -ri redis app requirements.txt tests` no devuelve nada (paso del CI) |

---

### BE-18 · Las notificaciones push no se envían — Alta

**Evidencia (verificada en todas las ramas el 30/10/2026).**
- La app **sí recibe** notificaciones: `push_notification_service.dart` escucha `FirebaseMessaging.onMessage` (línea 111) y obtiene el token del teléfono (línea 94).
- Pero el token solo se imprime y nunca se envía a la API.
- En la API no existe `firebase-admin`, ni tabla de dispositivos, ni envío al crear una novedad (`NovedadService.create`, líneas 64–66).
- Hoy una notificación solo llegaría si alguien la envía a mano desde la consola de Firebase con el token del log.
- El PBI 92 y la US027 lo piden. Los casos del PR-02 se escriben contra ese comportamiento y van a fallar hasta corregir esto.

**Diseño:**
- Tabla `dispositivos` (`id`, `id_usuario`, `token_fcm` único, `plataforma`, `actualizado`) con migración y endpoint `POST /api/v1/dispositivos` (cualquier rol autenticado; si el token ya existe lo reasigna al usuario actual). `DELETE /api/v1/dispositivos/{token}` al cerrar sesión.
- Interfaz `Notificador` en `app/application/common/notificador.py` con `enviar(tokens, titulo, cuerpo, datos)`. Implementación `NotificadorFirebase` en `app/infrastructure/` con `firebase-admin`. La credencial de la cuenta de servicio va en el ajuste `FIREBASE_CREDENTIALS_JSON` de Azure, **nunca en el repositorio**.
- `NovedadService` recibe el `Notificador` por constructor. Después de guardar una novedad, busca los padres del estudiante (`PadreRepository.get_by_estudiante`) y sus tokens, y envía «Nueva novedad de <estudiante>». Si el envío falla, la novedad se guarda igual y se registra el error.
- Contraparte en la app: APP-08.

| Prueba | Resultado esperado |
|---|---|
| Registrar dispositivo | `POST /dispositivos` → 201; repetirlo no duplica |
| Crear novedad (`NotificadorFalso` que guarda los envíos) | Un envío solo a los tokens de los padres de ese estudiante |
| Estudiante sin padres o sin tokens | Novedad 201 y ningún envío |
| Firebase falla (`NotificadorFalso` que lanza error) | Novedad 201; error registrado |
| Dispositivo real (PR-06) | En el POCO X7 con sesión de padre, registrar una novedad desde la web → llega la notificación |

---

### BE-19 · Boletín sin notas — Media (decisión del PO del 30/10/2026)

**Evidencia.** `NotaService.generate_boletin_pdf` (`app/application/notas/service.py`) genera el PDF aunque el estudiante no tenga notas: sale una hoja con «Promedio general: N/A». La US014 (CA-US014.3) y el PBI 15 (CA-PBI15.3) piden el mensaje «No hay datos disponibles para generar el boletín.». Ese texto no existe en ningún repositorio (hallazgo H-03 del PR-02).

**Diseño:**
- Si la consulta de notas del estudiante viene vacía, el servicio lanza `NotFoundException("No hay datos disponibles para generar el boletín.")` antes de crear el PDF. El endpoint responde 404 con ese `detail`.
- Se hace junto con BE-15 (boletín en memoria), porque tocan la misma función.
- La web lo muestra con WEB-09. La app ya muestra el mensaje que llega en `AppFailure` (`report_card_download.dart`, línea 72); solo se verifica.

| Prueba | Resultado esperado |
|---|---|
| Servicio con repositorio doble sin notas | `NotFoundException` con el texto exacto; no se genera PDF |
| HTTP `GET /notas/estudiantes/{id}/boletin/pdf` con estudiante sin notas | 404 con el mensaje |
| Estudiante con notas | 200 `application/pdf` (sin cambios) |

---

## 6. Infraestructura de pruebas

### BE-INF-1 · Pruebas contra PostgreSQL real (S7 montaje, S8 pruebas)

- Carpeta `tests/integration/` con marca `@pytest.mark.integration`, registrada en `pyproject.toml`. Por defecto `pytest -m "not integration"`.
- Fixture de sesión: crea la base con `schema.sql`, carga `seed_data.sql` y corre cada prueba en una transacción que se revierte al final.
- `ci.yml`: servicio `postgres:16` y paso `pytest -m integration` con `DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/eyes_test`.
- Local: `docker run -p 5432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=eyes_test postgres:16`.
- Primeras pruebas: correo duplicado → 409 (BE-12), entrada duplicada → 409 (BE-08), padre ajeno → 403 (BE-04), padre con dos hijos (BE-07), nota única por materia y periodo → 409 (`NotaService.create`).

### BE-INF-2 · Datos de QA (S7)

- `seed_data.sql` crea 10 usuarios de los cuatro roles (por ejemplo `admin@eyesschool.edu.co`). Las contraseñas se guardan cifradas, **pero el encabezado del archivo (líneas 29–33) las trae en texto plano en un comentario** para cuatro usuarios, incluido el admin. Quitar ese comentario y verificar que la base de producción no use esas contraseñas (ver hallazgo H-08 del PR-02). `seed_estudiantes_sinteticos.sql` crea 10 estudiantes por curso con una contraseña común escrita en el propio script.
- El seed ya trae un padre con **dos** hijos: `rosa.perez@gmail.com` (usuario 4) vinculado a los estudiantes 1 y 3 (`seed_data.sql`, líneas 235–238). Por eso BE-07 ya ocurre con los datos de prueba.
- Script `scripts/qa_reset_passwords.py`:
  - Solo corre con `ENVIRONMENT=qa`.
  - Lee `QA_PASSWORD`, que debe cumplir BE-09.
  - La asigna con `hash_password` a los usuarios de `seed_data.sql`.
  - Imprime correo · rol sin la contraseña.
- Orden de carga: `schema.sql` → `seed_data.sql` → `seed_estudiantes_sinteticos.sql` → script.
- Prueba: con `ENVIRONMENT=production` el script no hace nada.

### BE-INF-3 · SonarQube Cloud y secretos (S7)

- `ci.yml`: `--cov-report=xml`, paso `SonarSource/sonarqube-scan-action` con secreto `SONAR_TOKEN` y paso `gitleaks/gitleaks-action`.
- `sonar-project.properties`: `sonar.sources=app`, `sonar.tests=tests`, `sonar.python.coverage.reportPaths=coverage.xml`.
- Protección de rama en `develop` y `main`: CI en verde y Quality Gate aprobado para hacer merge.

**Estado al 09/11/2026:** `sonar-project.properties` ya está completo (`sonar.sources=app,main.py`, `sonar.tests=tests`, `sonar.exclusions=alembic/**,static/**,scripts/**`, `sonar.python.version=3.11`, `coverage.xml`) y `.gitleaks.toml` tiene la regla propia, **ya validada** (ver BE-01). Falta solo lo que no está en el repositorio: importar el proyecto en SonarQube Cloud y crear el secreto `SONAR_TOKEN`.

### BE-INF-4 · Entorno de QA operativo (S8, lo primero)

**Evidencia.** El 05/11/2026 la Web App `apieyeschool-q` ya no estaba pausada (`/docs` → 200), pero `GET /cursos` y el login del admin respondían **500** (un intento dio **502**), mientras que un cuerpo inválido respondía **422**. Un login con un correo que no existe también da 500 en vez de 401. La API arranca y valida, pero falla en cuanto consulta la base: es DEF-WEB-01 del PR-07 (aquí **DEF-020**). Bloquea 8 casos de integración y 23 de los 24 E2E de la web, además de los 69 casos de Newman y las pruebas de carga del PR-06.

**Qué se confirmó el 09/11/2026 y qué falta.** El despliegue de QA existe y es correcto: `origin/developer` tiene `.github/workflows/developer_apieyeschool-q.yml`, que despliega a la Web App `apieyeschool-q`, slot `Production`, con Python 3.11. Pero **no se pudo correr el preflight**, porque no hay URL con la que llegar a QA: `apieyeschool-q.azurewebsites.net` **no existe en DNS**, y tampoco `apieyeschool.azurewebsites.net` ni `api-eyesschool.azurewebsites.net` (comprobado con `Resolve-DnsName`; otros dominios resuelven bien desde el mismo equipo, así que no es un problema de red). La causa más probable es que Azure ya no asigna el nombre corto `<app>.azurewebsites.net`, sino un **dominio regional** del tipo `<app>-<hash>.<región>-01.azurewebsites.net`.

> **Por eso el primer paso de BE-INF-4 no es revisar `DATABASE_URL`, sino anotar las tres URLs reales** (Azure → cada Web App → Overview → *Default domain*) en la sección de entornos del PR-01: la de producción, la de QA y la de la Web App `api-eyesschool` de la decisión D-3. Sin la URL de QA no se puede ejecutar ni el preflight, ni Newman, ni `schemathesis`, ni k6, y tampoco los E2E de la web.

**Diagnóstico, en este orden** (lo hace Mariana; la IA solo interpreta lo que ella le pegue **sin la URL ni la contraseña**):

1. **La base, directamente desde el computador**, sin pasar por Azure. Con la URL externa de `qaeyesschool` leída con `Read-Host`, consultar `current_database()` y cuántas tablas hay en `public`.
   - No conecta (contraseña rechazada, *timeout*, base suspendida): el problema es la base o Render.
   - Conecta y no hay tablas: la base está vacía; faltan `alembic upgrade head` y los seeds (BE-INF-2).
   - Conecta y hay 21 tablas: la base está bien y el problema es la configuración de Azure (punto 2).
2. **La variable `DATABASE_URL` de `apieyeschool-q`** (Azure → Settings → Environment variables). Debe empezar por `postgresql+asyncpg://`, usar el host **externo** de Render, apuntar a la base `qaeyesschool` (**no a la de producción** del `.env` local), terminar en `?ssl=require` y llevar la contraseña **vigente**. Después de cambiarla: *Apply* y **Restart**.
3. **Log stream** de `apieyeschool-q` mientras se repite el login. La línea del error dice la causa:

| Error en el Log stream | Causa | Arreglo |
|---|---|---|
| `password authentication failed` | Contraseña vieja en Azure | Copiar la vigente de Render a `DATABASE_URL` y reiniciar |
| `relation "…" does not exist` | Base sin tablas | `alembic upgrade head` y seeds (BE-INF-2) |
| `unexpected keyword argument 'sslmode'` | Formato para psycopg2 | Cambiar a `?ssl=require` |
| `Name or service not known` | Host interno de Render | Usar el host externo |
| `The asyncio extension requires an async driver` | Falta `+asyncpg` | `postgresql+asyncpg://…` |
| *Timeout* o `connection refused` | Base suspendida o dormida | Revisar el estado de la base en Render |

**Otras variables de `apieyeschool-q`:** `SECRET_KEY` propia de QA y distinta de la de producción; `ENVIRONMENT=qa`; `FRONTEND_URL` con la web de QA; `SCM_DO_BUILD_DURING_DEPLOYMENT=true`. `CORS_ORIGINS` no hace falta (BE-01, punto 4). Startup command: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`.

**Aceptado cuando** el preflight sin credenciales en el código da:
- `GET /cursos/` sin token → **200** con la lista de cursos.
- Login con un correo que no existe → 401.
- Login con un cuerpo inválido → 422.
- Login del admin del seed con `QA_PASSWORD` → 200 con `access_token`.

> **Corrección del 09/11/2026:** este criterio decía antes «`GET /cursos/` sin token → 401 o 403», y estaba equivocado. `GET /cursos`, `GET /cursos/{id}`, `GET /cursos/{id}/horarios` y `GET /especializaciones` son **públicos a propósito**: son los catálogos que el formulario de registro de acudientes necesita antes de iniciar sesión, y están declarados como tales en `tests/test_authorization.py` (constante `PUBLICOS`), que falla si aparece cualquier otro endpoint sin token. La planeación de pruebas de sistema ya los usaba así en su prueba de humo. Pedir 401 ahí habría hecho fallar un preflight de un entorno sano.

**Estado al 09/11/2026: resuelto.** Con la URL real (`apieyeschool-q-g4hfgrgvepbecacc.chilecentral-01.azurewebsites.net`), el preflight da `/docs` → 200, `/openapi.json` → 200, `GET /cursos/` → 200 con datos, login inexistente → 401 y cuerpo inválido → 422. Es decir, **las consultas a la base funcionan y los 500 desaparecieron**. Falta solo el último punto del criterio, el login del admin del seed, que necesita `QA_PASSWORD` y lo corre quien la tenga:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST "$QA_API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"correo\":\"admin@eyesschool.edu.co\",\"password\":\"$QA_PASSWORD\"}"
```

El despliegue de `developer` del 09/11/2026 dejó en QA el código con las correcciones: `/openapi.json` ya expone 62 endpoints, entre ellos `/padres/me/hijos` (BE-07) y `/dispositivos` (BE-18).

---

## 7. Riesgos aceptados

| Riesgo | Evidencia | Decisión |
|---|---|---|
| QR predecible | Al registrarse, `codigo_estudiante` toma el número de documento (`auth/service.py`, línea 71) y la app genera el QR con ese código. Quien conozca el documento puede fabricar el QR de otro estudiante | El PO decidió el 30/10/2026 no firmar el QR en esta versión. Queda como riesgo aceptado en el PR-09. Mitigación: el docente o admin ve nombre y foto al escanear |

## 8. Reglas de código testeable para la API

1. **Endpoints delgados:** solo `require_roles`, dependencias y una llamada al servicio.
2. **Formato en el esquema:** rangos, `Literal`, correo y contraseña en `schemas.py`.
3. **Negocio en el servicio:** depende de métodos de repositorio con nombre claro (`exists_for_day`, `ids_estudiantes`, `docente_dicta`).
4. **Propiedad de datos en `authz.py`:** ningún endpoint con rol padre o estudiante sin `assert_acceso_estudiante` o una comparación con `current_user`.
5. **El actor sale del token, nunca del cuerpo** (`registrado_por`, dueño del recurso).
6. **Dependencias externas inyectadas** (base, correo, Firebase, almacenamiento, reloj).
7. **Errores con las excepciones del proyecto**, nunca `HTTPException` sueltas.
8. **Cada endpoint tocado:** prueba del éxito y del error esperado, con nombres en español que cuenten el escenario.
9. **Ningún secreto en el repositorio.** Solo `.env.example` con valores de ejemplo.

## 9. Definición de terminado

- [ ] La prueba que demuestra el defecto se escribió primero y fallaba antes del cambio.
- [ ] `ruff check app main.py tests` sin hallazgos.
- [ ] `pytest` en verde (unitarias y de integración).
- [ ] Cobertura de `app/` ≥ 61 % (nunca menor a 60 %).
- [ ] `pip-audit` sin críticas ni altas; `gitleaks` limpio; Quality Gate de SonarQube aprobado.
- [ ] PR revisado por otro integrante con `AB#<id>` del bug en Azure Boards.
- [ ] Desplegado en QA y verificado por el líder de pruebas.

## 10. Ramas y calendario

- Ramas desde `develop`: `fix/BE-xx-descripcion-corta`. Las críticas que ya están en producción (BE-03) salen como `hotfix/` desde `main` y se fusionan a `main` y `develop`.
- Commits: `test(asistencia): padre que pide otro estudiante recibe 403 (BE-04)` y luego `fix(asistencia): verifica propiedad del estudiante (BE-04)`.
- Liberación: `release/1.1.0` desde `develop` el 14 nov 2026 → pruebas de humo → `main` con etiqueta `v1.1.0`.

| Sprint | Fechas | Trabajo |
|---|---|---|
| S7 | 29 oct (día 1) | BE-01 (rotación), BE-03 (hotfix), ordenar ramas |
| S7 | 30 oct – 6 nov | BE-04, BE-05, BE-06, BE-08, BE-09, BE-10, BE-12, BE-14, BE-17, BE-INF-2, BE-INF-3, montaje BE-INF-1 |
| S8 | 7 – 9 nov | BE-07 (primero: la web y la app dependen de él) |
| S8 | 7 – 11 nov | BE-18 (con APP-08), BE-13, BE-19 (con WEB-09) |
| S8 | 11 – 14 nov | BE-11, BE-15, BE-16, pruebas BE-INF-1, liberación `v1.1.0` |

## 11. Decisiones del PO

**Tomadas el 30/10/2026:**

| Tema | Decisión |
|---|---|
| Registro público de padres | Es intencional; no es defecto (sección 3) |
| Redis | Se elimina del sistema (BE-17) |
| Notificaciones push | Se prueban según el PBI; como el emisor no existe, se corrige en esta versión (BE-18) |
| Salida sin entrada previa | Se rechaza con 400 (ampliación de BE-08) |
| Boletín sin notas | La API responde 404 con «No hay datos disponibles para generar el boletín.» (BE-19) |
| Reportes de asistencia (US016) | En esta versión el admin registra, consulta y descarga reportes; la generación automática con estadísticas y alertas se difiere a la siguiente versión (riesgo aceptado en el PR-09) |
| Aviso de novedad al área administrativa (US009) | El área administrativa la ve en la consulta de novedades; el push es solo para el acudiente |
| QR firmado | No en esta versión; riesgo aceptado (sección 7) |
| Lectura de notas del docente | Solo de los cursos que dicta (BE-11) |
| Carga de la API | ≥ 50 usuarios concurrentes con menos de 1 % de errores y p95 ≤ 800 ms |
| Producción | API en Azure, base en Render, web en Vercel, APK por GitHub Releases |

**Pendiente:**

| # | Pregunta | Recomendación QA |
|---|---|---|
| D-1 | ¿Se mueven los archivos a Azure Blob Storage ahora o en la siguiente versión? (BE-15) | Siguiente versión; en esta, solo quitar lo público y lo temporal |
