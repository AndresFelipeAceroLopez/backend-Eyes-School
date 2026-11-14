# Informe final de pruebas — Backend (API FastAPI) · Eyes School

> **Qué es este documento:** el consolidado de **todas** las pruebas ejecutadas sobre la API entre
> el 09 y el 10 de noviembre de 2026, con sus números, su veredicto contra el criterio que les
> aplica y la evidencia que los respalda. Está pensado para alimentar los informes PR-03 a PR-08.
> **Componente:** `backend-Eyes-School` · rama `developer`
> **Ejecutó:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> **Ninguna evidencia contiene contraseñas, tokens ni URLs con credenciales.**
>
> Los detalles de cada corrida están en [`corrida-2026-11-09.md`](corrida-2026-11-09.md); el estado
> por tipo de prueba, en [`informe-pruebas-backend.md`](informe-pruebas-backend.md). Este documento
> los resume y da el veredicto final.

---

## 1. Resumen ejecutivo

Se ejecutaron **nueve suites** de prueba de cinco tipos distintos. Siete cumplen su criterio, una
lo cumple parcialmente y una quedó sin un criterio aplicable.

| # | Suite | Tipo | Resultado | Veredicto |
|---|---|---|---|---|
| 1 | Unitarias y de componente | Caja blanca | **201 de 201** | ✅ |
| 2 | Integración con PostgreSQL 18 | Caja blanca | **55 de 55** | ✅ |
| 3 | Integración por HTTP (Newman) | Caja negra | 68 casos · **0 fallos funcionales** | ✅ |
| 4 | Contrato OpenAPI (schemathesis) | Caja negra | 46 operaciones · **1 defecto real** | ✅ corregido |
| 5 | Análisis estático (10 controles) | Estática | 9 de 10 · B4 pendiente de captura | ✅ |
| 6 | Carga, 50 usuarios (CP-NF-001) | No funcional | Tiempo ✔ · errores ✖ | 🟡 |
| 7 | Estrés, 200 usuarios (CP-NF-002) | No funcional | Degrada y **se recupera** | ✅ |
| 8 | DAST con OWASP ZAP (CP-NF-003) | Seguridad | **0 alertas altas y 0 medias** | ✅ |
| 9 | Preflight de entornos | Humo | Producción y QA sanos | ✅ |

**Cobertura de líneas de `app/`: 79,6 %** (meta MC-01: ≥ 60 %; línea base del 25/10/2026: 61 %).

**Defectos:** 23 registrados como issues de GitHub, **21 cerrados** con causa raíz documentada.
Quedan dos abiertos y **ninguno de los dos es un defecto de código**: la rotación de una credencial
y una decisión de dimensionamiento de infraestructura.

---

## 2. Pruebas unitarias y de componente (PR-04)

Verifican esquemas, servicios, autorización y seguridad **sin base de datos**, reemplazando
repositorios, Firebase, disco y reloj por dobles.

| Indicador | Línea base (25/10) | **Final** | Meta |
|---|---|---|---|
| Casos ejecutados | 26 | **201** | 100 % de los planificados ✔ |
| Aprobados | 26 | **201** | ≥ 95 % ✔ |
| Fallidos / con error / omitidos | 0 | **0 / 0 / 0** | — |
| Cobertura de líneas de `app/` | 61 % | **79,6 %** | ≥ 60 % ✔ |

### Evolución durante la campaña

| Momento | Casos | Qué se agregó |
|---|---|---|
| U1 (09/11, commit `0af4531`) | 154 | Las 18 pruebas UT-API-01 a 18 de las correcciones BE-03 a BE-19 |
| Tras BE-INF-2 | 159 | Las tres protecciones nuevas del script de contraseñas de QA |
| Tras DEF-039 y servicios CRUD | 199 | 13 del id fuera de rango + 27 de servicios sin cubrir |
| **Final** | **201** | Las dos cabeceras de seguridad que marcó ZAP |

### Cobertura por capa

| Capa | Cobertura |
|---|---|
| Núcleo (`app/core`) | 91 % |
| Aplicación (`app/application`) | 69 % → mejorada con los servicios CRUD |
| Presentación (`app/api`) | 66 % |
| Infraestructura | 62 % → 54–82 % al sumar las de integración |

> **Hallazgo de proceso:** el CI solo le enviaba a SonarQube la cobertura de las unitarias. Los
> repositorios se prueban con las de **integración**, y esa cobertura se descartaba. Se corrigió:
> el job de integración genera su propio informe y SonarQube los suma. Eso, más las pruebas
> nuevas, llevó la cobertura de 72 % a 79,6 %.

**Evidencia:** `evidencias/PR-04/api/U1_*` (pytest, JUnit, coverage.xml, HTML y por capa).

---

## 3. Pruebas de integración con PostgreSQL (PR-05)

Contra **PostgreSQL 18.6 real**, con el esquema creado desde los modelos y los seeds cargados.
Cada prueba corre en una transacción que se revierte.

| Indicador | Resultado |
|---|---|
| Casos ejecutados | **55** |
| Aprobados | **55** |
| Fallidos | **0** |
| Tiempo | ~40 s |

| Archivo | Casos | Correcciones que cubre |
|---|---|---|
| `integration/test_notas_novedades.py` | 18 | BE-06, BE-10, BE-11, BE-14, BE-15, BE-18, BE-19 |
| `integration/test_acceso_a_datos.py` | 19 | BE-03, BE-04, BE-05, BE-07, BE-08 y DEF-039 |
| `integration/test_auth_sesiones.py` | 17 | BE-09, BE-12, BE-13, BE-16, BE-17 |
| `integration/test_humo.py` | 1 | La app arranca contra la base real |

**Evidencia:** `evidencias/PR-05/api/I1_pytest_integracion.{txt,xml}`.

---

## 4. Integración por HTTP contra QA — Newman (PR-05)

Caja negra contra la API de QA desplegada, con usuarios y datos reales del entorno.

| Indicador | Resultado |
|---|---|
| Peticiones | **83 · 0 fallidas** |
| Casos CP-INT ejecutados | **68** de 69 |
| Aserciones | 159 · 55 fallidas |
| **Fallos funcionales (código y cuerpo)** | **0** |
| Fallos por tiempo de respuesta | 55 |
| Duración | 2 min 56 s · respuesta media 2 s |

**Todas las correcciones quedaron verificadas por HTTP contra un entorno real**, no solo con
dobles: BE-03 (200 en vez de 500), BE-04 (403 y 400), BE-06 (422 con 5.1), BE-07 (padre con dos
hijos), BE-08 (409 y 400), BE-09 (400 y 422), BE-10, BE-11 (403 sin asignación), BE-12 (409 con el
correo en otras mayúsculas), BE-15 (404 por `/static`) y BE-19.

**Las 55 fallas son de entorno, no de código:** todas son la misma aserción, `responde en ≤ 800 ms`.
Quedan enlazadas al defecto de rendimiento (#43) y **no se registraron como 55 defectos**.

**Caso pendiente:** CP-INT-052 (boletín sin notas) se omite porque la variable
`id_estudiante_sin_notas` del entorno está vacía.

**Evidencia:** `evidencias/PR-05/api/I1_newman.xml`.

---

## 5. Contrato OpenAPI — schemathesis (PR-05)

Generación automática de peticiones a partir del contrato publicado en `/openapi.json`.

| Resultado | Cantidad |
|---|---|
| Operaciones probadas | 46 de 107 (**solo las de lectura**) |
| Casos generados | 385 |
| **ST101 · Error de servidor** | **4** |
| ST108 · Respuesta no conforme al esquema | 25 |
| ST103 · Código de estado no documentado | 50 |
| ST205 / ST203 / ST105 · Cabeceras y tipos | 4 |

> **Por qué solo lectura:** schemathesis genera peticiones aleatorias y se ejecutó con un token de
> administrador. Un `DELETE` generado al azar habría borrado datos de QA.

**Los ST101 destaparon un defecto real (DEF-039):** un id fuera del rango de PostgreSQL devolvía
**500 en 9 de 9 endpoints** con parámetro de id. Se verificó a mano con el entorno en reposo para
descartar que fuera secuela de la prueba de carga. **Corregido y verificado en QA:** ahora responde
**422 «Valor fuera del rango permitido»**.

Los ST103 y ST108 **no son defectos**: son respuestas de error legítimas (401, 403) que los routers
no declaran en el contrato. Es deuda de documentación y entra al plan de remediación.

**Evidencia:** `evidencias/PR-05/api/I1_schemathesis.txt`.

---

## 6. Análisis estático (PR-03)

Dos corridas: E1 el 09/11 y E2 el 10/11 tras las correcciones.

| # | Control | Herramienta | E1 | **E2** | Umbral | |
|---|---|---|---|---|---|---|
| B1 | Reglas del CI | ruff 0.17.3 | 0 | **0** | 0 | ✔ |
| B2 | Perfil ampliado | ruff | 166 | 166 | Informativo | — |
| B3 | Seguridad del código | bandit 1.9.4 | 0A/0M/1B | **0A/0M/1B** | 0 altas o medias | ✔ |
| B4 | Calidad general | SonarQube Cloud | — | Pendiente de captura | Quality Gate | 🟡 |
| B5 | Complejidad CCN > 15 | lizard 1.25.0 | Ninguna | **Ninguna** | Informativo | ✔ |
| B6 | Duplicación | jscpd 4.3.0 | 0,54 % | **0,54 %** | ≤ 3 % | ✔ |
| B7 | Tamaño | pygount | 3 646 líneas / 80 archivos | — | — | — |
| B8 | **Secretos** | gitleaks 8.24.2 | **6 hallazgos** | **0** | 0 | ✔ |
| B9 | Dependencias | pip-audit 2.10.1 | 0 | **0** | 0 críticas o altas | ✔ |
| B10 | Cobertura | pytest-cov | 68 % | **79,6 %** | ≥ 60 % | ✔ |

### B8 fue el control que más información dio

E1 encontró **6 secretos en el historial de git**, y con dos correcciones a lo que decía la
planeación:

1. **El alcance era mayor:** además de `.env`, el secreto estaba en **`create_admin.py`**, y el
   commit `476c0de` que lo contenía **estaba en `main`, es decir en producción**.
2. **Los commits listados eran equivocados:** no eran `847a48c` ni `c5621f7`, sino `6fdf2cc`,
   `ccaec1c`, `db5565c`, `e21775a` y `476c0de`.

Tras reescribir el historial y silenciar los hallazgos conocidos por huella, E2 reporta
`no leaks found` sobre 60 commits.

> **Advertencia que debe quedar en el informe:** B8 en verde **no significa que el riesgo esté
> cerrado**. La contraseña de la base de Render **no se rotó**, así que esas credenciales siguen
> abriendo la base de producción. Los clones antiguos, los forks y las referencias `refs/pull/*`
> de GitHub conservan los commits originales. Ver el defecto #22.

Un falso positivo identificado y documentado: la regla `generic-api-key` leía el `"key": "<nombre>"`
del formato de Postman como si declarara una clave. Marcado en `.gitleaks.toml` con su motivo.

**Evidencia:** `evidencias/PR-03/api/E1_*` y `E2_*`.

---

## 7. Rendimiento: carga y estrés (PR-06)

### 7.1 Decisión del PO sobre el criterio

La meta del MC-01 es p95 ≤ 800 ms, pero QA está en `chilecentral` y su base en Render (Oregón). La
misma consulta tarda **1 526 ms en QA y 411 ms en producción**, un factor de 3,7: medir QA contra
800 ms es medir la distancia, no la aplicación. El equipo decidió **no mover la Web App ni la base**.

**Decisión del PO del 10/11/2026 (opción A): umbral ajustado para QA.**

| Criterio | MC-01 (producción) | Aprobado para QA |
|---|---|---|
| p95 de navegación | ≤ 800 ms | **≤ 3 000 ms** |
| p95 de `POST /auth/login` | — | ≤ 11 000 ms |
| Errores | < 1 % | **< 1 % (sin cambio)** |

### 7.2 Carga con 50 usuarios — CP-NF-001

Se ejecutó dos veces: antes y después de optimizar el acceso a datos.

| Métrica | S1 (antes) | **S2 (después)** | Cambio |
|---|---|---|---|
| Peticiones por segundo | 16,05 | **23,83** | **+48 %** |
| p95 global | 3 068 ms | **1 825 ms** | **−41 %** |
| p95 de navegación | 2 720 ms | **1 650 ms** | **−39 %** |
| Media | 2 161 ms | **1 075 ms** | **−50 %** |
| Mediana | 1 237 ms | **677 ms** | **−45 %** |
| p95 de las que respondieron | 3 990 ms | **1 350 ms** | −66 % |
| Errores | 8,05 % | 10,90 % | +35 % |

**Veredicto contra el criterio aprobado:**

| Criterio | Umbral QA | S2 | |
|---|---|---|---|
| p95 de navegación | ≤ 3 000 ms | **1 650 ms** | ✔ |
| p95 global | ≤ 3 000 ms | **1 825 ms** | ✔ |
| p95 de `POST /auth/login` | ≤ 11 000 ms | 13 190 ms | ✖ |
| Errores | < 1 % | 10,90 % | ✖ |

**CP-NF-001 se cumple en tiempo de respuesta y no se cumple en errores.**

### 7.3 Estrés hasta 200 usuarios — CP-NF-002

| Indicador | Resultado |
|---|---|
| Usuarios máximos | 200 |
| Peticiones | 22 450 a 20,8/s |
| Errores | 11,35 % |
| p95 | 12,49 s |
| **Recuperación** | **Sí**: volvió a su línea base **sin reiniciar** ✔ |

**CP-NF-002 se cumple.** La API degradó pero no se rompió, siguió sirviendo el 89 % de las
lecturas y se recuperó sola al bajar la carga, que es exactamente lo que pide el criterio.

### 7.4 Dónde estaba el tiempo, y qué se corrigió

Este fue el hallazgo técnico más útil de la campaña. Se midió **dentro del contenedor de QA**:

| Operación | Mediana |
|---|---|
| **Abrir una conexión nueva** (TCP + TLS + autenticación) | **1 233 ms** |
| Consulta sobre una conexión ya abierta | **164 ms** |

Abrir una conexión cuesta **siete veces** lo que una consulta. Con eso, los 866 ms de coste de base
de `GET /cursos` se explicaban: `pool_pre_ping` hacía un `SELECT 1` antes de entregar **cada**
conexión (164 ms), la consulta (164 ms), el `commit` que `get_db` hace **también en los GET**
(164 ms) y el resto entre el parse de la sentencia y el reset del pool.

**Cambios aplicados** (todos configurables por entorno):

| Antes | Ahora | Por qué |
|---|---|---|
| `pool_pre_ping=True` | `False` + `pool_recycle=1800` | El pre-ping costaba un viaje entero por petición |
| `pool_size=10`, `max_overflow=20` | `30` + `10` | Conexiones **fijas**: cada una de desbordamiento se abre en pleno pico y cobra 1,2 s |

**Resultado: coste de base de `GET /cursos` de 866 ms a 301 ms (−65 %).**

### 7.5 Por qué el error subió aunque todo mejoró

k6 no manda un número fijo de peticiones: manda las que el sistema acepte. Al volverse más rápido
el backend, los mismos 50 usuarios generan **más carga** (23,8 req/s frente a 16,1) y el cuello de
botella se movió. Lo confirma el desglose:

- Las peticiones que **sí** responden lo hacen en 1 350 ms de p95, frente a 3 990 ms antes.
- Las que fallan siguen muriendo en el máximo de **60,0 s**: no responden lento, se quedan colgadas.
- El `POST /auth/login` **empeoró** mientras la navegación mejoraba. bcrypt consume **CPU**; las
  lecturas solo esperan a la base.

**Conclusión: ya no faltan conexiones, falta CPU.** El siguiente techo es el plan de App Service, y
eso es dimensionamiento de infraestructura y una decisión de costo, no de QA.

**Evidencia:** `evidencias/PR-06/api/S1_k6_carga.*`, `S2_k6_carga.*` y `S1_k6_estres.*`.

---

## 8. Seguridad dinámica — OWASP ZAP (PR-06, CP-NF-003)

Escaneo DAST de la API de QA con ZAP 2.17.0, cargando el `openapi.json` para recorrer los 62
endpoints reales (102 URLs) y no solo lo que encontrara enlazado.

| Riesgo | Alertas |
|---|---|
| **Alto** | **0** ✔ |
| **Medio** | **0** ✔ |
| Bajo | 2 |
| Informativo | 1 |

**CP-NF-003 se cumple** (criterio: 0 alertas altas).

> **Spider y análisis pasivo, sin escaneo activo, a propósito:** el activo manda cargas de ataque a
> cada endpoint y, con POST, PUT y DELETE, habría creado y borrado datos en QA. Es el equivalente
> al *baseline scan* que se usa en integración continua.

### Las dos alertas bajas, corregidas

| Alerta | Instancias | Corrección |
|---|---|---|
| `X-Content-Type-Options` ausente | 4 | Middleware que lo fija en todas las respuestas |
| `Strict-Transport-Security` ausente | 5 | Middleware, solo sobre HTTPS |

`nosniff` importa más de lo que parece en esta API: los avatares se sirven públicos desde
`/static/avatars` (BE-14). Sin esa cabecera, un navegador puede ignorar el `Content-Type` y
ejecutar como HTML un archivo subido por un usuario. La validación de BE-14 ya impide subir algo
que no sea imagen; esto es la segunda barrera.

**Evidencia:** `evidencias/PR-06/api/S1_zap_baseline.{html,json}`.

---

## 9. Entornos: lo que se descubrió y se corrigió

### 9.1 Las dos bases iban por detrás de su código

El defecto DEF-036 (la API de QA respondía 500 en todo lo que consultaba la base) **no era de
configuración**, como suponía la planeación: **a la base de QA le faltaba la migración
`b7d2e9a41c03`**, y el código desplegado ya necesitaba las tablas `sesiones_refresco` y
`dispositivos`. **La misma falta estaba en producción.**

| Entorno | Antes | **Después** |
|---|---|---|
| Producción (`eyesschool_wru2`) | `a1b2c3d4e5f6` | **`b7d2e9a41c03`** ✔ |
| QA (`qaeyesschool`) | `a1b2c3d4e5f6` | **`b7d2e9a41c03`** ✔ |

La migración se probó antes contra una réplica con la misma estructura y volumen (21 tablas, 110
usuarios, 103 estudiantes): **2,9 s**, aditiva, sin pérdida de datos, reversible con `downgrade` y
**compatible con el código viejo**, lo que permitió migrar **sin ventana de caída**.

> **Para el PR-01:** el diagnóstico de BE-INF-4 empezaba por la contraseña y el formato de
> `DATABASE_URL`, y no mencionaba la revisión de Alembic. Se agregó un **paso 0**:
> `alembic current`. Un entorno cuyo código va por delante de su base da exactamente estos
> síntomas —`/docs` y las validaciones responden, todo lo que consulta la base falla— y fue lo que
> pasó en los dos entornos.

### 9.2 Preflight final de los dos entornos

| Comprobación | Producción | QA |
|---|---|---|
| `/docs` | 200 ✔ | 200 ✔ |
| `GET /cursos/` sin token | 200 ✔ | 200 ✔ |
| Login con correo inexistente | 401 ✔ | 401 ✔ |
| Login con cuerpo inválido | — | 422 ✔ |
| Login real del admin | — | **200 con token** ✔ |

**BE-INF-4 / DEF-036 cerrado** con el criterio de aceptación completo.

> **Corrección al criterio:** pedía «`GET /cursos/` sin token → 401 o 403», y estaba equivocado.
> Ese endpoint es **público a propósito** —es el catálogo que el formulario de registro de
> acudientes necesita antes de iniciar sesión— y está declarado así en
> `tests/test_authorization.py`. Pedir 401 ahí habría hecho fallar el preflight de un entorno sano.

### 9.3 Otros hallazgos de entorno

| Hallazgo | Estado |
|---|---|
| Producción no era la Web App que decía la planeación: es `api-eyesschool` (westus3). Se retiró el workflow sobrante | Corregido |
| Las Web Apps usan dominios regionales (`<app>-<hash>.<región>-01`), no el nombre corto | Documentado |
| El `.env` local no conecta: le falta `?ssl=require` | Documentado |
| `/home/site/wwwroot` no tiene el código: Oryx lo extrae a `/tmp/<id>` | Documentado |
| El despliegue de QA fallaba por credenciales OIDC caducadas | Corregido por el equipo |

---

## 10. Defectos (PR-07)

**23 defectos** registrados como issues de GitHub del repositorio del backend (#22 a #44).

> **Corrección de herramienta:** la planeación daba por hecho que irían a **Azure Boards**, pero el
> equipo usa Azure DevOps **solo para el componente móvil**. Los defectos del backend se gestionan
> en **GitHub Issues**, donde el pull request los cierra con `Closes #n` y el enlace al commit
> queda automático.

| Métrica | Valor |
|---|---|
| Total | **23** |
| Cerrados | **21** |
| Abiertos | **2** |
| **Críticos abiertos** | **1** |

### Causa raíz de los 21 cerrados

| Causa | Cantidad | Qué dice |
|---|---|---|
| **Diseño** | 11 | Reglas de negocio que nunca se especificaron |
| Codificación | 4 | Errores al escribir el código |
| Requisitos | 4 | El requisito existía en los clientes pero no en la API |
| Datos | 1 | Contraseñas en un comentario del seed |
| Entorno | 1 | Base por detrás del código |

Que la mayoría sea de **diseño** y no de codificación es el dato más útil para la retrospectiva:
no fueron descuidos al programar, fueron reglas que no se definieron antes de construir.

### Los dos que siguen abiertos

| # | Defecto | Por qué sigue abierto |
|---|---|---|
| **#22** | **DEF-001 · Credenciales en el historial de git** | **Crítico.** El historial está limpio y gitleaks en verde, pero **la contraseña de Render no se rotó**: esas credenciales siguen abriendo la base de producción. No depende de código |
| **#43** | DEF-038 · Rendimiento con 50 usuarios | Mejorado un 65 % en coste de base y un 48 % en throughput. La causa quedó acotada al **plan de App Service**: decisión de costo del PO |

### Defectos nuevos encontrados durante esta campaña

| Defecto | Lo encontró | Estado |
|---|---|---|
| DEF-037 · `create_admin.py` con credenciales, también en `main` | gitleaks (B8) | Cerrado |
| DEF-038 · La API falla con 50 usuarios | k6 (CP-NF-001) | Abierto |
| DEF-039 · Un id fuera de rango devuelve 500 | schemathesis | Cerrado y verificado en QA |

---

## 11. Trazabilidad: cada corrección y la prueba que la demuestra

| Corrección | Unitaria | Integración | HTTP en QA | Estado |
|---|---|---|---|---|
| BE-01 · Secretos | — | — | — | 🔴 Historial limpio, **credencial sin rotar** |
| BE-03 · Dashboard 500 | `test_dashboard.py` | `test_acceso_a_datos.py` | CP-INT-060 | ✅ |
| BE-04 · Asistencia ajena | `test_authorization.py` | `test_acceso_a_datos.py` | CP-INT-036 a 039 | ✅ |
| BE-05 · Vínculo de otro padre | `test_authorization.py` | `test_acceso_a_datos.py` | CP-INT-065 | ✅ |
| BE-06 · Escala de notas | `test_notas_validacion.py` | `test_notas_novedades.py` | CP-INT-043, 046 | ✅ |
| BE-07 · Varios hijos | `test_padre_varios_hijos.py` | `test_acceso_a_datos.py` | CP-INT-062 a 064 | ✅ |
| BE-08 · Duplicados | `test_asistencia_duplicados.py` | `test_acceso_a_datos.py` | CP-INT-031, 033, 034 | ✅ |
| BE-09 · Contraseña | `test_password_policy.py` | `test_auth_sesiones.py` | CP-INT-020, 028 | ✅ |
| BE-10 · Actor desde el token | `test_actor_token.py` | las tres | CP-INT-035 | ✅ |
| BE-11 · Permisos del docente | `test_permisos_docente.py` | `test_notas_novedades.py` | CP-INT-047, 048, 056 | ✅ |
| BE-12 · Correo | `test_correo.py` | `test_auth_sesiones.py` | CP-INT-007, 018, 077 | ✅ |
| BE-13 · Sesión | `test_sesion.py` | `test_auth_sesiones.py` | CP-INT-008 | ✅ |
| BE-14 · Avatares | `test_avatar.py` | `test_notas_novedades.py` | — | ✅ + `nosniff` |
| BE-15 · Archivos | `test_archivos.py`, `test_boletin.py` | `test_notas_novedades.py` | CP-INT-071 | ✅ |
| BE-16 · Bloqueo de login | `test_bloqueo_login.py` | `test_auth_sesiones.py` | — | ✅ |
| BE-17 · Sesiones sin Redis | `test_sesion.py` | `test_auth_sesiones.py` | CP-INT-008 | ✅ |
| BE-18 · Notificaciones | `test_notificaciones.py` | `test_notas_novedades.py` | — | 🟡 Falta `FIREBASE_CREDENTIALS_JSON` en QA |
| BE-19 · Boletín sin notas | `test_boletin.py` | `test_notas_novedades.py` | CP-INT-053 | ✅ |
| BE-INF-1 · PostgreSQL real | — | 55 casos | — | ✅ |
| BE-INF-2 · Datos de QA | `test_qa_reset_passwords.py` | — | — | ✅ |
| BE-INF-3 · Sonar y gitleaks | — | — | — | 🟡 gitleaks ✅, Sonar pendiente de captura |
| BE-INF-4 · Entorno de QA | Preflight | — | Preflight | ✅ |
| DEF-039 · Id fuera de rango | `test_id_fuera_de_rango.py` | `test_acceso_a_datos.py` | Verificado en QA | ✅ |

---

## 12. Correcciones a las planeaciones que estas pruebas obligaron

Las pruebas no solo encontraron defectos en el código: encontraron **supuestos equivocados en la
propia planeación de QA**. Quedan documentados porque afectan a los informes.

| Documento | Qué decía | Qué se comprobó |
|---|---|---|
| Correcciones (BE-01) | Los secretos estaban en `.env`, commits `847a48c` y `c5621f7` | También en `create_admin.py`, y los commits eran otros cinco |
| Correcciones (BE-INF-4) | Los 500 de QA eran de configuración de `DATABASE_URL` | Faltaba la migración de la base. El criterio pedía además 401 en un endpoint que es público a propósito |
| Correcciones (D-3) | Producción era el workflow `main_apieyeschool.yml` | Es `api-eyesschool` (westus3). Se retiró el sobrante |
| Integración | Variable `DATABASE_URL`, esquema desde `schema.sql` | Es `TEST_DATABASE_URL` y el esquema sale de los modelos |
| Sistema | El umbral de 800 ms aplicaba a QA | QA está 3,7x más lejos de su base: el PO aprobó un umbral ajustado |
| Gestión de defectos | Los defectos irían a Azure Boards | Azure DevOps es solo para móvil: van a GitHub Issues |
| Unitarias | La cobertura la daban las unitarias | El CI descartaba la de integración, que es la que cubre los repositorios |

---

## 13. Lo que queda, y de quién es

| # | Pendiente | Responsable | Bloquea |
|---|---|---|---|
| 1 | **Rotar la contraseña de la base en Render** y actualizar `DATABASE_URL` en las dos Web Apps | Andrés | Cierre de #22. Es un riesgo vivo sobre datos de menores |
| 2 | Avisar al equipo que **vuelva a clonar** tras la reescritura del historial | Mariana | Que nadie reintroduzca los commits con el secreto |
| 3 | Cambiar la **`QA_PASSWORD`** al terminar la campaña | Mariana | — |
| 4 | **Fusionar el PR #21** a producción (base ya migrada) | Andrés | Que las correcciones lleguen a los usuarios |
| 5 | **Decidir el plan de App Service** con el costo sobre la mesa | Sergio (PO) | Cierre de #43 y CP-NF-001 |
| 6 | **Capturas de SonarQube** para B4 | Mariana | Cierre del PR-03 |
| 7 | **`FIREBASE_CREDENTIALS_JSON`** en QA | Andrés | BE-18 punta a punta y CP-ACE-067, 085, 086 |
| 8 | Fijar `id_estudiante_sin_notas` en el entorno de Newman | Mariana | CP-INT-052 |
| 9 | Declarar las respuestas de error en los routers | Andrés | ST103 y ST108 del contrato |
| 10 | Evaluar quitar el `commit` en las peticiones de solo lectura | Andrés | ~164 ms por `GET` |

---

## 14. Herramientas y versiones

| Herramienta | Versión | Para qué |
|---|---|---|
| pytest + pytest-asyncio + pytest-cov | — | Unitarias e integración |
| PostgreSQL | 18.6 | Base real de las de integración |
| ruff | 0.17.3 | Estilo y errores |
| bandit | 1.9.4 | Seguridad del código |
| pip-audit | 2.10.1 | Dependencias vulnerables |
| lizard | 1.25.0 | Complejidad ciclomática |
| jscpd | 4.3.0 | Duplicación |
| **gitleaks** | **8.24.2** | Secretos en el historial |
| newman | 6.2.3 | Integración por HTTP |
| schemathesis | 4.33.1 | Contrato OpenAPI |
| **k6** | **2.3.0** | Carga y estrés |
| **OWASP ZAP** | **2.17.0** | DAST |
| SonarQube Cloud | — | Calidad general (pendiente de captura) |
