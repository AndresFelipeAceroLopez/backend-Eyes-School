# Cierre del backend — ejecución de la planeación BC-01 a BC-12

> **Fechas:** 13 y 14/11/2026 · **Ejecutó:** Mariana Cortés (QA) · **Rama:** `developer` (QA: `apieyeschool-q`) → `main` (producción: `api-eyesschool`)
> **Planeación:** «Planeación de cierre — Backend (API FastAPI)», del 13/11 al 21/11/2026.
> **Insumo de:** PR-03 a PR-08 v0.4.

---

## 1. Resumen

**Todas las tareas de la planeación quedaron ejecutadas, y no queda ningún defecto del backend abierto (23 de 23 cerrados).** La regresión final pasa completa en QA y el mismo código está en producción.

| Tarea | Estado | Evidencia principal |
|---|---|---|
| BC-01 Credencial de Render (#22) | ✅ Cerrado: la instancia filtrada ya no existe | 3.1 |
| BC-02 Rendimiento con 50 usuarios (#43) | ✅ **S3 cumple**: 0,08 % de errores, p95 1,07 s | `S3_k6_carga.*` |
| BC-03 Firebase | ✅ Credenciales puestas en las dos Web Apps | 3.3 |
| BC-04 Archivos de reportes (N-23) | ✅ En QA y en producción; 8/8 reportes descargan | `BC04_descarga_reportes_qa.txt` |
| BC-05 Pendiente o desactivada (N-31) | ✅ En QA y en producción | CP-INT-005 y 010 |
| BC-06 Newman | ✅ **81/81 CP-INT; I3: 184/184 aserciones, 0 fallos** (funcionales y de tiempo) | `I3b_newman.*` |
| BC-07 Contrato OpenAPI | ✅ 0 ST101/ST103/ST108 en local (2 978 casos) y en QA | `I3_schemathesis*.txt` |
| BC-08 SonarQube | ✅ Quality Gate OK, deuda 0 · faltan capturas | 3.8 |
| BC-09 Producción | ✅ Dos despliegues (#54 y #59); humo 9/9 | `BC09_humo_produccion*.txt` |
| BC-10 A09 y A10 | ✅ Cumplen · falta captura del *Log stream* | 3.10 |
| BC-11 Datos para los informes | ✅ | 3.11 |
| BC-12 Cierre de la campaña | ✅ 110 usuarios, 0 temporales, datos restaurados | 3.12 |

**Lo único que queda en manos del equipo:**

- Las capturas de pantalla de SonarQube, del *Log stream* y de las métricas de Azure y Render durante S3.
- El buzón de QA.
- Confirmar que la `SECRET_KEY` de producción es distinta de la filtrada (3.1).

La sección 5 lista también las **incidencias** de la ejecución, todas resueltas.

---

## 2. Cambios entregados

| PR | Contenido | Estado |
|---|---|---|
| [#47](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/47) | Contrato OpenAPI (BC-07), bcrypt fuera del bucle de eventos (BC-02), registro de eventos (BC-10), Newman completo (BC-06), renumeración (BC-11), arreglo del CI | ✅ |
| [#48](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/48) | N-23 (archivos de reportes en la base) y N-31 (motivo de la cuenta inactiva) | ✅ |
| [#49](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/49) | Los 2 code smells de SonarQube (deuda → 0) | ✅ |
| [#50](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/50), [#53](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/53), [#55](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/55), [#56](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/56) | Informe, scripts de verificación y restauración, schemathesis en solo lectura | ✅ |
| [#51](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/51) | Pool de 12 conexiones (DEF-038) | ✅ |
| [#52](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/52) | Migración `c4e1f7a9d2b8` desplegada antes que el código que la usa | ✅ |
| [#57](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/57) | QA y producción en servidores distintos: correcciones a la documentación | ✅ |
| [#58](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/58) | Rendimiento de los 3 endpoints que pasaban de 3 s; cobertura medida con `greenlet` | ✅ |
| [#54](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/54), [#59](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/59) | `developer → main`: v1.1.0 y luego N-23, N-31 y rendimiento | ✅ En producción (`7c5302a`) |

**Hallazgos en el CI:**
- `pip-audit` empezó a fallar el 13/11 por un CVE publicado ese día contra `dnspython` 2.9.1. Se actualizó a 2.9.2. Al cortarse el job antes de subir `coverage.xml`, SonarQube analizaba con la mitad de la cobertura: ahora el artefacto se sube siempre, `main.py` entra en la medición y la acción de Sonar pasa a v6.
- **coverage.py medía de menos todo el acceso a datos:** SQLAlchemy async corre en greenlets, y sin `concurrency = greenlet` coverage perdía las líneas que van después de cada `await` a la base. Al configurarlo, la cobertura global con ramas pasó del 76 % al 80 % sin escribir pruebas nuevas.

---

## 3. Detalle por tarea

### 3.1 BC-01 · Credencial de la base filtrada (DEF-001, #22) — cerrado

| Hecho | Cómo se comprobó |
|---|---|
| La URL filtrada en el historial era de `dpg-dae7si5bedkc73bltec0` / `eyesschool_tr7a` | Comparada con el `.env` local |
| Producción usa **otra** instancia: `dpg-dbkht01srm7s73c08bs0` / `eyesschool_wru2` | Consola SSH de `api-eyesschool`, 14/11 |
| QA usa **otra** instancia: `dpg-dbki7dh42hec73cn2d1g` / `qaeyesschool` | Consola SSH de `apieyeschool-q`, 14/11 |
| La instancia filtrada **ya no existe** en Render | Panel de Render, Mariana Cortés, 14/11 |
| El `.env` local se cambió y el historial ya no tiene el secreto | Mariana Cortés, 14/11 · `git filter-repo` + gitleaks en verde |

No hizo falta rotar la contraseña: la que se filtró era de una instancia que ya no existe. El DNS no sirve como prueba, porque Render resuelve cualquier host al mismo proxy de entrada.

**Queda por confirmar:** la `SECRET_KEY` de `api-eyesschool` tiene que ser distinta de la que estaba en el `.env` filtrado. Si fuera la misma, cualquiera podría firmar tokens de administrador: en ese caso se genera otra y se reabre el #22. `scripts/qa/verificar_rotacion.py` queda para la próxima rotación.

### 3.2 BC-02 · Rendimiento con 50 usuarios (DEF-038, #43) — cerrado

**La premisa de la planeación («falta CPU en el App Service») no se sostenía.** Una carga corta que registró el código de **cada** petición (11/11, 50 usuarios, 5 min) mostró:

- **Primeros 180 s:** 0 errores en 5 368 peticiones.
- **Después:** **una caída total de ~90 s**, con 500 y 502 mezclados, de la que se recuperó sola.

Los 2 104 errores de S2 equivalen a una sola caída de ese tipo.

**Causa (métricas de Render del 13/11):** cada entorno tiene su propio servidor de Render, del plan más chico: **0,1 CPU, 256 MB y 97 conexiones**. Con el pool anterior (30 + 10), una carga de 50 usuarios abría hasta 40 conexiones, es decir, 40 procesos de PostgreSQL compitiendo por una décima de núcleo y 256 MB, y la base dejaba de responder. No se pudo confirmar si el límite fue la memoria o la CPU, porque Render ya no muestra el 11/11. La CPU que faltaba era la de la base.

| Corrección | Efecto |
|---|---|
| bcrypt corría **dentro** del bucle de eventos (PR #47) | Medido: 3 logins congelaban **605 ms** toda la API; en un hilo, 21 ms. Límite `BCRYPT_CONCURRENCIA=2` |
| **Pool de 12 conexiones fijas, 0 de desbordamiento** (PR #51) | Una prueba en `test_config.py` impide volver a pasarse |
| «Quitar el commit de las lecturas» (opción B) | No se aplicó: cerrar la transacción con `ROLLBACK` cuesta el mismo viaje que el `COMMIT` |
| Bajar el costo de bcrypt | No se hizo (lo prohíbe la planeación) |

**Corrida S3** (14/11, 02:31–02:44 UTC, mismo guion que S1 y S2):

| Criterio | Umbral QA | S1 | S2 | **S3** |
|---|---|---|---|---|
| Errores | < 1 % | 8,05 % | 10,90 % | **0,08 %** ✔ |
| p95 de navegación | ≤ 3 000 ms | 2 720 ms | 1 650 ms | **1 070 ms** ✔ |
| p95 global | ≤ 3 000 ms | 3 068 ms | 1 825 ms | **1 130 ms** ✔ |
| p95 del login | ≤ 11 000 ms | — | 13 190 ms | **10 310 ms** ✔ |

- De los 13 errores, **11 fueron del cliente**: sin respuesta, terminaron a la vez tras ~243 s (el límite es 60 s) y coinciden con un congelamiento de 4 minutos del equipo que ejecutaba la prueba. **Del servidor: 2 respuestas 502 de 15 786.**
- Durante la corrida se consultó producción cada 5 s: 93 consultas, 0 fallos.
- **CP-NF-001: Aprobado** con el umbral del PO. Se anularon los 1 011 registros de asistencia que creó la carga.
- Falta para el PR-06: la captura de CPU y memoria de Azure y de Render del 14/11, de 02:30 a 02:45 UTC.

### 3.3 BC-03 · Firebase

`FIREBASE_CREDENTIALS_JSON` está configurada en `apieyeschool-q` y en `api-eyesschool` (Mariana Cortés, 14/11). Las claves privadas que se compartieron en el chat de trabajo el 13/11 (QA `ff6a273b…`, producción `87446535…`) **deben estar revocadas** en Google Cloud Console si no son las que se configuraron; nunca se guardaron en ningún archivo ni repositorio. Las pruebas de la notificación en el teléfono (CP-INT-057 y 058 de punta a punta) son de la planeación móvil (MC-04).

### 3.4 BC-04 · Archivos de reportes (N-23) — opción A

- El contenido va a la tabla `reporte_archivos`, con la **misma ruta** que la API devolvía como clave: la web no cambia. La descarga lee de la base y, por compatibilidad, del disco.
- Los reportes del seed apuntaban a archivos que nunca existieron. La migración `c4e1f7a9d2b8` les generó un PDF **rotulado como documento de ejemplo**: 8 reportes en QA y los mismos 8 del seed en producción. Ningún reporte real se tocó.
- **Prueba de integración:** subir → borrar el disco (lo que hace un despliegue) → descargar → 200 con el mismo contenido.
- **QA, después de migrar y desplegar:** los **8 reportes con archivo descargan su PDF** (dos vueltas) y los 2 en estado «Pendiente» responden 404 «El reporte no tiene archivo adjunto». En Newman, CP-INT-069 a 071 (subir, descargar y `/static` sin token → 404) pasan con el almacenamiento en la base.
- **Queda para el equipo:** repetir CP-SIS-088 y CP-ACE-096 (app).

### 3.5 BC-05 · Cuenta pendiente o desactivada (N-31)

| Caso | Antes | Ahora |
|---|---|---|
| Docente o admin autorregistrado, sin validar | 401 `Usuario inactivo` | **403** `Cuenta pendiente de validación. Un administrador debe aprobarla.` |
| Cuenta desactivada por el admin | 401 `Usuario inactivo` | **403** `Cuenta desactivada. Comunícate con el administrador del colegio.` |
| Contraseña equivocada (cualquier estado) | 401 `Credenciales inválidas` | Igual: sin la contraseña no se revela el estado |

La cuenta autorregistrada nace con `pendienteValidacion = true` en el mismo INSERT, y la marca se quita cuando el admin la activa o la desactiva. Verificado en QA con CP-INT-005 (pendiente → 403) y CP-INT-010 (desactivada → «Cuenta desactivada»). **La app y la web deben mostrar el `detail`** (planeación móvil, MC-03).

### 3.6 BC-06 · Newman

| Corrida | Fecha | CP-INT | Aserciones | Fallos funcionales | Fallos de tiempo (≤ 3 000 ms) |
|---|---|---|---|---|---|
| I2 | 13/11 | 75 | 183 | 0 | 3: CP-INT-016 (3,5 s), 025 (7,1 s), 051 (8,0 s) |
| I3 | 14/11, recién desplegado | 75 | 184 | 0 | 1: CP-INT-024 (4,7 s, arranque en frío) |
| **I3b** | **14/11, QA caliente** | **75** | **184** | **0** | **0** |

- **81 de 81 CP-INT con ejecución:** 75 en Newman contra QA y 6 solo en pytest, que no se pueden hacer por HTTP. Esos son CP-INT-012 a 015, porque el token llega por correo, CP-INT-049, que es del repositorio, y CP-INT-057, el envío push. Pasan en la integración (64/64).
- CP-INT-052 se ejecuta solo: busca un estudiante sin notas → 404 con el mensaje de BE-19.
- CP-INT-006, 009, 010, 029, 058 y 072 corren sobre una **cuenta temporal** que la colección crea y borra.
- Los 3 casos lentos de la I2 se corrigieron en el PR #58:

| Endpoint | Causa | Consultas | QA |
|---|---|---|---|
| Eliminar usuario (025) | ~20 DELETE seguidos | 20 → **2** (una sentencia con CTEs) | 7,1 s → **1,2 s** |
| Registro (016) | Comprobaciones y modificación por separado | 10 → **6** | 3,6 s → **2,9 s** |
| Boletín (051) | Importación de fpdf en frío, PDF en el bucle de eventos | 6 (igual) | 8,0 s → **2,0 s** |

- Resultado por caso: `evidencias/PR-05/api/I3b_newman.xml` (JUnit) e `I3b_newman.html`.

### 3.7 BC-07 · Contrato OpenAPI

| Hallazgo (I1, QA, 10/11) | Corrección |
|---|---|
| ST103 × 50: 401/403/404 no declarados | Errores reales declarados con `ErrorOut {"detail": str}` sobre el esquema generado |
| ST108 × 25: fechas sin zona | Fechas de los `Out` con zona UTC (`…Z`); las horas de `Horario` son locales y se documentan con su patrón |
| ST205 × 3: `Allow` incompleto en los 405 | `Allow` con todos los métodos de la URL |
| ST105 × 1: el boletín no declaraba PDF | `application/pdf` declarado |
| Al corregir aparecieron ST202, ST201 y ST204 | Ids `Entero32` validados antes de la base; `?fecha=` solo `AAAA-MM-DD`; `PUT /estudiantes/me` ya no cae en `/{id}` |

| Corrida | Casos | ST101 · ST103 · ST108 | Resto |
|---|---|---|---|
| I2 en QA (13/11) | 5 927 | **0 · 0 · 0** | 4 ST112, del cliente (anexo A) |
| **I3 local, código final (14/11)** | **2 978** | **0 · 0 · 0** | **0: los 2 978 pasan** |
| **I3 en QA, código final (14/11)** | **2 075** | **0 · 0 · 0** | **0: los 2 075 pasan** |

**Efecto en los clientes:** las fechas llegan como `2026-11-03T03:03:37Z`.

### 3.8 BC-08 · SonarQube Cloud (rama `developer`)

| Métrica | Valor |
|---|---|
| Quality Gate | **OK** (también en todos los PR del cierre) |
| Bugs · Vulnerabilidades · Hotspots | 0 · 0 · 0 (100 % revisados) |
| Code smells · Deuda técnica | **0 · 0 min** (eran 2 y 15 min; PR #49) |
| Ratio de deuda | 0,0 % |
| Complejidad cognitiva · ciclomática | 341 · 642 (análisis del 14/11 00:04 UTC) |
| Duplicación | 0,0 % |
| Líneas de código | 4 037 |

Faltan las capturas de *Overview*, *Issues* y *Measures*.

### 3.9 BC-09 · Despliegue a producción

| Despliegue | Contenido | Migración |
|---|---|---|
| **#54** (14/11, `48c0b2c`) | v1.1.0: BE-03…BE-19, calidad y seguridad, contrato, pool | No hizo falta: producción ya estaba en `b7d2e9a41c03` |
| **#59** (14/11, `7c5302a`) | N-23, N-31 y rendimiento | `c4e1f7a9d2b8` ya aplicada (ver la incidencia 5.3) |

| Humo | Antes de #54 | Después de #54 | Después de #59 |
|---|---|---|---|
| `GET /docs` → 200 | ✔ | ✔ | ✔ |
| `/padres/me/hijos` en el contrato | ✖ | ✔ | ✔ |
| `GET /cursos` → 200 | ✔ | ✔ | ✔ |
| `X-Content-Type-Options: nosniff` | ✖ | ✔ | ✔ |
| Correo inexistente → 401 | ✔ | ✔ | ✔ |
| Login del admin · cuenta temporal · **6.º intento → 429** · cuenta borrada | — | **✔ ✔ ✔ ✔** (Mariana Cortés, 03:31 UTC) | Sin cambios en ese código |

Evidencia: `BC09_humo_produccion_ANTES.txt`, `BC09_humo_produccion.txt` (9/9) y `BC09_humo_produccion_despliegue2.txt`.

**Efecto visible:** producción responde CORS con `*` y sin credenciales, igual que QA. Si algún cliente usa `withCredentials`, hay que definir `CORS_ORIGINS` en Azure.

### 3.10 BC-10 · A09 y A10

**A10 (SSRF): cumple.** Las únicas llamadas salientes van a Resend (URL fija) y a Firebase (SDK). fpdf no carga imágenes y el avatar se abre desde bytes. **0 rutas descargan URLs del usuario.** Hallazgo lateral, ya corregido: el nombre del usuario se insertaba sin escapar en el HTML del correo de recuperación.

**A09 (registro): cumple en la app.** Antes, los `logger.info` no salían en Azure y un 403 o un 404 no dejaban rastro. Ahora todos los logs llevan fecha y hora:

- Los 401, 403, 404 y 429 se registran con método, ruta, estado y origen, **sin** query string, cabeceras ni cuerpo.
- El login fallido registra el id del usuario y el número de intento, sin el correo ni la contraseña.

Las pruebas lo verifican con un token en la query y en la cabecera. Falta la captura del *Log stream*.

### 3.11 BC-11 · Datos para los informes

**Defectos (GitHub Issues #22 a #44):**

| Dato | Valor |
|---|---|
| Total · cerrados · abiertos | **23 · 23 · 0** |
| Reabiertos | 0 |
| Renumeración | DEF-020…023 → **DEF-036…039** (#41 a #44) |
| Causa raíz | Comentada en los 23 issues: **Diseño 12 · Codificación 5 · Requisitos 4 · Datos 1 · Entorno 1** |
| Tiempo de corrección | BE-03 a BE-19: identificados el 28 y el 30/10, corregidos el 09/11 (**10 a 12 días**). DEF-036, 037 y 039: el mismo día. DEF-038: 4 días (10 → 14/11). DEF-001: 17 días (28/10 → 14/11) |

> `closedAt` no sirve para medir el tiempo de corrección: los issues se crearon el 10/11 después de corregir.

| Issue | DEF | Causa | Commit |
|---|---|---|---|
| #22 | DEF-001 | Codificación (secreto versionado) | `filter-repo` + instancia eliminada |
| #23 | DEF-002 | Codificación | `fca0e93` |
| #24, #25, #28, #30–#37 | DEF-003, 004, 007, 009–016 | Diseño | `88cd544` |
| #26, #29, #38, #39 | DEF-005, 008, 017, 018 | Requisitos | `88cd544` |
| #27 | DEF-006 | Codificación | `88cd544` |
| #40 | DEF-019 | Datos | `abd7691` |
| #41 | DEF-036 | Entorno | `b7d1ceb` (migración) |
| #42 | DEF-037 | Codificación | `06bf07f` / `83d9e22` |
| #43 | DEF-038 | Diseño (pool sin dimensionar para el servidor) | `#47`, `#51` |
| #44 | DEF-039 | Codificación | `4d486a9` |

**Pruebas (código final):**

| Suite | Resultado |
|---|---|
| Unitarias | **239 en 31,6 s** |
| Integración (PostgreSQL 18) | **64 en 42,8 s** |
| Total | 303 en 31 archivos |

| Capa | Líneas | Ramas | Funciones |
|---|---|---|---|
| `api` | 75,2 % | 51,3 % | 36,8 % |
| `application` | 84,5 % | 60,8 % | 62,9 % |
| `core` | 93,6 % | 90,9 % | 96,4 % |
| `domain` (interfaz abstracta) | 0,0 % | — | 0,0 % |
| `infrastructure` | 83,5 % | 28,1 % | 58,5 % |
| `main.py` | 94,9 % | 71,4 % | 83,3 % |
| **Total** | **82,9 %** (2 629/3 170) | **56,2 %** (245/436) | **55,8 %** (207/371) |

La cobertura de funciones de `api` es baja porque cada endpoint cuenta como función y muchos solo se ejecutan en Newman, que no mide cobertura.

### 3.12 BC-12 · Cierre de la campaña

- **QA: 110 usuarios y 0 temporales** después de todas las corridas.
- Anulados todos los registros de asistencia que crearon las pruebas de carga: 403 del 11/11 y 1 011 del 14/11.
- Datos alterados por schemathesis **restaurados** (incidencia 5.1): especializaciones activas 10/10 y novedades 1 a 10, con sus valores del seed.
- Falta el buzón de QA del equipo (CP-INT-012, 014 y CP-ACE-016). Mientras tanto, la recuperación de contraseña se cubre en pytest.

---

## 4. Definición de terminado

- [x] #22, #43, N-23 y N-31 cerrados.
- [x] 81/81 CP-INT de la API ejecutados con resultado por caso; 0 fallas funcionales (y 0 de tiempo en la I3b).
- [x] Schemathesis con 0 ST101, ST103 y ST108.
- [ ] Capturas de SonarQube en el PR-03. **La deuda ya está en el informe (0).** Faltan las capturas.
- [x] Producción desplegada con el humo en verde.

---

## 5. Incidencias durante la ejecución

Se registran porque cambiaron datos o conclusiones. Todas quedaron resueltas.

### 5.1 schemathesis escribió en QA (13/11, ~20:17–20:31)

Una repetición se lanzó con `--include-method GET` y `--include-path-regex`. schemathesis **combina esos filtros con OR**, así que probó también 11 operaciones de escritura con el token de admin durante unos 12 minutos.

| Tabla | Daño | Restauración |
|---|---|---|
| `profesores` 1–3 | `estado` → «Inactivo» | Por API |
| `asignaciones` 1, 3, 6, 10 | desactivadas | Por API |
| `especializaciones` 1, 3, 6, 10 | desactivadas; la 1 sin descripción | API + `restaurar_qa.py` (14/11) |
| `novedades` 1, 2, 5, 9 | borradas | `restaurar_qa.py`, con los ids y valores del seed (14/11) |

**Corrección de proceso:** schemathesis va siempre contra un `openapi.json` recortado a GET (`scripts/qa/openapi_solo_lectura.py`) y con `--exclude-checks unsupported_method,allow_header_conformance`. Esos dos checks mandan a propósito métodos no declarados, o comparan `Allow` con el contrato recortado. El comando quedó así en la planeación de integración.

### 5.2 El informe y el runbook decían que QA y producción compartían servidor

Se tomó del runbook sin comprobarlo, y con eso se concluyó que cada carga en QA tumbaría producción. Las consolas de Azure mostraron tres instancias distintas (3.1). Se corrigieron el runbook, la planeación, este informe, `config.py`, dos pruebas y el #43 (PR #57). La corrección del pool no cambia: el límite es por servidor.

### 5.3 La migración `c4e1f7a9d2b8` se aplicó en producción desde la consola equivocada (14/11, ~03:20 UTC)

Los comandos para QA se corrieron en la consola SSH de `api-eyesschool`, porque no comprobaban la Web App antes de migrar. La restauración de QA sí se detuvo: su guardia comparó la base y se negó. Impacto, revisado desde la misma consola:

- Los 8 reportes **del seed** recibieron el PDF de ejemplo; sus archivos nunca existieron.
- 0 cuentas marcadas como pendientes de validación.
- Ningún dato real cambió.

La migración es aditiva y el código de ese momento no la leía. **Faltó el respaldo previo que pedía BC-09.** Desde entonces, `restaurar_qa.py` exige `--base` y comprueba `WEBSITE_SITE_NAME`, y el runbook pide `echo $WEBSITE_SITE_NAME` antes de cualquier comando.

### 5.4 Otras

- **El vigilante de producción abortó la primera S3** al tomar como caída el 307 de `/cursos/`. Se corrigió a `/cursos` y se relanzó.
- **El commit del pool borró por error `scripts/qa/verificar_rotacion.py`** (un `git commit -a` con el archivo ausente de la copia de trabajo). Se repuso en el #53.
- **La segunda corrida del humo sobrescribió la evidencia 9/9.** Se restauró con su contenido original y la nueva quedó como `BC09_humo_produccion_despliegue2.txt`.

---

## Anexo A · schemathesis contra QA

**I2** (13/11, GET, `--checks all`, `I2_schemathesis.txt`): 5 927 casos; **0 ST101, ST103, ST105, ST108 y ST201–ST205**.

- Los 4 ST112 (tiempo) son del cliente: marcan de 147 s a 921 s con un límite de 60 s, y coinciden con un corte de red del equipo.
- 12 operaciones solo vieron 401 porque el token venció a los 30 min de una corrida de 68. Se repitieron con token nuevo (`I2_schemathesis_repeticion.txt`): 606 casos, 0 ST101/ST103/ST108/ST112.

**I3** (14/11, código final, contrato recortado a GET, `--exclude-checks unsupported_method,allow_header_conformance`, 10 ejemplos por operación para terminar antes de que venza el token; `I3_schemathesis.txt`): **2 075 casos, 2 075 pasan**. Coverage 46/46, Fuzzing 46/46 y Stateful 10/10. Las 6 operaciones que «solo devuelven 401/403» son `/me` y los dashboards de otros roles: con token de admin, el 403 es lo correcto.
