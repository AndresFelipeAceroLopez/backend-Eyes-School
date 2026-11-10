# Planeación del registro y gestión de defectos — Backend (API FastAPI) · Eyes School

> **Tipo de documento:** planeación de QA para el PR-07 (Registro y gestión de defectos). Describe cómo se registran, clasifican, corrigen, verifican y cierran los defectos de este componente en Azure Boards, y lista los defectos que ya se conocen. No contiene resultados de ejecución.
> **Pensado para:** cualquier integrante del equipo o una IA que no conoce el proyecto. Los defectos conocidos salen de la revisión de código (prueba estática) del 28 al 30/10/2026 y del 02/11/2026, documentada en las planeaciones de correcciones, el PR-02 y el PR-03.
> **Elaboró:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> **Plazo:** registro de los defectos conocidos en S7 (hasta el 6 nov 2026); gestión continua en S8 a S10; corte del PR-07 el 21 nov (S9) y cierre el 28 nov (S10), según el PR-01.

---

## 1. Dónde viven los defectos

| Elemento | Valor |
|---|---|
| Herramienta | Azure Boards del proyecto (proceso Scrum), tipo de elemento **Bug** |
| Etiquetas | `api` (componente) y el origen: `revision-codigo`, `analisis-estatico`, `pruebas-unitarias`, `pruebas-integracion`, `pruebas-sistema` o `uat` |
| Enlace con el código | Cada PR de corrección en `backend-Eyes-School` lleva `AB#<id>` en el título o la descripción. Requiere la app Azure Boards instalada en la organización de GitHub (una sola vez) |
| Relación con el caso | Campo «Repro Steps» con el ID del caso (CP-INT, CP-SIS, CP-NF o CP-ACE) y la corrección planeada (BE, WEB o APP) |

## 2. Ciclo de vida (proceso Scrum de Azure Boards)

| Estado | Quién lo mueve | Cuándo |
|---|---|---|
| New | QA | Al registrar el bug con la ficha de la sección 4 del PR-07 |
| Approved | PO (Sergio Gómez) | Al confirmar la prioridad en el refinamiento |
| Committed | Desarrollador asignado | Al tomarlo en el sprint |
| Done | QA (Mariana Cortés o Samuel Sierra) | Solo después de verificar la corrección en QA: el caso que lo detectó pasa y la regresión del módulo no rompe nada |
| Removed | PO | Si es un falso positivo o una decisión de diseño (con la justificación escrita) |

Un bug que falla la verificación vuelve a **Committed** y se cuenta como reabierto (métrica del PR-07).

## 3. Clasificación

- **Severidad (la define QA)** con los cuatro niveles del PR-07: Crítica, Alta, Media y Baja. En Azure Boards: 1 - Critical, 2 - High, 3 - Medium, 4 - Low.
- **Prioridad (la define el PO)** de P1 a P4. QA propone: Crítica → P1, Alta → P2, Media → P3, Baja → P4, y el PO la confirma o la cambia.
- **Tiempo objetivo de corrección:** Crítica ≤ 24 h; Alta ≤ 3 días; Media dentro del mismo sprint; Baja al backlog. Las críticas conocidas tienen acción el primer día de S7.

## 4. Defectos ya conocidos de este componente

Se registran en Azure Boards antes del 6 nov con estado New, etiqueta `revision-codigo` y la fecha en que se identificaron como fecha de apertura. El número `AB#` que asigne Azure Boards se anota en el PR-07.

| ID PR-07 | Corrección | Título | Severidad | Prioridad propuesta | Caso que lo verifica | Asignado | Identificado | Sprint |
|---|---|---|---|---|---|---|---|---|
| DEF-001 | BE-01 | El historial de git conserva un .env con la URL de la base de Render (usuario y contraseña) y la SECRET_KEY | Crítica | P1 | CP-NF-012 | Andrés Acero | 28/10/2026 | S7 (día 1) |
| DEF-002 | BE-03 | GET /dashboard/estudiante responde 500 (AttributeError) y rompe el inicio del estudiante, también en producción | Crítica | P1 | CP-INT-060 | Andrés Acero | 28/10/2026 | S7 (día 1, hotfix) |
| DEF-003 | BE-04 | Un padre o un estudiante lee la asistencia de cualquier estudiante por GET /asistencia | Crítica | P1 | CP-INT-036 a 038 | Andrés Acero | 28/10/2026 | S7 |
| DEF-004 | BE-05 | Un padre lee el vínculo de otro padre en GET /padres/{id} | Media | P3 | CP-INT-065 | Andrés Acero | 28/10/2026 | S7 |
| DEF-005 | BE-06 | La API acepta notas de 0 a 10 en vez de 0.0 a 5.0 | Alta | P2 | CP-INT-043, 046 | Andrés Acero | 28/10/2026 | S7 |
| DEF-006 | BE-07 | Un padre con dos hijos provoca error 500 en /padres/me, el dashboard y la autorización | Alta | P2 | CP-INT-062 a 064 | Andrés Acero | 28/10/2026 | S8 |
| DEF-007 | BE-08 | Se guardan dos entradas o dos salidas del mismo estudiante el mismo día | Alta | P2 | CP-INT-031, 033, 034 | Andrés Acero | 28/10/2026 | S7 |
| DEF-008 | BE-09 | La API no aplica la política de contraseña (5 reglas) ni pide la contraseña actual al cambiarla | Alta | P2 | CP-INT-013, 020, 028 | Andrés Acero | 28/10/2026 | S7 |
| DEF-009 | BE-10 | registrado_por lo envía el cliente: se puede registrar a nombre de otro docente | Media | P3 | CP-INT-035 | Andrés Acero | 28/10/2026 | S7 |
| DEF-010 | BE-11 | El docente califica cualquier materia, lee todas las notas y edita novedades de otros | Media | P3 | CP-INT-047, 048, 056 | Andrés Acero | 28/10/2026 | S8 |
| DEF-011 | BE-12 | El correo distingue mayúsculas y no se valida su formato | Media | P3 | CP-INT-007, 018, 077 | Andrés Acero | 28/10/2026 | S7 |
| DEF-012 | BE-13 | Un usuario desactivado sigue renovando su sesión y el enlace de recuperación se puede reutilizar | Media | P3 | CP-INT-009, 010, 014, 029 | Andrés Acero | 28/10/2026 | S8 |
| DEF-013 | BE-14 | Los avatares no validan tipo ni tamaño y se sirven como públicos (permite XSS almacenado) | Media | P3 | CP-INT-072 | Andrés Acero | 28/10/2026 | S7 |
| DEF-014 | BE-15 | Los reportes se descargan sin token por /static y los boletines PDF nunca se borran | Media | P3 | CP-INT-051, 071 | Andrés Acero | 28/10/2026 | S8 |
| DEF-015 | BE-16 | No hay límite de intentos de inicio de sesión | Media | P3 | CP-INT-006 | Andrés Acero | 28/10/2026 | S8 |
| DEF-016 | BE-17 | Si Redis falla, la revocación de sesiones se desactiva sin aviso (try/except pass) | Alta | P2 | CP-INT-009 | Andrés Acero | 30/10/2026 | S7 |
| DEF-017 | BE-18 | Las notificaciones push al acudiente no se envían: no existe el emisor | Alta | P2 | CP-INT-057, 058 | Andrés Acero | 30/10/2026 | S8 |
| DEF-018 | BE-19 | El boletín de un estudiante sin notas sale como PDF vacío en vez del mensaje del CA | Media | P3 | CP-INT-052 | Andrés Acero | 30/10/2026 | S8 |
| DEF-019 | H-08 | seed_data.sql trae en un comentario las contraseñas de 4 usuarios de prueba, incluido el admin | Crítica | P1 | CP-NF-012 | Andrés Acero | 30/10/2026 | S7 (día 1) |
| DEF-020 | BE-INF-4 | La API de QA (apieyeschool-q) responde 500 en todo lo que consulta la base: bloquea la integración y los E2E | Alta | P1 | Preflight de BE-INF-4 | Mariana Cortés · Andrés Acero | 05/11/2026 | S8 (primero) |
| DEF-021 | BE-01 | create_admin.py trae la DATABASE_URL con usuario y contraseña embebida, y el commit que está en main (producción) todavía la tiene | Crítica | P1 | CP-NF-012 (B8 de E1) | Andrés Acero | 09/11/2026 | S8 |
| DEF-022 | — | Con 50 usuarios concurrentes la API falla: 8,05 % de peticiones sin respuesta y p95 de 3,06 s contra la meta de 800 ms | Alta | P2 | CP-NF-001 | Andrés Acero | 09/11/2026 | S9 |
| DEF-023 | — | Cualquier endpoint con un id fuera del rango de PostgreSQL responde 500 en vez de 404 o 422 | Media | P3 | CP-INT (contrato OpenAPI) | Andrés Acero | 10/11/2026 | S9 |

**DEF-022 · Rendimiento bajo carga (un solo bug, no uno por umbral).** La corrida S1 del
09/11/2026 incumplió cuatro umbrales a la vez —errores, p95 global, p95 de navegación y p95 de
login—, pero son síntomas de una misma saturación, así que se registra **un** defecto y no cuatro.
Esto sigue la regla de la sección 8 de la planeación de análisis estático: un hallazgo con una
causa común no se duplica.

| Dato | Valor |
|---|---|
| Medición | 50 VUs + 5 docentes + 6 logins/min, 13 min, QA · 12 578 peticiones a 16,1/s |
| Errores | 8,05 % (1 013). Máximo de 60,0 s = tiempo de espera agotado |
| p95 | 3,06 s global · 2,72 s navegación · 11,31 s login |
| Recuperación | La API volvió sola a su línea base sin reiniciar (criterio de CP-NF-002) |
| Evidencia | `evidencias/PR-06/api/S1_k6_carga.{txt,json}` |

**Lo que hay que decidir antes de corregir, y no es de QA:**

1. **El entorno de medición.** QA está en `chilecentral` y su base en Render (Oregón): la misma
   consulta tarda 1 526 ms allí y 411 ms en producción. El equipo decidió el 09/11/2026 **no mover
   la Web App ni la base**, así que esta diferencia es permanente. El PO decide si CP-NF-001 se
   evalúa en QA con un umbral ajustado, o si se acepta el incumplimiento como riesgo documentado.
2. **No tocar el pool a ciegas.** `pool_size=10` + `max_overflow=20` son 30 conexiones; subirlas
   solo ayuda si el plan de Render admite más, y si no, empeora. Hay que confirmar el límite antes.
3. **La única palanca que no depende de la infraestructura** es reducir el número de consultas por
   petición. Entra al plan de remediación del PR-03, no a este bug.

**No se registran** como defectos aparte las 55 aserciones de tiempo que falló Newman (I1): son el
mismo fenómeno medido sin carga y quedan enlazadas a DEF-022.

**DEF-023 · Un id fuera de rango produce 500.** Lo encontró `schemathesis` contra el contrato
publicado en `/openapi.json` y se verificó a mano con el entorno en reposo, para descartar que
fuera una secuela de la prueba de carga:

| Petición | Respuesta | Esperado |
|---|---|---|
| `GET /api/v1/estudiantes/9223372036854775808` | **500** | 404 o 422 |
| `GET /api/v1/cursos/{id}/horarios` con ese id | **500** | 404 o 422 |
| `GET /api/v1/especializaciones/87178291200` | **500** | 404 o 422 |
| `GET /api/v1/cursos/2/horarios` (id válido) | 200 | ✔ |
| `GET /api/v1/especializaciones/0` | 404 | ✔ |

**Afecta a 9 de 9 endpoints probados** con parámetro de id (`estudiantes`, `cursos`, `usuarios`,
`notas`, `asistencia`, `materias`, `profesores`, `novedades`, `reportes`), así que no es un
endpoint defectuoso sino un patrón.

**Causa.** FastAPI valida que el parámetro sea un entero, pero no su magnitud: el valor llega a la
consulta y PostgreSQL rechaza lo que no cabe en `integer`/`bigint`. El error de la base sube sin
capturar y se convierte en 500. Incumple dos reglas del propio proyecto: «validar todos los
inputs» y «nunca exponer stack traces en producción».

**Corrección propuesta** (dos opciones, la primera es la mínima):

1. Acotar los parámetros de ruta: `id: int = Path(..., ge=1, le=2147483647)`. Devuelve 422 y no
   llega a la base. Hay que tocar cada endpoint.
2. Un manejador global de `sqlalchemy.exc.DBAPIError` en `main.py` que responda 422. Es un solo
   cambio y cubre también los casos que aún no se conocen, pero atrapa más de lo que se busca.

**Severidad Media:** no expone datos ni permite acceso indebido, y hace falta un id absurdo para
provocarlo. Se registra porque es un 500 no controlado y porque el contrato de OpenAPI declara
solo 200 y 422 para esas operaciones.

**DEF-020 quedó resuelto el 09/11/2026.** Causa raíz: **Entorno** — la base de QA estaba en la revisión `a1b2c3d4e5f6` mientras el código desplegado desde `developer` ya necesitaba `b7d2e9a41c03` (tablas `sesiones_refresco` y `dispositivos`). Se aplicó la migración desde la consola SSH de `apieyeschool-q`. Verificación: login del admin con `QA_PASSWORD` → 200. La misma falta se encontró en producción y se corrigió igual, antes de desplegar `v1.1.0`.

**DEF-020** es el mismo DEF-WEB-01 del repositorio de la web; se registra también aquí porque la causa y la corrección son del backend. No se duplica: se enlaza al bug de la web.

**DEF-021 sale de la corrida E1 del 09/11/2026** (ver [`../Resultados/corrida-2026-11-09.md`](../Resultados/corrida-2026-11-09.md), sección 3.3). Según la regla de la sección 8 de la planeación de análisis estático, un hallazgo que ya tiene corrección planeada se enlaza a esa corrección en vez de abrir otro bug; se registra aparte de DEF-001 porque **amplía el alcance de BE-01 a un archivo y a una rama que ese defecto no cubría** (`create_admin.py` en `main`), y porque su corrección es un cambio de código, no solo la rotación de secretos. Al cerrar DEF-001 **no** queda cerrado DEF-021.

## 5. Ficha del bug en Azure Boards

| Campo de Azure Boards | Contenido |
|---|---|
| Title | Verbo + qué falla + dónde (como los títulos de la sección 4) |
| Repro Steps | Pasos numerados, resultado esperado, resultado obtenido, ID del caso y corrección planeada |
| System Info | URL de QA, commit de la API y la petición/respuesta (sin token) |
| Severity / Priority | Sección 3 |
| Assigned To | Responsable de la corrección en la planeación |
| Tags | `api` + origen |
| Adjuntos | Captura, video o log **sin tokens ni contraseñas** |
| Al cerrar | Causa raíz (Requisitos, Diseño, Codificación, Datos o Entorno) y commit de la corrección |

## 6. Verificación y regresión

1. El desarrollador fusiona la corrección en `develop` con la prueba que demuestra el defecto (fallaba antes y pasa después).
2. Se despliega en QA y QA repite el caso que lo detectó.
3. Se corre la regresión del módulo: las pruebas automatizadas del componente y los casos de sistema del mismo módulo.
4. Si todo pasa, QA mueve el bug a **Done** y anota la fecha de cierre; si no, vuelve a **Committed** y se cuenta como reabierto.

## 7. Registro en el PR-07

| Dato | Dónde va |
|---|---|
| Cada defecto con su `AB#`, estado y fechas | Tabla 2 (registro consolidado) |
| Conteos por severidad, reabiertos y tiempos | Tabla 3 (métricas) y Figura 2 |
| Causa raíz al cerrar | Sección 7 (análisis de causa raíz) |

Corte del registro: 21 nov 2026 (fin de S9) y 28 nov 2026 (fin de S10). En cada corte se exporta la consulta de Azure Boards («Bugs del proyecto Eyes School») a CSV y se anexa al PR-07.

## 8. Responsables y calendario

| Actividad | Fecha | Responsable |
|---|---|---|
| Registrar los 23 defectos conocidos en Azure Boards | 3 – 6 nov | Mariana Cortés |
| Confirmar prioridades | Refinamiento de S7 | Sergio Gómez (PO) |
| Registrar los defectos nuevos de PR-03 a PR-06 | Durante cada corrida | Quien ejecuta la corrida |
| Verificar correcciones y cerrar | S8 a S10 | Mariana Cortés · Samuel Sierra |
| Cortes del PR-07 | 21 y 28 nov | Samuel Sierra (líder de pruebas) |

## 9. Definición de terminado

- [ ] Los 23 defectos conocidos de este componente están en Azure Boards con su `AB#` anotado en el PR-07.
- [ ] Cada bug cerrado tiene la verificación en QA, la causa raíz y el commit.
- [ ] 0 defectos críticos o altos abiertos al cierre de S10 (criterio de salida del PR-01).
