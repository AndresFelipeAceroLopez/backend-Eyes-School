# Pruebas de la API — Eyes School

Implementación de las planeaciones de QA de `docs/test/`. Cada corrección (BE-xx) tiene primero
la prueba que demuestra el defecto y después el cambio que la hace pasar.

## Cómo se ejecutan

| Qué | Comando | Necesita |
|---|---|---|
| Unitarias y de componente (PR-04) | `pytest` | Nada: base y servicios externos son dobles |
| Con cobertura | `pytest --cov=app --cov-branch --cov-report=term-missing` | — |
| Integración contra PostgreSQL (PR-05) | `TEST_DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5432/eyes_test pytest -m integration` | Una base **desechable** (`docker run -p 5432:5432 -e POSTGRES_PASSWORD=test -e POSTGRES_DB=eyes_test postgres:18`) |
| Colección Newman contra QA (PR-05) | `scripts/qa/correr_integracion.sh I1` | `newman`, `QA_API`, `QA_PASSWORD` |
| Carga y estrés (PR-06) | `k6 run tests/carga/carga_50.js` | `k6`, `QA_API`, `QA_PASSWORD` y `usuarios_ds02.json` |
| Análisis estático (PR-03) | `scripts/qa/correr_estatico.sh E1` | ruff, bandit, lizard, radon, jscpd, gitleaks |
| Evidencias de unitarias (PR-04) | `scripts/qa/correr_unitarias.sh U1` | — |

`pytest` por defecto excluye las de integración (`-m 'not integration'` en `pyproject.toml`).
Las de integración se omiten solas si `TEST_DATABASE_URL` no está definida. **Nunca** apunte
`TEST_DATABASE_URL` a producción: la suite borra y recrea el esquema `public`.

La suite de integración crea el esquema desde los modelos (`Base.metadata.create_all`) y carga
`seed_data.sql` + `seed_estudiantes_sinteticos.sql`. No usa `schema.sql` porque ese archivo es un
dump de Supabase (roles, extensiones y políticas RLS) que no carga en un PostgreSQL limpio.
Cada prueba corre en una transacción que se revierte.

## Qué archivo cubre cada corrección

| ID | Corrección | Unitarias | Integración |
|---|---|---|---|
| UT-API-01 | BE-03 · inicio del estudiante | `test_dashboard.py` | `integration/test_acceso_a_datos.py` |
| UT-API-02 | BE-04 · asistencia ajena | `test_authorization.py` | `integration/test_acceso_a_datos.py` |
| UT-API-03 | BE-05 · vínculo de otro padre | `test_authorization.py` | `integration/test_acceso_a_datos.py` |
| UT-API-04 | BE-06 · escala de notas | `test_notas_validacion.py` | `integration/test_notas_novedades.py` |
| UT-API-05 | BE-07 · varios hijos | `test_padre_varios_hijos.py` | `integration/test_acceso_a_datos.py` |
| UT-API-06 | BE-08 · duplicados | `test_asistencia_duplicados.py` | `integration/test_acceso_a_datos.py` |
| UT-API-07 | BE-09 · política de contraseña | `test_password_policy.py` | `integration/test_auth_sesiones.py` |
| UT-API-08 | BE-10 · actor desde el token | `test_actor_token.py` | `integration/` (asistencia, notas, novedades) |
| UT-API-09 | BE-11 · permisos del docente | `test_permisos_docente.py` | `integration/test_notas_novedades.py` |
| UT-API-10 | BE-12 · correo | `test_correo.py`, `test_normalizar_correos.py` | `integration/test_auth_sesiones.py` |
| UT-API-11 | BE-13 · sesión | `test_sesion.py` | `integration/test_auth_sesiones.py` |
| UT-API-12 | BE-14 · avatares | `test_avatar.py` | `integration/test_notas_novedades.py` |
| UT-API-13 | BE-15 · archivos | `test_archivos.py`, `test_boletin.py` | `integration/test_notas_novedades.py` |
| UT-API-14 | BE-16 · bloqueo de login | `test_bloqueo_login.py` | `integration/test_auth_sesiones.py` |
| UT-API-15 | BE-17 · sesiones en PostgreSQL | `test_sesion.py` + paso de búsqueda de restos del CI | `integration/test_auth_sesiones.py` |
| UT-API-16 | BE-18 · notificaciones | `test_notificaciones.py` | `integration/test_notas_novedades.py` |
| UT-API-17 | BE-19 · boletín sin notas | `test_boletin.py` | `integration/test_notas_novedades.py` |
| UT-API-18 | BE-INF-2 · datos de QA | `test_qa_reset_passwords.py` | — |

## Dobles de prueba

- `tests/conftest.py`: fixture `client` (HTTP con `ASGITransport`), `sin_base_de_datos` (reemplaza
  `get_db`) y `bearer(rol, id_rol, id_usuario)`.
- `tests/dobles.py`: repositorios falsos con estado (sesiones, usuarios, notas, novedades,
  dispositivos) y `NotificadorFalso`. Se reemplazan con `monkeypatch.setattr(modulo, "XRepository", Doble)`.

## Colección Newman

`tests/newman/eyes_school_api.postman_collection.json` se **genera** con
`python tests/newman/generar_coleccion.py` (un caso por fila, con el ID CP-INT en el nombre; la
lista se valida contra la tabla de la planeación de integración). La contraseña nunca está en la
colección: entra con `--env-var QA_PASSWORD=...`. Variables del entorno que dependen de QA:
`id_estudiante_sin_notas` (CP-INT-052 se omite si está vacía) y los ids de DS-01/DS-03.

## Estado de las corridas

| Corrida | Estado | Detalle |
|---|---|---|
| U1 (unitarias) | ✔ 09/11/2026 | 154/154 · cobertura 68 % |
| E1 (estático) | ✔ 09/11/2026 | 9 de 10 controles; B8 falla por BE-01 (6 secretos en el historial) |
| I1 (integración local) | ✔ 09/11/2026 | 53/53 contra PostgreSQL 18.6 |
| I1 (Newman / QA) | Bloqueada | BE-INF-4: la API de QA responde 500 |
| S1 (k6) | Bloqueada | BE-INF-4 |
| B4 (SonarQube) | Pendiente | Falta `SONAR_TOKEN` |

Los resultados completos están en
[`../docs/test/Resultados/corrida-2026-11-09.md`](../docs/test/Resultados/corrida-2026-11-09.md).

## Lo que sigue pendiente (fuera del código)

BE-01 (rotar secretos de Render y Azure, llevar `create_admin.py` corregido a `main` y,
opcionalmente, limpiar el historial de `.env` **y `create_admin.py`**), BE-INF-4 (arreglar
`DATABASE_URL` de `apieyeschool-q`), SonarQube Cloud (token y proyecto), la URL de la API de QA y
el registro de bugs en Azure Boards.
