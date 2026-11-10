# Planeación de pruebas unitarias y cobertura — Backend (API FastAPI) · Eyes School

> **Tipo de documento:** planeación de QA para el PR-04 (Informe de pruebas unitarias y cobertura). Describe qué pruebas unitarias existen, cuáles se escriben, cómo se ejecutan, cómo se mide la cobertura y dónde queda cada resultado. No contiene resultados: se llenan al ejecutar.
> **Pensado para:** cualquier integrante del equipo o una IA que no conoce el proyecto. El inventario se contó leyendo el código del commit `0af4531` el 02/11/2026.
> **Elaboró:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> **Plazo:** las pruebas nuevas se escriben con cada corrección (S7 y S8); la ejecución que se reporta en el PR-04 es en S8 (7 – 14 nov 2026), según el PR-01.
> **Actualizado el 09/11/2026 (U1 ejecutada):** las 18 pruebas nuevas (UT-API-01 a 18) ya existen. El inventario pasó de 26 a **154 casos, todos aprobados**, y la cobertura de líneas de 61 % a **68 %**. Los pasos de la sección 6 quedaron automatizados en `scripts/qa/correr_unitarias.sh`. Dos correcciones al contexto: `tests/conftest.py` ya **no** fija `REDIS_URL` (Redis se retiró con BE-17) y usa `TEST_DATABASE_URL`. Los resultados están en [`../Resultados/corrida-2026-11-09.md`](../Resultados/corrida-2026-11-09.md), no en esta planeación.

---

## 1. Objetivo y alcance

Verificar esquemas, servicios, autorización y seguridad de la API **sin base de datos real**, reemplazando repositorios, correo, Firebase, disco y reloj por dobles, y medir la cobertura de líneas del paquete `app/` contra el umbral del MC-01.

| Es prueba unitaria o de componente (PR-04) | No entra en el PR-04 |
|---|---|
| Todo lo que hay en `tests/` sin la marca `integration`: esquemas con `model_validate`, servicios con repositorios dobles, endpoints por HTTP con `httpx.ASGITransport` y dependencias reemplazadas | `tests/integration/` contra PostgreSQL real (BE-INF-1) y la colección Newman contra QA: **PR-05** |

## 2. Contexto técnico

| Dato | Valor |
|---|---|
| Repositorio y commit | `backend-Eyes-School` · `chore/calidad-seguridad` · `0af4531` (25/10/2026). Si para el 7 nov ya existe `develop` con las correcciones, se ejecuta sobre `develop` y se anota el commit |
| Framework | `pytest` + `pytest-asyncio` + `httpx` (`ASGITransport`). Dobles con clases falsas, `monkeypatch` y `app.dependency_overrides` |
| Fixtures existentes | `tests/conftest.py`: fuerza `DATABASE_URL` a una dirección inexistente (ninguna prueba toca datos reales) y solo `TEST_DATABASE_URL` puede reemplazarla; fixture `client`, `sin_base_de_datos` y helper `bearer(rol, id_rol, id_usuario)`. Los dobles de repositorio y el `NotificadorFalso` están en `tests/dobles.py`. **Ya no fija `REDIS_URL`: Redis se retiró con BE-17** |
| Cobertura | `pytest-cov` (coverage.py) sobre `app/`; el CI genera `coverage.xml` |
| CI | `ci.yml`: `pytest -q --cov=app --cov-report=term --cov-report=xml` |
| Línea base (MC-01, 25/10/2026) | 26 de 26 pruebas aprobadas · cobertura de líneas 61 % |

## 3. Inventario actual (contado en el código)

| Archivo | Funciones de prueba | Casos ejecutados | Qué prueba |
|---|---|---|---|
| `test_app.py` | 2 | 2 | La API expone sus rutas; los modelos y relaciones se configuran |
| `test_authorization.py` | 7 | 9 (una función parametrizada con 3 roles) | Endpoints públicos declarados; 401 sin token o con token inválido; un refresh no sirve como acceso; solo el admin lista usuarios; CORS |
| `test_config.py` | 4 | 6 (una función parametrizada con 3 valores) | En producción no arranca sin `SECRET_KEY`; `CORS_ORIGINS` como lista |
| `test_register.py` | 4 | 4 | Perfil y estado según el rol al registrarse; vínculo del padre |
| `test_security.py` | 5 | 5 | Hash de contraseña; tipos de token; token alterado, de otra clave o vencido |
| **Total** | **22** | **26 (cuadra con la línea base)** | |

El número de casos por archivo parametrizado se confirma con `pytest --collect-only -q`.

## 4. Pruebas unitarias nuevas (salen de la planeación de correcciones del backend)

Cada una se escribe **antes** del cambio y debe fallar contra el código actual. Los casos detallados están en la sección de cada corrección.

| ID | Corrección | Archivo | Casos | Resultado esperado hoy |
|---|---|---|---|---|
| UT-API-01 | BE-03 · inicio del estudiante | `tests/test_dashboard.py` | 3 (estudiante 200, padre 200, docente 403) | Falla: 500 por `AttributeError` |
| UT-API-02 | BE-04 · asistencia ajena | `tests/test_authorization.py` | 5 | Falla: responde 200 |
| UT-API-03 | BE-05 · vínculo de otro padre | `tests/test_authorization.py` | 3 | Falla en «padre pide el de otro» |
| UT-API-04 | BE-06 · escala de notas | `tests/test_notas_validacion.py` | 4 (límites válidos, inválidos, actualización, HTTP 422) | Falla: acepta hasta 10 |
| UT-API-05 | BE-07 · varios hijos | `tests/test_padre_varios_hijos.py` | 6 | Falla: `/padres/me/hijos` no existe |
| UT-API-06 | BE-08 · duplicados y salida sin entrada | `tests/test_asistencia_duplicados.py` | 5 | Falla: guarda duplicados |
| UT-API-07 | BE-09 · política de contraseña | `tests/test_password_policy.py` | 8 | Falla: el módulo no existe |
| UT-API-08 | BE-10 · actor desde el token | `tests/test_actor_token.py` | 3 (asistencia, notas, novedades) | Falla: guarda el `registrado_por` del cuerpo |
| UT-API-09 | BE-11 · permisos del docente | `tests/test_permisos_docente.py` | 5 (con y sin asignación; novedad ajena docente y admin; lectura de notas) | Falla |
| UT-API-10 | BE-12 · correo | `tests/test_correo.py` | 2 (normaliza; rechaza formato inválido) | Falla |
| UT-API-11 | BE-13 · sesión | `tests/test_sesion.py` | 5 (refresco válido, cierre, desactivado, desactivación revoca, enlace reutilizado) | Falla |
| UT-API-12 | BE-14 · avatares | `tests/test_avatar.py` | 4 | Falla: acepta cualquier archivo |
| UT-API-13 | BE-15 · archivos | `tests/test_archivos.py` | 2 (`/static/reportes` 404; boletín sin archivo en `tmp/`) | Falla |
| UT-API-14 | BE-16 · intentos de inicio de sesión | `tests/test_bloqueo_login.py` | 3 (con reloj fijo) | Falla: no hay bloqueo |
| UT-API-15 | BE-17 · sesiones sin Redis | `tests/test_sesion.py` | 3 (login crea, refresh revocado 401, logout revoca) + paso del CI que busca restos de Redis | Falla: hoy usa Redis |
| UT-API-16 | BE-18 · notificaciones | `tests/test_notificaciones.py` | 4 (dispositivo; envío solo a acudientes; sin acudientes; Firebase falla) | Falla: no existe el emisor |
| UT-API-17 | BE-19 · boletín sin notas | `tests/test_boletin.py` | 3 | Falla: genera PDF vacío |
| UT-API-18 | BE-INF-2 · datos de QA | `tests/test_qa_reset_passwords.py` | 1 (con `ENVIRONMENT=production` el script no hace nada) | Falla: el script no existe |

Los nombres de archivo de UT-API-08, 09, 10, 13, 14, 16 y 17 los propone este plan, porque la planeación de correcciones no los fijó. Las pruebas de integración que mencionan BE-07, BE-08, BE-12, BE-13 y BE-17 van en el PR-05.

## 5. Herramientas en VS Code

- Extensión **Python** (Microsoft): pestaña Testing con `pytest` configurado en `tests/`; muestra cada caso y permite depurarlo.
- Extensión **Coverage Gutters** (opcional) para ver en el editor las líneas cubiertas a partir de `coverage.xml`.
- Entorno virtual con Python 3.11: `pip install -r requirements.txt pytest pytest-asyncio pytest-cov httpx`.

## 6. Ejecución (S8)

| Corrida | Fecha | Qué mide |
|---|---|---|
| U1 | 7 nov 2026 | Estado al empezar S8, con las pruebas nuevas que ya existan |
| U2 | 13 nov 2026 | Con las correcciones de S7 y S8 fusionadas; es el resultado oficial del PR-04 |

```bash
git rev-parse --short HEAD          > evidencias/PR-04/api/U1_commit.txt

# 1. Inventario
pytest --collect-only -q -m "not integration" > evidencias/PR-04/api/U1_inventario.txt

# 2. Ejecución con cobertura de líneas y ramas, y reporte JUnit para contar resultados
pytest -m "not integration" -q --durations=10 \
       --cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html \
       --junitxml=evidencias/PR-04/api/U1_junit.xml > evidencias/PR-04/api/U1_pytest.txt
cp coverage.xml evidencias/PR-04/api/U1_coverage.xml
cp -r htmlcov evidencias/PR-04/api/U1_htmlcov

# 3. Cobertura por capa para la Tabla 3
coverage report --include="app/api/*"            > evidencias/PR-04/api/U1_cov_presentacion.txt
coverage report --include="app/application/*"    > evidencias/PR-04/api/U1_cov_aplicacion.txt
coverage report --include="app/infrastructure/*" > evidencias/PR-04/api/U1_cov_infraestructura.txt
coverage report --include="app/core/*"           > evidencias/PR-04/api/U1_cov_nucleo.txt
```

- `-m "not integration"` deja por fuera las pruebas de PostgreSQL (BE-INF-1). Mientras esa marca no exista, el filtro no excluye nada y no afecta.
- `--cov-branch` agrega la cobertura de ramas que pide la plantilla; la meta del MC-01 sigue siendo la de líneas.

## 7. Criterios

| Indicador | Meta | Origen |
|---|---|---|
| Pruebas ejecutadas | 100 % de las planificadas | PR-01 |
| Pruebas aprobadas | ≥ 95 %; en la U2, 100 % de las de correcciones ya fusionadas | PR-01 / MC-01 |
| Cobertura de líneas de `app/` | ≥ 60 % (MC-01); ninguna corrección la puede bajar del 61 % de la línea base | MC-01 y definición de terminado del backend |
| Cobertura de ramas | Sin meta en el MC-01: se registra | — |

## 8. Exclusiones de la medición

| Excluido | Motivo |
|---|---|
| `alembic/` | Migraciones generadas |
| `tests/` | Código de prueba |
| `main.py` | Arranque y montaje de rutas; queda cubierto por `test_app.py` pero no está dentro de `app/` |

## 9. Registro en el PR-04 y defectos

| Resultado | Dónde va |
|---|---|
| Totales de `U2_junit.xml` (tests, failures, errors, skipped) y tiempo | Tabla 1 |
| `U2_inventario.txt` | Tabla 2 |
| Reportes por capa | Tabla 3 y sección 4.2 (archivos con menos cobertura según `term-missing`) |
| Prueba fallida sin corrección planeada | Bug en Azure Boards (etiqueta `pruebas-unitarias`) y Tabla 4 |
| Prueba nueva que falla porque su corrección no se ha fusionado | Tabla 4 con estado «Falla esperada» y la referencia BE-xx |

## 10. Responsables y calendario

| Actividad | Fecha | Responsable |
|---|---|---|
| UT-API-01 (hotfix BE-03) | S7, día 1 | Andrés Acero |
| UT-API-02 a 04, 06 a 08, 10, 12, 15 y 18 | S7 | Andrés Acero |
| UT-API-05, 09, 11, 13, 14, 16 y 17 | S8 | Andrés Acero |
| U1 | 7 nov | Mariana Cortés |
| U2 y columna API del PR-04 | 13 – 14 nov | Mariana Cortés · revisa Samuel Sierra |

## 11. Definición de terminado

- [ ] Las 18 pruebas nuevas existen, fallaron antes de su corrección y pasan después.
- [ ] U1 y U2 ejecutadas, con evidencias en `evidencias/PR-04/api/`.
- [ ] Cobertura de líneas de `app/` ≥ 61 %.
- [ ] Columna API del PR-04 diligenciada y revisada por el líder de pruebas.
