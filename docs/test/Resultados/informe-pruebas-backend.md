# Informe de pruebas — Backend (API FastAPI) · Eyes School

> **Tipo de documento:** informe de estado. Dice, para cada tipo de prueba, qué pedía su planeación, qué se ejecutó, qué resultó y **qué falta** para poder cerrar su entregable (PR-03 a PR-08).
> **Corte:** 09/11/2026, 21:10. **Rama:** `developer` · commit `06bf07f`.
> **Elaboró:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> Los resultados numéricos detallados están en [`corrida-2026-11-09.md`](corrida-2026-11-09.md). Este documento es el resumen por tipo de prueba y la lista de pendientes.

---

## 1. Tablero general

| Tipo de prueba | Entregable | Planeación | Ejecutado | Resultado | Estado |
|---|---|---|---|---|---|
| Unitarias y de componente | PR-04 | `Unitarias/` | **Sí** (U1) | 154/154 · cobertura 68 % | ✅ Listo para U2 |
| Integración con PostgreSQL | PR-05 | `Integracion/` | **Sí** (I1 local) | 53/53 contra PostgreSQL 18.6 | ✅ Listo para I2 |
| Integración por HTTP (Newman) | PR-05 | `Integracion/` | No | 70 casos generados, 0 corridos | ⏳ Desbloqueado hoy |
| Contrato OpenAPI (schemathesis) | PR-05 | `Integracion/` | No | — | ⏳ Desbloqueado hoy |
| Análisis estático | PR-03 | `Codigo_Estatico/` | **Sí** (E1) | 9 de 10 controles; B4 sin correr | 🟡 Falta SonarQube |
| Sistema: carga y estrés (k6) | PR-06 | `Sistema/` | No | k6 instalado, scripts listos | ⏳ Desbloqueado hoy |
| Sistema: DAST con OWASP ZAP | PR-06 | `Sistema/` | No | ZAP no instalado | ⏳ Desbloqueado hoy |
| Sistema: OWASP Top 10 | PR-06 | `Sistema/` | Parcial | Lo cubierto por unitarias e integración | 🟡 Falta la tabla |
| Gestión de defectos | PR-07 | `GestionDefectos/` | Parcial | 21 defectos identificados, 0 en Azure Boards | 🔴 Sin registrar |
| Aceptación (UAT) | PR-08 | `uat/` | No | Sesión en S10 | ⏳ Según cronograma |

**Lectura corta:** todo lo que se puede automatizar y correr sin el entorno de QA está hecho y en verde. Lo que faltaba estaba bloqueado por dos cosas, y **las dos se resolvieron hoy**: la API de QA ya responde y ya se conoce su URL. Lo que queda abierto de verdad es **BE-01** (la contraseña de Render sigue sin rotar) y **el registro de los 21 defectos en Azure Boards**.

---

## 2. Unitarias y cobertura (PR-04)

**Lo que pedía la planeación:** las 18 pruebas nuevas UT-API-01 a 18, cada una escrita antes de su corrección; cobertura de líneas ≥ 61 %; corridas U1 (7 nov) y U2 (13 nov).

**Lo que hay:** 154 casos en 21 archivos, **todos aprobados**, en 23 s. Cobertura de líneas **68 %** y de ramas registrada. Las 18 pruebas nuevas existen, así que las correcciones BE-03 a BE-19 y BE-INF-2 están implementadas.

| Capa | Cobertura |
|---|---|
| Núcleo (`app/core`) | 91 % |
| Aplicación (`app/application`) | 69 % |
| Presentación (`app/api`) | 66 % |
| Infraestructura | 62 % |
| **Total `app/`** | **68 %** |

**Qué falta:**

1. **U2, la corrida oficial del PR-04** (13 nov): se repite con `bash scripts/qa/correr_unitarias.sh U2` sobre el commit de `release/1.1.0`. Es lo que va en las Tablas 1 a 4 del PR-04; U1 es solo la línea base.
2. **Llenar las Tablas 1 a 4 del PR-04** con `U2_junit.xml`, `U2_inventario.txt` y los reportes por capa.
3. **Nada de código.** La capa de infraestructura al 62 % es el punto más bajo; no incumple ninguna meta, pero es donde conviene mirar si se quiere subir la cobertura.

---

## 3. Integración (PR-05)

### 3.1 Contra PostgreSQL real — hecho

**Lo que pedía la planeación:** carpeta `tests/integration/` con marca `integration`, esquema y seeds cargados una vez por sesión, cada prueba en una transacción que se revierte, y `postgres:18` en el CI.

**Lo que hay:** **53 casos, todos aprobados** contra PostgreSQL 18.6, en 31 s.

| Archivo | Casos | Correcciones que cubre |
|---|---|---|
| `integration/test_notas_novedades.py` | 18 | BE-06, BE-10, BE-11, BE-14, BE-15, BE-18, BE-19 |
| `integration/test_acceso_a_datos.py` | 17 | BE-03, BE-04, BE-05, BE-07, BE-08 |
| `integration/test_auth_sesiones.py` | 17 | BE-09, BE-12, BE-13, BE-16, BE-17 |
| `integration/test_humo.py` | 1 | La app arranca contra la base real |

### 3.2 Por HTTP contra QA — pendiente, ya desbloqueado

**Lo que pedía la planeación:** 69 casos CP-INT en una colección Newman contra la API de QA, más `schemathesis` contra `/openapi.json` para la Tabla 6.

**Lo que hay:** la colección se genera con `python tests/newman/generar_coleccion.py` (**70 casos**), `newman 6.2.3` instalado y la API de QA ya respondiendo con el código nuevo (62 endpoints). **Cero casos corridos.**

**Qué falta:**

1. **`QA_PASSWORD`.** Es el único dato que falta. Correr `scripts/qa_reset_passwords.py` contra `qaeyesschool` para fijarla (ver sección 6 de este informe) y después:
   ```bash
   export QA_API=https://apieyeschool-q-g4hfgrgvepbecacc.chilecentral-01.azurewebsites.net/api/v1
   export QA_PASSWORD=...        # nunca en un archivo versionado
   bash scripts/qa/correr_integracion.sh I1
   ```
2. **`id_estudiante_sin_notas`** en `tests/newman/qa.postman_environment.json`: si queda vacía, CP-INT-052 (boletín sin notas, BE-19) se omite.
3. **`schemathesis`**: no está instalado (`pip install schemathesis`) y necesita un `TOKEN_ADMIN` recién generado, que caduca en 30 min.
4. **I2, la corrida oficial** (13 nov), y las Tablas 1, 2, 3 y 6 del PR-05.
5. **Los casos CP-INT-075 y 076** (web↔API y móvil↔API) no son de este componente: van en las planeaciones de la web y de la app.

---

## 4. Análisis estático (PR-03)

**Lo que pedía la planeación:** 10 controles B1 a B10 con sus umbrales, dos corridas (E1 el 7 nov, E2 el 13 nov) y la validación de la regla propia de gitleaks.

**Lo que hay:** E1 completa salvo SonarQube.

| # | Control | Resultado | Umbral | |
|---|---|---|---|---|
| B1 | ruff (reglas del CI) | 0 hallazgos | 0 | ✔ |
| B2 | ruff perfil ampliado | 166 informativos | Informativo | — |
| B3 | bandit | 0 altas · 0 medias · 1 baja | 0 altas o medias | ✔ |
| B4 | **SonarQube Cloud** | **No ejecutado** | Quality Gate aprobado | 🟡 |
| B5 | Complejidad (CCN > 15) | Ninguna función | Informativo | ✔ |
| B6 | Duplicación | 0,54 % (3 clones) | ≤ 3 % | ✔ |
| B7 | Tamaño | 3 646 líneas, 80 archivos | — | — |
| B8 | Secretos (gitleaks) | **0** tras la reescritura | 0 | ✔ |
| B9 | Dependencias (pip-audit) | 0 vulnerabilidades | 0 críticas o altas | ✔ |
| B10 | Cobertura | 68 % | ≥ 60 % | ✔ |

**B8 cambió hoy.** E1 encontró 6 secretos en el historial (BE-01, ampliado a `create_admin.py`). Después de reescribir el historial con `git filter-repo` y marcar los hallazgos en `.gitleaksignore`, gitleaks reporta `no leaks found`. **Esto no significa que el riesgo esté cerrado**: ver la sección 7.

**Qué falta:**

1. **B4, SonarQube Cloud.** El `SONAR_TOKEN` ya está creado; falta que el CI corra sobre `developer` y guardar del Overview: calificaciones, bugs, vulnerabilidades, hotspots, code smells, complejidad cognitiva, Technical Debt y Debt Ratio (Tablas 1, 2 y 3 del PR-03).
2. **Plan de remediación de B2.** Los 166 informativos no bloquean, pero hay que decidir qué hacer con ellos. Propuesta: silenciar `TRY003` en `pyproject.toml` (son 101 de los 166 y es el estilo del proyecto: `NotFoundException("...")`), aplicar `ruff --fix` a los 5 `UP017`, y dejar el resto en el backlog.
3. **E2** (13 nov) con prefijo `E2_`, para la sección de evolución del PR-03.
4. **Confirmar que gitleaks corre en el CI con `fetch-depth: 0`.** En local solo alcanzó 23 de 41 commits porque el clon no tiene todas las ramas; la corrida que vale es la del CI.

---

## 5. Sistema (PR-06)

**Lo que pedía la planeación:** carga y estrés con k6 (CP-NF-001 y 002), DAST con OWASP ZAP (CP-NF-003), la tabla OWASP Top 10 y los casos de secretos, archivos públicos, dependencias y usuario desactivado.

**Lo que hay:** los scripts `tests/carga/carga_50.js` y `tests/carga/estres.js`, `k6 v2.3.0` instalado y varios riesgos OWASP ya cubiertos por pruebas automatizadas (control de acceso con BE-04, BE-05, BE-07 y BE-11; autenticación con BE-09, BE-13 y BE-16; carga de archivos con BE-14). **Nada ejecutado:** el PR-06 estaba programado para S9 (15–21 nov).

**Qué falta:**

1. **`QA_PASSWORD`, `QA_DOCENTE` y `QA_ID_ESTUDIANTE_CLASE`**, y generar `usuarios_ds02.json` con `tests/carga/generar_usuarios_ds02.py`.
2. **OWASP ZAP** no está instalado y el DAST no se ha corrido. Nunca contra producción.
3. **`FIREBASE_CREDENTIALS_JSON`** en la Web App de QA: sin esa variable, BE-18 no envía nada y los casos de notificación del PR-06 y de la app no se pueden probar de verdad. Hoy está vacía.
4. **No hay endpoint `/health`.** La prueba de humo usa `GET /api/v1/cursos`, que es público a propósito. Si se quiere un chequeo que no consulte la base, hay que agregarlo; hoy no existe y no está planeado.
5. **Métricas de Azure** (CPU, memoria, 5xx) durante la carga, para la Tabla 3.
6. **Correr la carga fuera del horario de pruebas manuales**, para no afectar a la web y a la app.

---

## 6. Datos y entorno de QA (BE-INF-2 y BE-INF-4)

**BE-INF-4 quedó resuelto hoy.** El preflight contra la URL real da `/docs` → 200, `GET /cursos/` → 200 con datos, login inexistente → 401 y cuerpo inválido → 422: las consultas a la base funcionan y los 500 de DEF-020 desaparecieron. El despliegue de `developer` dejó allí el código con las correcciones.

| Entorno | URL |
|---|---|
| QA | `apieyeschool-q-g4hfgrgvepbecacc.chilecentral-01.azurewebsites.net` (región chilecentral) |
| Producción | `api-eyesschool-hrf2gsg7hyf9dacq.westus3-01.azurewebsites.net` (región westus3) |

La Web App `ApiEyeSchool` quedó sin uso y su workflow `main_apieyeschool.yml` se retiró (decisión D-3). Esto corrige lo que decía la planeación de correcciones, que daba ese workflow como el de producción.

**Qué falta:**

1. **Anotar las dos URLs en la sección de entornos del PR-01.** Varias planeaciones siguen diciendo «URL pendiente de definir».
2. **Fijar `QA_PASSWORD`** corriendo `scripts/qa_reset_passwords.py --base qaeyesschool` desde el computador que tiene el backend, con el `.env` de producción **fuera de la carpeta** y `DATABASE_URL` fijada en la terminal (regla 1.4). Resultado esperado: 110 usuarios cambiados. **Este es el paso que desbloquea Newman, schemathesis, k6 y los E2E de la web.**
3. **Confirmar los datos de QA:** 21 tablas, 110 usuarios y 103 estudiantes, y que DS-01 (`roberto.diaz@gmail.com`, un hijo) y DS-03 (`rosa.perez@gmail.com`, dos hijos) existan.
4. **Verificar que la `SECRET_KEY` de QA sea distinta de la de producción.**

---

## 7. Defectos (PR-07) y el estado real de BE-01

**21 defectos identificados, 0 registrados en Azure Boards.** Es el pendiente más grande del informe, porque sin el `AB#` de cada bug no se pueden llenar las Tablas 2 y 3 del PR-07 ni cumplir la definición de terminado de ninguna corrección.

| Defecto | Estado al 09/11/2026 |
|---|---|
| DEF-002 a DEF-018 (BE-03 a BE-19) | **Corregidos y probados** en `developer`. Falta verificarlos en QA y moverlos a Done |
| DEF-019 (H-08, contraseñas en el seed) | **Corregido**: los comentarios ya no están |
| DEF-020 (BE-INF-4, QA en 500) | **Resuelto hoy**; se cierra con el preflight como evidencia |
| DEF-001 y DEF-021 (BE-01) | **Abiertos.** Ver abajo |

### BE-01: qué se hizo y qué sigue abierto

Hecho hoy: `create_admin.py` ya lee la URL de la configuración; el historial se reescribió con `git filter-repo` sobre las 5 ramas y `.env` y `create_admin.py` no aparecen en ningún commit; gitleaks da `no leaks found`.

**Lo que sigue abierto, y es lo importante:**

1. **La contraseña de la base de Render NO se rotó** (decisión del equipo del 09/11/2026). Las credenciales que estaban en el historial **siguen abriendo la base de datos de producción**, que contiene datos de menores de edad.
2. **Reescribir el historial no las desactiva.** Los clones antiguos de cada integrante, cualquier fork y las referencias `refs/pull/*/head` que GitHub conserva de los pull requests siguen teniendo los commits originales. Esas refs no se pueden reescribir con un push: hay que pedirle a GitHub Support que las purgue.
3. **Por eso `.gitleaksignore` lleva una advertencia escrita** en vez de una fecha de rotación: el CI quedó verde, pero el secreto sigue vivo. Quien retome BE-01 debe cambiar esa contraseña en Render y actualizar `DATABASE_URL` en las dos Web Apps.
4. **El equipo tiene que volver a clonar.** Un `git pull` sobre un clon viejo falla o reintroduce los commits con el secreto.

> **Resumen honesto:** el Quality Gate de B8 pasa y el repositorio está limpio, pero el riesgo de BE-01 no está cerrado. Lo único que lo cierra es rotar la contraseña.

---

## 8. Aceptación (UAT, PR-08)

La API no tiene pantallas: el PO la acepta a través de la web y de la app. La sesión está programada para S10 (22–28 nov).

**Lo que ya se puede confirmar:** de las 13 correcciones que condicionan escenarios CP-ACE, **las 13 están fusionadas en `developer` y desplegadas en QA**. Es decir, ningún escenario de aceptación queda bloqueado por el backend.

**Qué falta:**

1. **Congelar la versión** (`release/1.1.0`) y no desplegar nada durante la sesión.
2. **`pg_dump` de la base de QA** antes de la sesión.
3. **Recargar los datos** la mañana de la sesión y entregar `QA_PASSWORD` por canal privado.
4. **`FIREBASE_CREDENTIALS_JSON`** y una notificación de prueba al POCO X7: sin eso, CP-ACE-067, 085 y 086 (BE-18) no se pueden aceptar.
5. **Andrés con el Log stream abierto** durante la sesión.
6. Después: cambiar `QA_PASSWORD` y volver a correr el script.

---

## 9. Lo que falta, en orden de urgencia

| # | Qué | Quién | Bloquea |
|---|---|---|---|
| 1 | **Rotar la contraseña de la base en Render** y actualizar `DATABASE_URL` en las dos Web Apps | Andrés | Cierre de BE-01 / DEF-001 y DEF-021. Es un riesgo vivo sobre datos de menores |
| 2 | **Avisar al equipo que reclone**; pedir a GitHub Support la purga de `refs/pull/*` | Mariana | Que nadie reintroduzca los commits con el secreto |
| 3 | **Abrir el PR del hotfix a `main`** (BE-03 + `create_admin.py` + retiro del workflow) | Andrés | El inicio del estudiante sigue roto en producción |
| 4 | **Fijar `QA_PASSWORD`** con `qa_reset_passwords.py` | Samuel | Newman, schemathesis, k6 y los E2E de la web |
| 5 | **Registrar los 21 defectos en Azure Boards** con su `AB#` | Mariana | PR-07 y la definición de terminado de cada corrección |
| 6 | **Correr el CI sobre `developer`** y guardar las capturas de SonarQube | Samuel | B4 del PR-03 |
| 7 | **Configurar `FIREBASE_CREDENTIALS_JSON`** en QA | Andrés | BE-18 en el PR-06 y en la UAT |
| 8 | **Anotar las dos URLs de Azure en el PR-01** | Mariana | Varias planeaciones dicen «pendiente de definir» |
| 9 | **Instalar OWASP ZAP** y correr el DAST | Samuel | CP-NF-003 del PR-06 |
| 10 | **I2, U2 y E2** sobre `release/1.1.0` | Mariana | Los números oficiales de PR-03, PR-04 y PR-05 |

---

## 10. Trazabilidad: cada corrección y la prueba que la demuestra

| Corrección | Unitaria | Integración | Estado |
|---|---|---|---|
| BE-01 · secretos | — | — | 🔴 Historial limpio, **contraseña sin rotar** |
| BE-03 · dashboard 500 | `test_dashboard.py` | `test_acceso_a_datos.py` | ✅ en `developer` · ⏳ en `main` |
| BE-04 · asistencia ajena | `test_authorization.py` | `test_acceso_a_datos.py` | ✅ |
| BE-05 · vínculo de otro padre | `test_authorization.py` | `test_acceso_a_datos.py` | ✅ |
| BE-06 · escala de notas | `test_notas_validacion.py` | `test_notas_novedades.py` | ✅ |
| BE-07 · varios hijos | `test_padre_varios_hijos.py` | `test_acceso_a_datos.py` | ✅ |
| BE-08 · duplicados | `test_asistencia_duplicados.py` | `test_acceso_a_datos.py` | ✅ |
| BE-09 · contraseña | `test_password_policy.py` | `test_auth_sesiones.py` | ✅ |
| BE-10 · actor desde el token | `test_actor_token.py` | las tres de integración | ✅ |
| BE-11 · permisos del docente | `test_permisos_docente.py` | `test_notas_novedades.py` | ✅ |
| BE-12 · correo | `test_correo.py`, `test_normalizar_correos.py` | `test_auth_sesiones.py` | ✅ |
| BE-13 · sesión | `test_sesion.py` | `test_auth_sesiones.py` | ✅ |
| BE-14 · avatares | `test_avatar.py` | `test_notas_novedades.py` | ✅ |
| BE-15 · archivos | `test_archivos.py`, `test_boletin.py` | `test_notas_novedades.py` | ✅ |
| BE-16 · bloqueo de login | `test_bloqueo_login.py` | `test_auth_sesiones.py` | ✅ |
| BE-17 · sesiones sin Redis | `test_sesion.py` | `test_auth_sesiones.py` | ✅ |
| BE-18 · notificaciones | `test_notificaciones.py` | `test_notas_novedades.py` | 🟡 Código listo; falta la credencial de Firebase en QA |
| BE-19 · boletín sin notas | `test_boletin.py` | `test_notas_novedades.py` | ✅ |
| BE-INF-1 · PostgreSQL real | — | 53 casos | ✅ |
| BE-INF-2 · datos de QA | `test_qa_reset_passwords.py` | — | 🟡 Script listo; falta correrlo en QA |
| BE-INF-3 · Sonar y gitleaks | — | — | 🟡 gitleaks ✅; SonarQube sin correr |
| BE-INF-4 · entorno de QA | Preflight | — | ✅ Resuelto el 09/11/2026 |
