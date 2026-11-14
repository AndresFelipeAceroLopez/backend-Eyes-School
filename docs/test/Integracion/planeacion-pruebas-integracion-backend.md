# Planeación de pruebas de integración — Backend (API FastAPI) · Eyes School

> **Tipo de documento:** planeación de QA para el PR-05 (Informe de pruebas de integración). Describe cómo se ejecutan los casos CP-INT del PR-02 que prueban la API contra PostgreSQL y contra los servicios externos, con qué herramientas, datos y comandos, y dónde queda cada resultado. No contiene resultados: se llenan al ejecutar.
> **Pensado para:** cualquier integrante del equipo o una IA que no conoce el proyecto. Los casos y sus ID son los del PR-02 v0.2.
> **Elaboró:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> **Plazo:** montaje en S7 (hasta el 6 nov 2026) y ejecución en S8 (7 – 14 nov 2026), según el PR-01.
> **Actualizado el 09/11/2026 (montaje terminado; I1 local ejecutada, I1 contra QA bloqueada):** las **53 pruebas** de `tests/integration/` ya existen y **pasan las 53 contra PostgreSQL 18.6 real** (ver [`../Resultados/corrida-2026-11-09.md`](../Resultados/corrida-2026-11-09.md), sección 4). La colección Newman se **genera** con 70 casos. Tres cosas cambiaron respecto a lo planeado y se corrigen abajo: la variable es **`TEST_DATABASE_URL`**, no `DATABASE_URL`; el esquema se crea **desde los modelos SQLAlchemy**, no desde `schema.sql`; y la base local se puede montar con **PostgreSQL 18 nativo (winget)**, no solo con Docker. La ejecución de Newman y de los casos contra QA sigue **bloqueada por BE-INF-4/DEF-WEB-01** (la API de QA responde 500 en todo lo que consulta la base).

---

## 1. Objetivo y alcance

Verificar que la API funciona con sus dependencias **reales**: la base PostgreSQL (consultas, restricciones, transacciones) y la interfaz HTTP completa con tokens reales. Las pruebas unitarias del PR-04 prueban la lógica con dobles; aquí se prueba la integración.

| Interfaz | Casos del PR-02 | Cómo se prueba |
|---|---|---|
| API ↔ PostgreSQL | 81 casos de la API (CP-INT-001 a 074 y 077 a 083) | Newman contra la API de QA y `pytest` con marca `integration` contra PostgreSQL en Docker |
| API ↔ servicios externos | CP-INT-011 (correo), CP-INT-057 y 058 (Firebase) | El correo real está fuera de alcance (PR-01): se verifica la respuesta neutra. Firebase se reemplaza por `NotificadorFalso` (BE-18); el envío real a un teléfono es del PR-06 |
| Web ↔ API y Móvil ↔ API | CP-INT-075 y 076 | En las planeaciones de integración de la web y de la app |

## 2. Entornos

| Entorno | Para qué | Datos |
|---|---|---|
| Local (Docker **o** PostgreSQL nativo) | `pytest -m integration`: casos que necesitan controlar el estado de la base, generar tokens con la `SECRET_KEY` o reemplazar Firebase | Esquema desde los **modelos SQLAlchemy** + `seed_data.sql` + `seed_estudiantes_sinteticos.sql`; cada prueba corre en una transacción que se revierte |
| QA (Azure + PostgreSQL de QA) | Colección Newman: caja negra por HTTP con usuarios reales de QA | `alembic upgrade head` → `seed_data.sql` → `seed_estudiantes_sinteticos.sql` → `scripts/qa_reset_passwords.py` (BE-INF-2) |

- **Versión de PostgreSQL:** 18, la de producción en Render (decisión del 30/10/2026). La planeación de correcciones (BE-INF-1) dice `postgres:16`; se corrige a `postgres:18` en el `ci.yml` y en Docker.
- **Base local sin Docker (verificado el 09/11/2026):** si el equipo no tiene Docker Desktop, sirve el **zip de binarios** de PostgreSQL 18, que no necesita instalador ni permisos de administrador:

  ```bash
  curl -L -A "Mozilla/5.0" -o pg.zip \
    https://get.enterprisedb.com/postgresql/postgresql-18.6-5-windows-x64-binaries.zip
  # extraer el zip y, desde la carpeta pgsql/bin:
  initdb   -D ../../data -U postgres --pwfile=pw.txt -E UTF8 --locale=C
  pg_ctl   -D ../../data -l server.log -o "-p 5432" start
  createdb -U postgres -h 127.0.0.1 eyes_test
  ```

  **`winget install PostgreSQL.PostgreSQL.18` no funciona:** EnterpriseDB rechaza el *User-Agent* de winget y la descarga falla con `0x80190193 : Prohibido (403)` después de varios minutos sin mensaje claro. La misma URL responde 200 con el *User-Agent* de un navegador, que es lo que hace el `curl` de arriba. Con esto queda la misma URL de conexión que con Docker y el clúster se puede borrar con `pg_ctl stop` y eliminando la carpeta.
- **Nunca `schema.sql`:** es un dump de Supabase (roles, extensiones y políticas RLS) que no carga en un PostgreSQL limpio. Esta planeación decía `schema.sql` en la sección 3; el montaje real crea el esquema con `Base.metadata.create_all`.
- **La variable es `TEST_DATABASE_URL`, no `DATABASE_URL`.** `tests/conftest.py` fuerza `DATABASE_URL` a una dirección inexistente para que ninguna prueba toque datos reales, y solo `TEST_DATABASE_URL` puede reemplazarla. Si `TEST_DATABASE_URL` no está definida, las 53 pruebas se **omiten solas** (`skipped`) en lugar de fallar: hay que revisar el conteo, porque una corrida «sin errores» puede ser una corrida sin ejecutar nada.
- **URL de la API de QA:** pendiente de definir en el PR-01 (sección de entornos). Mientras no exista, la colección se corre contra la API local levantada con `uvicorn` sobre la base de Docker, y así se anota en el PR-05.
- **Usuarios:** DS-01 (un usuario por rol, padre de un hijo: `roberto.diaz@gmail.com`), DS-03 (padre de dos hijos: `rosa.perez@gmail.com`). La contraseña es `QA_PASSWORD`, que se pasa por variable de entorno y nunca se escribe en la colección ni en las evidencias.

## 3. Preparación (S7)

### BE-IT-1 · pytest de integración (es BE-INF-1)

1. Carpeta `tests/integration/` y marca `integration` registrada en `pyproject.toml`. El CI de cada PR corre `pytest -m "not integration"`; un job aparte corre `pytest -m integration`.
2. `tests/integration/conftest.py` (**montado el 02/11/2026; verificado el 09/11/2026**):
   - crea el motor con `TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/eyes_test` y **omite todas las pruebas si la variable no está**;
   - crea el esquema con `Base.metadata.create_all` y carga `seed_data.sql` y `seed_estudiantes_sinteticos.sql` una vez por sesión (no usa `schema.sql`);
   - fija una contraseña de pruebas para los usuarios del seed, porque las del seed ya no se conocen (H-08);
   - abre una transacción por prueba y la revierte al final;
   - reemplaza solo lo externo con `app.dependency_overrides`: `Notificador` → `NotificadorFalso`, envío de correo → doble que guarda los mensajes;
   - genera tokens con `create_access_token` y los de recuperación con `create_password_reset_token`.
3. Servicio `postgres:18` en el job del CI.

### BE-IT-2 · Colección Newman

1. Colección `tests/newman/eyes_school_api.postman_collection.json` con una carpeta por módulo: Auth, Usuarios, Asistencia, Notas, Novedades, Padres y dashboard, Horarios y asignaciones, Reportes y archivos. **La colección no se edita a mano: se genera** con `python tests/newman/generar_coleccion.py` (regenerada el 09/11/2026: **70 casos**).
2. Cada petición lleva el ID del caso en el nombre (por ejemplo «CP-INT-031 Segunda entrada → 409») y pruebas `pm.test` del código de estado, del cuerpo esperado y del tiempo de respuesta.
3. Entorno `tests/newman/qa.postman_environment.json` con `base_url` y los correos de DS-01 y DS-03. La contraseña entra con `--env-var QA_PASSWORD=...` desde un secreto.
4. Una carpeta inicial «00 Sesiones» inicia sesión con cada rol y guarda los tokens en variables de colección.
5. Los registros que crea la colección (usuarios, asistencias, notas, novedades de prueba) se borran en una carpeta final «99 Limpieza».

### BE-IT-3 · Validación del contrato con OpenAPI

- `schemathesis` (pip) contra `GET /openapi.json` de la API de QA, con el token de admin, para la Tabla 6 del PR-05 (respuesta conforme al esquema publicado).

### BE-IT-4 · Herramientas en VS Code

- Extensión **Postman** (o Thunder Client) para editar la colección; Node.js y `npm install -g newman newman-reporter-htmlextra` (newman 6.2.3 instalado el 09/11/2026).
- Extensión **Python** para correr `pytest -m integration` desde la pestaña Testing.
- Docker Desktop **o** PostgreSQL 18 nativo para la base local (ver sección 2).

### BE-IT-5 · Precondición: entorno de QA operativo

La colección Newman, `schemathesis` y los 69 casos que se ejecutan contra QA **no se pueden correr hasta que se cierre BE-INF-4 (DEF-WEB-01)**: al 09/11/2026 la API de QA responde 500 en todo lo que consulta la base. No se sustituye apuntando la colección a la base de producción: lo prohíbe la regla 1.4 de la planeación de correcciones. Mientras el bloqueo siga, en el PR-05 esos casos se registran como **Bloqueados**, con BE-INF-4 como causa, y solo se reportan los 53 de `pytest -m integration` contra la base local.

## 4. Mapeo de casos a herramienta

Los 81 casos de la API del PR-02 se ejecutan así: 51 solo con Newman, 12 solo con pytest de integración (necesitan controlar la base, la `SECRET_KEY`, el reloj o Firebase) y 18 con las dos herramientas (la regla se prueba por HTTP en QA y la restricción en la base real).

> **BC-06 (13/11/2026): los 81 CP-INT tienen ejecución.** 75 corren en Newman contra QA y 6 solo en pytest de integración, porque no se pueden hacer por HTTP sin un buzón de correo o tocan una capa interna. CP-INT-006, 009, 010, 029, 058 y 072 pasaron de pytest a Newman: se ejecutan sobre una **cuenta temporal** que la colección crea al empezar y borra al final, para no bloquear ni desactivar cuentas del seed.
>
> | Caso | Por qué se queda en pytest | Prueba que lo cubre (`tests/integration/`) |
> |---|---|---|
> | CP-INT-012 | El token de recuperación llega por correo | `test_auth_sesiones.py::test_restablecer_la_contrasena_permite_entrar_con_la_nueva` |
> | CP-INT-013 | Ídem | `test_auth_sesiones.py::test_restablecer_con_una_contrasena_debil_responde_422` |
> | CP-INT-014 | Ídem | `test_auth_sesiones.py::test_el_enlace_de_recuperacion_no_se_puede_reutilizar` |
> | CP-INT-015 | Ídem (además necesita un token vencido) | `test_auth_sesiones.py::test_un_enlace_vencido_responde_401` |
> | CP-INT-049 | Es del repositorio, no tiene ruta HTTP | `test_notas_novedades.py::test_el_promedio_del_estudiante_se_calcula_en_la_base` |
> | CP-INT-057 | El envío push no es observable por HTTP | `test_notas_novedades.py::test_la_novedad_notifica_solo_a_los_acudientes_del_estudiante` |
>
> Los otros seis también tienen su prueba pytest: CP-INT-006 → `test_cinco_fallos_bloquean_el_sexto_intento_aunque_la_clave_sea_correcta`, CP-INT-009 → `test_login_refresh_logout_refresh_termina_en_401`, CP-INT-010 → `test_un_usuario_desactivado_no_renueva_su_sesion`, CP-INT-029 → `test_desactivar_desde_el_admin_revoca_las_sesiones`, CP-INT-058 → `test_registrar_el_mismo_dispositivo_dos_veces_no_lo_duplica`, CP-INT-072 → `test_el_avatar_valida_el_contenido_real_del_archivo`.

| ID | Interfaz | Ejecución | Hoy |
|---|---|---|---|
| CP-INT-001 | POST /api/v1/auth/login | Newman (QA) | Sin ejecutar |
| CP-INT-002 | POST /api/v1/auth/login | Newman (QA) | Sin ejecutar |
| CP-INT-003 | POST /api/v1/auth/login | Newman (QA) | Sin ejecutar |
| CP-INT-004 | POST /api/v1/auth/login | Newman (QA) | Sin ejecutar |
| CP-INT-005 | POST /api/v1/auth/login | Newman (QA) | Sin ejecutar |
| CP-INT-006 | POST /api/v1/auth/login | Newman (QA) con cuenta temporal + pytest integración (local) | Falla esperada (BE-16) |
| CP-INT-007 | POST /api/v1/auth/login | Newman (QA) | Falla esperada (BE-12) |
| CP-INT-008 | POST /api/v1/auth/refresh | Newman (QA) | Sin ejecutar |
| CP-INT-009 | POST /auth/logout → POST /auth/refresh | Newman (QA) con cuenta temporal + pytest integración (local) | Falla esperada (BE-13, BE-17) |
| CP-INT-010 | POST /api/v1/auth/refresh | Newman (QA) con cuenta temporal + pytest integración (local) | Falla esperada (BE-13) |
| CP-INT-011 | POST /api/v1/auth/forgot-password | Newman (QA) | Sin ejecutar |
| CP-INT-012 | POST /api/v1/auth/reset-password | pytest integración (local) | Sin ejecutar |
| CP-INT-013 | POST /api/v1/auth/reset-password | pytest integración (local) | Falla esperada (BE-09) |
| CP-INT-014 | POST /api/v1/auth/reset-password | pytest integración (local) | Falla esperada (BE-13) |
| CP-INT-015 | POST /api/v1/auth/reset-password | pytest integración (local) | Sin ejecutar |
| CP-INT-016 | POST /api/v1/auth/register | Newman (QA) | Sin ejecutar |
| CP-INT-017 | POST /api/v1/auth/register | Newman (QA) y pytest integración | Sin ejecutar |
| CP-INT-018 | POST /api/v1/auth/register | Newman (QA) y pytest integración | Falla esperada (BE-12) |
| CP-INT-019 | POST /api/v1/auth/register | Newman (QA) | Sin ejecutar |
| CP-INT-020 | POST /api/v1/auth/register | Newman (QA) | Falla esperada (BE-09) |
| CP-INT-021 | POST /api/v1/auth/register | Newman (QA) | Sin ejecutar |
| CP-INT-022 | POST /api/v1/usuarios | Newman (QA) | Sin ejecutar |
| CP-INT-023 | POST /api/v1/usuarios | Newman (QA) | Sin ejecutar |
| CP-INT-024 | PUT /api/v1/usuarios/{id} | Newman (QA) | Sin ejecutar |
| CP-INT-025 | DELETE /api/v1/usuarios/{id} | Newman (QA) | Sin ejecutar |
| CP-INT-026 | GET /api/v1/usuarios | Newman (QA) | Sin ejecutar |
| CP-INT-027 | GET y POST /api/v1/usuarios | Newman (QA) | Sin ejecutar |
| CP-INT-028 | PUT /api/v1/usuarios/{propio} | Newman (QA) | Falla esperada (BE-09) |
| CP-INT-029 | PATCH /api/v1/usuarios/{id}/estado?estado=false | Newman (QA) con cuenta temporal + pytest integración (local) | Falla esperada (BE-13) |
| CP-INT-030 | POST /api/v1/asistencia | Newman (QA) y pytest integración | Sin ejecutar |
| CP-INT-031 | POST /api/v1/asistencia | Newman (QA) y pytest integración | Falla esperada (BE-08) |
| CP-INT-032 | POST /api/v1/asistencia | Newman (QA) y pytest integración | Sin ejecutar |
| CP-INT-033 | POST /api/v1/asistencia | Newman (QA) y pytest integración | Falla esperada (BE-08) |
| CP-INT-034 | POST /api/v1/asistencia | Newman (QA) y pytest integración | Falla esperada (BE-08) |
| CP-INT-035 | POST /api/v1/asistencia, /notas, /novedades | Newman (QA) y pytest integración | Falla esperada (BE-10) |
| CP-INT-036 | GET /api/v1/asistencia?id_estudiante={ajeno} | Newman (QA) y pytest integración | Falla esperada (BE-04) |
| CP-INT-037 | GET /api/v1/asistencia | Newman (QA) y pytest integración | Falla esperada (BE-04) |
| CP-INT-038 | GET /api/v1/asistencia/{id} | Newman (QA) y pytest integración | Falla esperada (BE-04) |
| CP-INT-039 | GET /api/v1/estudiantes/{id}/asistencia | Newman (QA) | Sin ejecutar |
| CP-INT-040 | DELETE /api/v1/asistencia/{id} | Newman (QA) | Sin ejecutar |
| CP-INT-041 | POST /api/v1/notas | Newman (QA) | Sin ejecutar |
| CP-INT-042 | POST /api/v1/notas | Newman (QA) | Sin ejecutar |
| CP-INT-043 | POST /api/v1/notas | Newman (QA) | Falla esperada (BE-06) |
| CP-INT-044 | POST /api/v1/notas | Newman (QA) | Sin ejecutar |
| CP-INT-045 | POST /api/v1/notas | Newman (QA) y pytest integración | Sin ejecutar |
| CP-INT-046 | PUT /api/v1/notas/{id} | Newman (QA) | Falla esperada (BE-06) |
| CP-INT-047 | POST /api/v1/notas | Newman (QA) y pytest integración | Falla esperada (BE-11) |
| CP-INT-048 | GET /api/v1/notas | Newman (QA) y pytest integración | Falla esperada (BE-11) |
| CP-INT-049 | NotasRepository.get_promedio_estudiante ↔ PostgreSQL | pytest integración (local) | Sin ejecutar |
| CP-INT-050 | GET /api/v1/estudiantes/{id}/notas | Newman (QA) | Sin ejecutar |
| CP-INT-051 | GET /api/v1/notas/estudiantes/{id}/boletin/pdf | Newman (QA) | Falla esperada (BE-15) |
| CP-INT-052 | GET /api/v1/notas/estudiantes/{id}/boletin/pdf | Newman (QA) | Falla esperada (BE-19) |
| CP-INT-053 | GET /api/v1/notas/estudiantes/{id}/boletin/pdf | Newman (QA) | Sin ejecutar |
| CP-INT-054 | POST /api/v1/novedades | Newman (QA) | Sin ejecutar |
| CP-INT-055 | POST /api/v1/novedades | Newman (QA) | Sin ejecutar |
| CP-INT-056 | PUT y DELETE /api/v1/novedades/{id} | Newman (QA) | Falla esperada (BE-11) |
| CP-INT-057 | NovedadService.create → Notificador | pytest integración (local) | Falla esperada (BE-18) |
| CP-INT-058 | POST /api/v1/dispositivos | Newman (QA) con cuenta temporal + pytest integración (local) | Falla esperada (BE-18) |
| CP-INT-059 | GET /api/v1/estudiantes/{id}/novedades | Newman (QA) | Sin ejecutar |
| CP-INT-060 | GET /api/v1/dashboard/estudiante | Newman (QA) | Falla esperada (BE-03) |
| CP-INT-061 | GET /api/v1/dashboard/padre | Newman (QA) | Sin ejecutar |
| CP-INT-062 | GET /api/v1/padres/me/hijos | Newman (QA) y pytest integración | Falla esperada (BE-07) |
| CP-INT-063 | GET /api/v1/padres/me | Newman (QA) y pytest integración | Falla esperada (BE-07) |
| CP-INT-064 | GET /api/v1/dashboard/padre?id_estudiante={ajeno} | Newman (QA) y pytest integración | Falla esperada (BE-07) |
| CP-INT-065 | GET /api/v1/padres/{id} | Newman (QA) | Falla esperada (BE-05) |
| CP-INT-066 | GET /api/v1/horarios?id_curso={curso} | Newman (QA) | Sin ejecutar |
| CP-INT-067 | GET /api/v1/asignaciones?id_profesor={propio} | Newman (QA) | Sin ejecutar |
| CP-INT-068 | GET /api/v1/reportes | Newman (QA) | Sin ejecutar |
| CP-INT-069 | POST /api/v1/reportes/archivo → POST /api/v1/reportes | Newman (QA) | Sin ejecutar |
| CP-INT-070 | GET /api/v1/reportes/{id}/archivo | Newman (QA) | Sin ejecutar |
| CP-INT-071 | GET /static/reportes/{archivo} | Newman (QA) | Falla esperada (BE-15) |
| CP-INT-072 | POST /api/v1/auth/me/avatar | Newman (QA) con cuenta temporal + pytest integración (local) | Falla esperada (BE-14) |
| CP-INT-073 | GET /api/v1/auth/me | Newman (QA) | Sin ejecutar |
| CP-INT-074 | GET /api/v1/estudiantes/me | Newman (QA) | Sin ejecutar |
| CP-INT-077 | POST /api/v1/usuarios | Newman (QA) y pytest integración | Falla esperada (BE-12) |
| CP-INT-078 | POST /api/v1/usuarios | Newman (QA) | Sin ejecutar |
| CP-INT-079 | PUT /api/v1/usuarios/{id} | Newman (QA) | Sin ejecutar |
| CP-INT-080 | POST /api/v1/notas | Newman (QA) | Sin ejecutar |
| CP-INT-081 | GET /api/v1/asistencia?fecha={hoy} | Newman (QA) | Sin ejecutar |
| CP-INT-082 | GET /api/v1/estudiantes/{propio}/notas | Newman (QA) | Sin ejecutar |
| CP-INT-083 | GET /api/v1/novedades | Newman (QA) | Sin ejecutar |
«Falla esperada» repite el estado del PR-02: el defecto ya está identificado y el caso pasa a verde cuando se fusiona la corrección indicada.

## 5. Ejecución (S8)

| Corrida | Fecha | Qué mide |
|---|---|---|
| I1 | 7 nov 2026 | Estado al empezar S8; registra las fallas esperadas |
| I2 | 13 nov 2026 | Con las correcciones de S7 y S8 en QA; es el resultado oficial del PR-05 |

```bash
# 0. Base local y datos
# Base local: Docker...
docker run -d --name eyes_pg -p 5432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=eyes_test postgres:18
# ...o PostgreSQL 18 nativo ya instalado (ver sección 2):
createdb -U postgres eyes_test

git rev-parse --short HEAD > evidencias/PR-05/api/I1_commit.txt

# 1. pytest de integración contra PostgreSQL. La variable es TEST_DATABASE_URL (si falta, las 53
#    pruebas se omiten en silencio). NUNCA apuntarla a producción: la suite recrea el esquema.
export TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/eyes_test
pytest -m integration -v --junitxml=evidencias/PR-05/api/I1_pytest_integracion.xml \
       > evidencias/PR-05/api/I1_pytest_integracion.txt
# Verificar en la última línea que diga "53 passed" y no "53 skipped".

# 2. Colección Newman contra QA (la contraseña sale de un secreto, no se escribe)
newman run tests/newman/eyes_school_api.postman_collection.json \
       -e tests/newman/qa.postman_environment.json --env-var "QA_PASSWORD=$QA_PASSWORD" \
       -r cli,junit,htmlextra \
       --reporter-junit-export evidencias/PR-05/api/I1_newman.xml \
       --reporter-htmlextra-export evidencias/PR-05/api/I1_newman.html

# 3. Contrato contra OpenAPI, SOLO LECTURA (ver la nota de abajo)
python -m scripts.qa.openapi_solo_lectura "${QA_API%/api/v1}" openapi_solo_get.json
schemathesis run openapi_solo_get.json --url "${QA_API%/api/v1}" -H "Authorization: Bearer $TOKEN_ADMIN" \
       --checks all --exclude-checks unsupported_method,allow_header_conformance > evidencias/PR-05/api/I2_schemathesis.txt
```

- **schemathesis va siempre contra un contrato recortado a GET** (`scripts/qa/openapi_solo_lectura.py`). Con el contrato completo prueba también POST, PUT y DELETE con el token de administrador; y los filtros `--include-method`/`--include-path-regex` se combinan con OR, así que no lo impiden. Y se excluyen `unsupported_method` (ST204), que manda a propósito los métodos no declarados en el contrato, y `allow_header_conformance` (ST205), que compara `Allow` con un contrato que al recortarlo ya no lista PUT ni DELETE. Así se alteraron datos de QA el 13/11/2026 (ver `Resultados/cierre-backend-2026-11-13.md`, anexo A).
- Antes de cada corrida en QA se ejecuta `scripts/qa_reset_passwords.py` y se verifica que la prueba de humo de la API responda.
- Los casos con el mismo ID en Newman y en pytest se reportan como **un solo caso**: aprobado si pasan los dos.

## 6. Criterios

| Indicador | Meta | Origen |
|---|---|---|
| Casos ejecutados | 100 % de los 81 | PR-01 |
| Casos aprobados en la I2 | ≥ 95 % | PR-01 / MC-01 |
| Defectos críticos o altos abiertos | 0 | PR-01 |
| Respuestas conformes a OpenAPI | 100 % de los endpoints de la Tabla 6 | PR-02 (riesgo R-07) |

Se suspende la ejecución si la API o la base de QA no están disponibles más de 4 horas hábiles o si más del 30 % de los casos queda bloqueado (PR-01).

## 7. Registro en el PR-05 y defectos

| Resultado | Dónde va |
|---|---|
| Totales de los reportes JUnit (Newman y pytest) | Tabla 1 |
| Conteo por interfaz | Tabla 2 |
| Resultado de cada CP-INT con su evidencia | Tabla 3 |
| Código, conformidad con OpenAPI y tiempo por endpoint | Tabla 6 |
| Caso fallido sin corrección planeada | Bug en Azure Boards (etiqueta `pruebas-integracion`) con el ID del caso |
| Caso con falla esperada | Se enlaza al bug de su corrección BE-xx; no se duplica |

## 8. Responsables y calendario

| Actividad | Fecha | Responsable |
|---|---|---|
| BE-IT-1 (montaje de pytest con PostgreSQL 18) | 3 – 6 nov | Samuel Sierra · Andrés Acero |
| BE-IT-2 (colección Newman) y BE-IT-3 | 3 – 6 nov | Mariana Cortés |
| I1 | 7 nov | Mariana Cortés |
| I2 y columnas de la API del PR-05 | 13 – 14 nov | Mariana Cortés · revisa Samuel Sierra |

## 9. Definición de terminado

- [ ] `pytest -m integration` corre en el CI con `postgres:18`.
- [ ] La colección Newman tiene los 69 casos que le corresponden, cada uno con su ID, y limpia lo que crea.
- [ ] I1 e I2 ejecutadas, con evidencias en `evidencias/PR-05/api/` y sin contraseñas ni tokens en ellas.
- [ ] Tablas 1, 2, 3 y 6 del PR-05 diligenciadas para la API y revisadas por el líder de pruebas.
