# Cierre del backend — ejecución de la planeación BC-01 a BC-12

> **Fecha:** 13/11/2026 · **Ejecutó:** Mariana Cortés (QA) · **Rama:** `developer` (QA: `apieyeschool-q`)
> **Planeación:** «Planeación de cierre — Backend (API FastAPI)», del 13/11 al 21/11/2026.
> **Insumo de:** PR-03 a PR-08 v0.4.

---

## 1. Resumen

| Tarea | Estado | Qué falta y de quién |
|---|---|---|
| BC-01 Rotar la contraseña de Render (#22) | 🟡 Herramienta lista | **Andrés:** rotar en Render y en las dos Web Apps; luego correr `scripts/qa/verificar_rotacion.py` |
| BC-02 Rendimiento con 50 usuarios (#43) | 🟡 Corrección parcial desplegada | Revisar las métricas de Render del 11/11 22:40–22:43 UTC **antes** de la corrida S3 (ver 3.2) |
| BC-03 Firebase en QA y producción | 🔴 Bloqueado | Las claves compartidas en el chat del 13/11 **deben revocarse**; generar otras y ponerlas en Azure (ver 3.3) |
| BC-04 Archivos de reportes (N-23) | 🟢 Hecho en código (PR #48, opción A) | Migrar `qaeyesschool` y luego fusionar el #48 |
| BC-05 Cuenta pendiente o desactivada (N-31) | 🟢 Hecho en código (PR #48) | Igual que BC-04; la app debe mostrar el `detail` (MC-03) |
| BC-06 Newman completo | ✅ **81/81 ejecutados, 0 fallas funcionales** | — |
| BC-07 Contrato OpenAPI | ✅ 0 ST101, 0 ST103 y 0 ST108, en local y en QA (5 927 casos) | — |
| BC-08 SonarQube | ✅ Datos tomados; deuda llevada a 0 (PR #49) | Capturas de pantalla (Mariana) |
| BC-09 Despliegue a producción | 🟡 Herramienta lista | Respaldo, migración y PR `developer → main` (equipo); humo con `scripts/qa/humo_produccion.py` |
| BC-10 A09 y A10 | ✅ A10 cumple · A09 cumple en la app | Captura del Log stream de Azure (Mariana) |
| BC-11 Datos para los informes | ✅ | — |
| BC-12 Cierre de la campaña | 🟡 110 usuarios, 0 temporales | Correr `restaurar_qa_2026-11-13.sql` en QA (anexo A); buzón de QA (equipo) |

---

## 2. Cambios entregados

| PR | Contenido | Estado |
|---|---|---|
| [#47](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/47) | BC-02 (bcrypt), BC-06, BC-07, BC-10, BC-11 y el arreglo del CI | Fusionado (`88cdb88`) y desplegado en QA |
| [#48](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/48) | BC-04 (N-23) y BC-05 (N-31), migración `c4e1f7a9d2b8` | **Borrador:** se fusiona después de migrar `qaeyesschool` |
| [#49](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/pull/49) | Los 2 code smells de SonarQube (deuda 15 min → 0) | CI en curso |

**Hallazgo en el CI (13/11):** `pip-audit` empezó a fallar por un CVE publicado ese día contra `dnspython` 2.9.1. Al cortarse el job antes de subir `coverage.xml`, SonarQube analizó el PR solo con la cobertura de integración y marcó un 65,1 % de código nuevo cubierto; el valor real era 98,7 %. Se corrigió en el #47: `dnspython` 2.9.2, el artefacto de cobertura se sube siempre, `main.py` entra en la medición y la acción de Sonar pasa a v6.

---

## 3. Detalle por tarea

### 3.1 BC-01 · Rotación de la contraseña de la base

No depende de código. `scripts/qa/verificar_rotacion.py` deja la evidencia que pide la planeación (`evidencias/PR-03/api/BC01_rotacion.txt`). Pide la URL **vieja** sin mostrarla, comprueba que Render la rechaza y corre el preflight de producción y de QA. En el archivo solo quedan el host y el nombre de la base. El preflight ya está en verde en los dos entornos (13/11): `/docs` 200, `/cursos/` 200 y correo inexistente 401.

### 3.2 BC-02 · Rendimiento con 50 usuarios (DEF-038, #43)

**La premisa de la planeación («falta CPU») no se sostiene.** Se repitió una carga corta con el código de estado de **cada** petición (11/11, 50 usuarios, 5 min):

| Tramo | Errores |
|---|---|
| 0–180 s | **0 de 5 368** |
| 180–270 s | **~100 %** (500 y 502 mezclados) |
| Después | Se recupera solo |

No es saturación: es **una caída de ~90 s**. Los 2 104 errores de S2 equivalen a una sola caída de ~88 s. Las peticiones que fallan responden rápido (los 502 en ~160 ms), así que no se cuelgan por falta de CPU.

**Riesgo para producción:** la base de QA está **en el mismo servidor de Render que producción** (runbook, sección 3). Si la caída es del servidor (memoria o conexiones), cada corrida de carga en QA tumba también producción. Por eso **no se lanzó la S3**.

| Hecho | Resultado |
|---|---|
| bcrypt corría **dentro** del bucle de eventos | Medido: 3 logins congelaban **605 ms** toda la API. Ahora va a un hilo (21 ms) con `BCRYPT_CONCURRENCIA=2`. Desplegado en QA |
| «Quitar el commit de las lecturas» (opción B) | **No se aplicó:** cerrar la transacción con `ROLLBACK` al devolver la conexión cuesta el mismo viaje que el `COMMIT` |
| Bajar el costo de bcrypt | No se hizo (lo prohíbe la planeación) |

**Para cerrar #43:** en Render → base → *Metrics/Events*, revisar del 11/11 de 22:40 a 22:43 UTC si hubo reinicio, memoria al límite o conexiones al máximo. Si fue eso, bajar `DB_POOL_SIZE` en QA (hoy 30 + 10 por proceso; con 24 req/s basta ~10) o subir el plan de Render, y correr la S3 con el *Log stream* abierto. Hasta entonces **CP-NF-001 sigue sin aprobar**. El diagnóstico completo está en el [comentario de #43](https://github.com/AndresFelipeAceroLopez/backend-Eyes-School/issues/43#issuecomment-6868695022).

### 3.3 BC-03 · Firebase

El 13/11 se compartieron en el chat de trabajo las claves privadas de las cuentas de servicio de QA (`qa-eyes-school`, `private_key_id` `ff6a273b…`) y de producción (`eyes-school`, `87446535…`). Según el punto 3 de BC-03, **las dos deben revocarse** en Google Cloud Console → IAM → Cuentas de servicio → `firebase-adminsdk-fbsvc` → Claves. No se usaron ni se guardaron en ningún archivo ni repositorio.

Con las claves nuevas, para pegarlas en Azure sin que pasen por ningún chat (PowerShell, en el equipo donde se descargó):

```powershell
(Get-Content "$HOME\Downloads\<archivo>.json" -Raw | ConvertFrom-Json | ConvertTo-Json -Compress -Depth 5) | Set-Clipboard
Remove-Item "$HOME\Downloads\<archivo>.json"
```

Después: Azure → Web App → *Environment variables* → `FIREBASE_CREDENTIALS_JSON` → pegar → *Apply* → *Restart*. QA en `apieyeschool-q`, producción en `api-eyesschool`, con **claves distintas**.

### 3.4 BC-04 · Archivos de reportes (N-23) — opción A

- El contenido va a la tabla `reporte_archivos`, con la **misma ruta** que la API devolvía como clave. La web no cambia.
- La descarga lee de la base y, por compatibilidad, del disco.
- Los reportes del seed apuntaban a nombres que nunca existieron (`asistencia_junio_2026.pdf`). La migración les genera un PDF **rotulado como documento de ejemplo**: 8 reportes en la prueba local. Los 2 reportes en estado «Pendiente» siguen sin archivo, como corresponde.
- **Prueba de integración:** subir → borrar el disco (lo que hace un despliegue) → descargar → **200 con el mismo contenido**.
- **Verificación en QA pendiente:** después de migrar y fusionar el #48, `GET /reportes/{id}/archivo` → 200 en los 8 reportes del seed, también tras un despliegue nuevo. Luego se repiten CP-SIS-088 y CP-ACE-096.

### 3.5 BC-05 · Cuenta pendiente o desactivada (N-31)

| Caso | Antes | Ahora |
|---|---|---|
| Docente o admin autorregistrado, sin validar | 401 `Usuario inactivo` | **403** `Cuenta pendiente de validación. Un administrador debe aprobarla.` |
| Cuenta desactivada por el admin | 401 `Usuario inactivo` | **403** `Cuenta desactivada. Comunícate con el administrador del colegio.` |
| Contraseña equivocada (cualquier estado) | 401 `Credenciales inválidas` | Igual: sin la contraseña no se revela el estado |

La columna `usuario.pendienteValidacion` se marca al autorregistrarse y se quita cuando el admin activa o desactiva la cuenta. La migración marca como pendientes las cuentas de docente o admin inactivas que nunca iniciaron sesión. **La app y la web deben mostrar el `detail`.** Si alguna compara el texto `Usuario inactivo`, hay que cambiarla.

### 3.6 BC-06 · Newman (corrida I2, 13/11/2026, commit en `evidencias/PR-05/api/I2_commit.txt`)

| Indicador | Resultado |
|---|---|
| CP-INT de la API con ejecución | **81 de 81**: 75 en Newman contra QA + 6 solo en pytest |
| Fallas **funcionales** (código y cuerpo) | **0** |
| Aserciones | 183 · 3 fallan, **todas de tiempo** |
| Tiempo, umbral de QA ≤ 3 000 ms | 72 de 75 cumplen. Fuera: CP-INT-016 registro (3 485 ms), 025 eliminar usuario (7 081 ms), 051 boletín PDF (7 954 ms) |

- **CP-INT-052** corrió por primera vez: busca solo un estudiante sin notas → 404 con el mensaje de BE-19.
- **CP-INT-006, 009, 010, 029, 058 y 072** pasaron de pytest a Newman sobre una **cuenta temporal** que la colección crea y borra. Ninguna cuenta del seed se bloquea ni se desactiva.
- **Solo en pytest**, con su prueba anotada en la planeación de integración: 012 a 015 (el token llega por correo), 049 (repositorio) y 057 (envío push). Los seis pasan en la integración (61/61).
- CP-INT-014: se usó la opción de pytest, que genera el token (`test_el_enlace_de_recuperacion_no_se_puede_reutilizar`).
- Resultado por caso: `evidencias/PR-05/api/I2_newman.xml` (JUnit, una suite por CP-INT) e `I2_newman.html`.

### 3.7 BC-07 · Contrato OpenAPI

| Hallazgo (I1, QA, 10/11) | Corrección |
|---|---|
| ST103 × 50: 401/403/404 no declarados | Errores reales declarados con `ErrorOut {"detail": str}` sobre el esquema generado: una ruta nueva queda documentada sola |
| ST108 × 25: fechas sin zona | Fechas de los `Out` con zona UTC (`…Z`). Las horas de `Horario` son hora local: se documentan con su patrón, sin inventarles zona |
| ST205 × 3: `Allow` incompleto en los 405 | `Allow` con todos los métodos de la URL |
| ST105 × 1: el boletín no declaraba PDF | `application/pdf` declarado (y los tipos del archivo de reporte) |
| Aparecieron al corregir: ST202, ST201, ST204 | Ids `Entero32` (rango de `integer`, validado antes de la base); `?fecha=` solo `AAAA-MM-DD`; `PUT /estudiantes/me` ya no cae en `/{id}` |

- **Local, misma configuración (GET, `--checks all`):** **2 933 casos generados, 2 933 pasan**; 0 en todos los checks. Evidencia: `I2_schemathesis_local.txt`.
- **QA:** 5 927 casos, **0 ST101, 0 ST103, 0 ST108** y 0 en los demás checks de contrato. Los únicos 4 fallos (ST112, tiempo) son del cliente; ver el anexo A.

**Efecto en los clientes:** las fechas llegan como `2026-11-03T03:03:37Z`. Si la web o la app hacen `new Date(fecha)`, antes la tomaban como hora local (5 h corridas) y ahora sale bien.

### 3.8 BC-08 · SonarQube Cloud (rama `developer`, análisis del 14/11/2026 00:04 UTC, después del #47)

| Métrica | Valor |
|---|---|
| Quality Gate | **OK** |
| Bugs · Vulnerabilidades | 0 · 0 |
| Security hotspots · revisados | 0 · 100 % |
| Code smells | 2 → **0 con el PR #49** |
| Deuda técnica | 15 min → **0 con el PR #49** |
| Ratio de deuda | 0,0 % (15 ÷ (4 037 LOC × 30 min) = 0,012 %) |
| Complejidad cognitiva · ciclomática | 341 · 642 |
| Duplicación | 0,0 % |
| Cobertura (Sonar) | 76,6 % global · 80,1 % líneas · 51,4 % ramas |
| Líneas de código | 4 037 (la planeación usaba 3 646, de antes del cierre) |

Los dos code smells eran `python:S1845` (BLOCKER, `config.py:63`, la propiedad `cors_origins` se confundía con `CORS_ORIGINS`) y `python:S8519` (`base_repository.py:17`). Faltan las capturas de *Overview*, *Issues* y *Measures*.

### 3.9 BC-09 · Despliegue a producción

Orden seguro, porque la migración es aditiva y el código viejo funciona con la base ya migrada:

1. Respaldo de la base de producción en Render.
2. `alembic current` en producción → debe estar en `b7d2e9a41c03`.
3. `alembic upgrade head` → `c4e1f7a9d2b8`, **antes** de desplegar.
4. PR `developer → main` con el CI en verde y despliegue.
5. Variables: `DATABASE_URL` nueva (BC-01), `SECRET_KEY` propia, `ENVIRONMENT=production`, `FRONTEND_URL`, `FIREBASE_CREDENTIALS_JSON` de producción (BC-03).
6. `python -m scripts.qa.humo_produccion` → `evidencias/PR-06/api/BC09_humo_produccion.txt`. Comprueba `/docs`, `/padres/me/hijos` en el contrato, `/cursos/`, el 401, `nosniff` y el bloqueo 429, este con una cuenta temporal de padre sin vínculo que se borra al final.

Si el equipo decide no desplegar todavía, el PR-08 lo dice: la versión aceptada es la de QA.

### 3.10 BC-10 · A09 y A10

**A10 (SSRF): cumple.** La API solo hace llamadas salientes a Resend (URL fija) y a Firebase (SDK), las dos sin datos del usuario en la URL. fpdf no carga imágenes y el avatar se abre desde bytes. **0 rutas descargan URLs del usuario.** Hallazgo lateral, corregido: el nombre del usuario se insertaba sin escapar en el HTML del correo de recuperación.

**A09 (registro): cumple en la app.** Antes los `logger.info` no salían en Azure (la raíz del logging no tenía handler) y ni un 403 ni un 404 dejaban rastro. Ahora:
- Todos los logs llevan fecha y hora.
- 401, 403, 404 y 429 se registran con método, ruta, estado y origen, **sin** query string, cabeceras ni cuerpo.
- El login fallido registra el id del usuario y el número de intento, sin el correo escrito ni la contraseña.

Las pruebas lo verifican con un token en la query y en la cabecera (`test_cierre_seguridad_rendimiento.py`). Falta la captura del *Log stream* de `apieyeschool-q` con 6 logins fallidos, un 403 y un 404.

### 3.11 BC-11 · Datos para los informes

**Defectos (GitHub Issues #22 a #44):**

| Dato | Valor |
|---|---|
| Total · cerrados · abiertos | 23 · 21 · 2 (#22 crítico, #43 alto) |
| Reabiertos | **0** (eventos `reopened` de los 23 issues) |
| Renumeración | DEF-020…023 → **DEF-036…039** (#41 a #44): títulos, planeaciones, informes y código |
| Causa raíz | Comentada en los 21 issues cerrados: **Diseño 11 · Codificación 4 · Requisitos 4 · Datos 1 · Entorno 1** |
| Tiempo de corrección | Desde la fecha de identificación hasta el commit: BE-03 a BE-19 identificados el 28 y el 30/10, corregidos el 09/11 (`88cd544`): **10 a 12 días**; DEF-036 y DEF-037 el mismo día; DEF-039, el mismo día (`4d486a9`) |

> `closedAt` no sirve para medir el tiempo de corrección: los 23 issues se crearon el 10/11 después de corregir y se cerraron 7 minutos después.

| Issue | DEF | Causa | Commit |
|---|---|---|---|
| #23 | DEF-002 | Codificación | `fca0e93` |
| #24, #25, #28, #30–#37 | DEF-003, 004, 007, 009–016 | Diseño | `88cd544` |
| #26, #29, #38, #39 | DEF-005, 008, 017, 018 | Requisitos | `88cd544` |
| #27 | DEF-006 | Codificación | `88cd544` |
| #40 | DEF-019 | Datos | `abd7691` |
| #41 | DEF-036 | Entorno | `b7d1ceb` (migración) |
| #42 | DEF-037 | Codificación | `06bf07f` / `83d9e22` |
| #44 | DEF-039 | Codificación | `4d486a9` |

**Pruebas (con el PR #48 incluido):**

| Dato | Valor |
|---|---|
| Unitarias | **238 en 20,7 s** |
| Integración (PostgreSQL 18) | **61 en 30,4 s** |
| Total | 299 en 31 archivos |

| Capa | Líneas | Ramas | Funciones |
|---|---|---|---|
| `api` | 74,6 % | 50,0 % | 36,0 % |
| `application` | 83,2 % | 55,3 % | 61,8 % |
| `core` | 93,6 % | 90,9 % | 96,4 % |
| `domain` (interfaz abstracta) | 0,0 % | — | 0,0 % |
| `infrastructure` | 78,0 % | 28,1 % | 58,1 % |
| `main.py` | 94,9 % | 71,4 % | 83,3 % |
| **Total** | **80,8 %** (2 568/3 178) | **52,7 %** (231/438) | **55,0 %** (203/369) |

La cobertura de funciones de `api` es baja porque cuenta cada endpoint como función, y muchos solo se ejecutan en Newman, que no mide cobertura.

**Pruebas por archivo:** `test_servicios_crud.py` 30 · `test_authorization.py` 19 · `test_cierre_seguridad_rendimiento.py` 19 · `integration/test_acceso_a_datos.py` 19 · `integration/test_notas_novedades.py` 18 · `integration/test_auth_sesiones.py` 17 · `test_id_fuera_de_rango.py` 14 · `test_password_policy.py` 14 · `test_qa_app_movil.py` 14 · `test_qa_reset_passwords.py` 13 · `test_sesion.py` 13 · `test_correo.py` 10 · `test_notas_validacion.py` 9 · `test_notificaciones.py` 9 · `test_padre_varios_hijos.py` 9 · `test_permisos_docente.py` 8 · `test_avatar.py` 7 · `test_bloqueo_login.py` 7 · `test_asistencia_duplicados.py` 6 · `test_config.py` 6 · `test_dashboard.py` 6 · `integration/test_estado_cuenta_y_reportes.py` 5 · `test_security.py` 5 · `test_archivos.py` 4 · `test_boletin.py` 4 · `test_register.py` 4 · `test_actor_token.py` 3 · `test_normalizar_correos.py` 3 · `test_app.py` 2 · `integration/test_dashboard_asistencia.py` 1 · `integration/test_humo.py` 1.

### 3.12 BC-12 · Cierre de la campaña

- **QA tiene 110 usuarios y 0 temporales** (13/11, después de la corrida I2 de Newman y su limpieza).
- Se anularon **403 registros de asistencia «clase»** del estudiante 1 del 11/11, creados por la corrida de diagnóstico de carga. Quedan 0 activos.
- **Pendiente:** correr `scripts/qa/restaurar_qa_2026-11-13.sql` en `qaeyesschool` para reactivar 4 especializaciones y reponer 4 novedades que borró la repetición de schemathesis (anexo A).
- Falta el buzón de QA del equipo (CP-INT-012, 014 y CP-ACE-016). Mientras tanto, los cuatro casos de recuperación de contraseña se cubren en pytest.

---

## 4. Definición de terminado

- [ ] #22, #43, N-23 y N-31 cerrados. **N-23 y N-31:** código listo en el #48, falta migrar y fusionar. **#22 y #43:** ver 3.1 y 3.2.
- [x] 81/81 CP-INT de la API ejecutados con resultado por caso; 0 fallas funcionales.
- [x] Schemathesis con 0 ST101, ST103 y ST108 (local y QA; anexo A).
- [ ] Capturas y deuda de SonarQube en el PR-03. **Deuda: sí.** Faltan las capturas.
- [ ] Producción desplegada con el humo en verde, o la decisión de no desplegar escrita en el PR-08.

---

## Anexo A · schemathesis contra QA (I2)

**Corrida principal** (13/11, GET, `--checks all`, token de admin, `evidencias/PR-05/api/I2_schemathesis.txt`):

| Fase | Resultado |
|---|---|
| Coverage | 45 ✔ · 1 ✖ |
| Fuzzing | 43 ✔ · 3 ✖ |
| Stateful | 162 ✔ |
| **Casos generados** | **5 927** |
| ST101, ST103, ST105, ST108, ST201–ST205 | **0** |
| ST112 (tiempo de respuesta) | 4: `/asignaciones`, `/cursos/{id}/estudiantes`, `/novedades` y `/reportes` |

- **Los 4 ST112 no son del servidor:** marcan entre 147 s y 921 s, imposibles con un límite de 60 s por petición. Coinciden con un corte de red del equipo que ejecutaba la prueba (se perdió la resolución DNS en esa misma ventana).
- **12 operaciones solo recibieron 401:** la corrida duró 68 min y el token de admin vence a los 30. Esas 12, más las 4 de los ST112, se repitieron aparte con token nuevo (abajo).
- Las 3 que responden 403 (`/dashboard/estudiante`, `/dashboard/padre`, `/padres/me`) son de otro rol: con token de admin el 403 es lo correcto.

**Repetición de las 16 operaciones** (`I2_schemathesis_repeticion.txt`): _ver la sección siguiente._

### Incidente durante la repetición (13/11/2026, ~20:17–20:31)

El primer intento de repetición se lanzó con `--include-method GET` y `--include-path-regex`. **schemathesis combina esos dos filtros con OR, no con AND**, así que seleccionó 57 operaciones en vez de 16, entre ellas **11 de escritura**, y las probó con el token de administrador durante ~12 minutos. Se detuvo al ver «57 selected» y se revisaron las tablas afectadas comparándolas con el seed:

| Tabla | Daño | Restauración |
|---|---|---|
| `profesores` 1, 2, 3 | `estado` → «Inactivo» | ✅ Por API (`PUT estado: Activo`) |
| `asignaciones` 1, 3, 6, 10 | desactivadas (la 1 rompía los permisos del docente de prueba) | ✅ Por API (`PUT activo: true`) |
| `especializaciones` 1 | descripción borrada | ✅ Por API |
| `especializaciones` 1, 3, 6, 10 | desactivadas | ⏳ `scripts/qa/restaurar_qa_2026-11-13.sql` (el API no permite reactivarlas) |
| `novedades` 1, 2, 5, 9 | **borradas** (el DELETE es físico) | ⏳ El mismo SQL, con los ids y valores exactos del seed |

No se crearon registros nuevos y las demás novedades, títulos de profesores y fechas de asignación coinciden con el seed. El SQL se probó en local sobre una base con el mismo nombre: restaura, es idempotente y se niega a correr si la base no es `qaeyesschool`.

**Lección para la planeación de integración:** para acotar schemathesis a solo lectura no basta con los filtros de la CLI. La repetición correcta usa un `openapi.json` recortado en local con únicamente las operaciones GET, así es imposible que mande una escritura.
