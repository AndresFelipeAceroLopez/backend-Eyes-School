# Planeación de pruebas de sistema — Backend (API FastAPI) · Eyes School

> **Tipo de documento:** planeación de QA para el PR-06 (Informe de pruebas de sistema). Describe las pruebas no funcionales de la API (rendimiento, seguridad con OWASP Top 10, archivos, sesiones) y lo que el backend debe preparar para que la web y la app ejecuten sus pruebas de sistema. No contiene resultados: se llenan al ejecutar.
> **Pensado para:** cualquier integrante del equipo o una IA que no conoce el proyecto. Los casos y sus ID son los del PR-02 v0.2.
> **Elaboró:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> **Plazo:** preparación en S8 (hasta el 14 nov 2026) y ejecución en S9 (15 – 21 nov 2026), según el PR-01. Regresión en S10.
> **Actualizado el 09/11/2026 (montaje terminado y corrida de humo hecha):** `usuarios_ds02.json`
> generado con 50 cuentas y escenarios verificados contra QA. **Una corrida de humo con 10 VUs ya
> da p95 = 4,32 s contra la meta de 800 ms, con 0 % de errores.** La meta de CP-NF-001 no se va a
> cumplir, y la causa principal **no es el código**: QA está en `chilecentral` y su base en Render
> (Oregón), y la misma consulta tarda 1526 ms en QA frente a 411 ms en producción (westus3). El
> equipo decidió el 09/11/2026 **no mover la Web App ni la base**, así que esa diferencia se queda.
>
> **DECISIÓN DEL PO (Sergio Gómez, 10/11/2026): opción A, umbral ajustado para QA.**
>
> CP-NF-001 se evalúa en QA con el umbral del MC-01 escalado por la diferencia de entorno medida:
> 1 526 ms en QA contra 411 ms en producción para la misma consulta, un factor de 3,7.
>
> | Criterio | MC-01 (producción) | **Aprobado para QA** |
> |---|---|---|
> | p95 de navegación | ≤ 800 ms | **≤ 3 000 ms** |
> | p95 de `POST /auth/login` | — | ≤ 11 000 ms |
> | Errores | < 1 % | **< 1 % (sin cambio)** |
>
> Los umbrales están aplicados en `tests/carga/carga_50.js`, con la justificación escrita en el
> propio archivo. Si algún día QA y su base quedan en la misma región, se vuelve a 800 ms.
>
> **Ojo con lo que esta decisión NO resuelve:** el umbral ajustado solo cubre el tiempo de
> respuesta. La corrida S1 también incumplió el criterio de **errores** (8,05 % frente a < 1 %), y
> ese no se escala: «8 % de peticiones sin respuesta» no se vuelve aceptable por estar lejos de la
> base. Lo que ocurre es que QA alcanza su techo de throughput (~20 req/s) con 50 usuarios, y a
> partir de ahí encola hasta agotar el tiempo de espera. **CP-NF-001 sigue sin cumplirse por el
> criterio de errores**, y eso es lo que queda abierto en DEF-038.
>
> El escenario de carga se corrigió el 09/11/2026: antes iniciaba sesión en **cada** iteración, y
> como el login tarda ~3 s por bcrypt (frente a ~1 s de una consulta normal), la prueba medía sobre
> todo el costo de hashear. Ahora cada usuario virtual inicia sesión una vez y reutiliza el token,
> como hacen la web y la app, y el login se mide en su propio escenario a 6 por minuto.
>
> **Anterior:** `k6 v2.3.0` ya está instalado (`winget install k6`) y los scripts `tests/carga/carga_50.js` y `tests/carga/estres.js` existen. La ejecución sigue **bloqueada por BE-INF-4 (DEF-036/DEF-WEB-01)**: la API de QA responde 500 en todo lo que consulta la base, y las pruebas de carga **no se corren contra producción** (regla 1.4 de la planeación de correcciones). Si BE-INF-4 no se cierra antes del 15 nov, la carga y el estrés se corren contra la API local sobre la base de PostgreSQL de pruebas y se anota en el PR-06 que los números no representan al servidor de Azure.

---

## 1. Objetivo y alcance

| Entra | No entra |
|---|---|
| Carga y estrés de la API (CP-NF-001 y 002) | Flujos de pantalla: planeaciones de la web y de la app |
| Escaneo DAST de la API con OWASP ZAP (parte API de CP-NF-003) | Análisis estático: PR-03 |
| Verificación OWASP Top 10 (Tabla 4 del PR-06) | |
| Secretos, archivos públicos, dependencias y usuario desactivado (CP-NF-012, 014, 015 y 019) | |
| Preparación del entorno de QA para todo el PR-06 | |

## 2. Entorno

| Elemento | Valor |
|---|---|
| API | QA en Azure App Service (URL pendiente de definir en el PR-01). **Nunca se hace carga ni DAST contra producción** |
| Base | PostgreSQL 18 de QA con `schema.sql` → `seed_data.sql` → `seed_estudiantes_sinteticos.sql` → `scripts/qa_reset_passwords.py` (BE-INF-2) |
| Monitoreo | Métricas de Azure App Service (CPU, memoria, tiempo de respuesta) durante la carga |
| Versión | `release/1.1.0` desplegada en QA (liberación del 14/11/2026); se anota el commit |

## 3. Preparación para todo el PR-06 (S8)

1. Desplegar en QA la versión con las correcciones de S7 y S8.
2. Cargar los datos de QA y confirmar DS-01 y DS-03 (`roberto.diaz@gmail.com` con un hijo y `rosa.perez@gmail.com` con dos).
3. Configurar `FIREBASE_CREDENTIALS_JSON` en la API de QA para que lleguen las notificaciones (BE-18) en los casos de la app.
4. Publicar a las tres partes la URL de QA y la hora de cada recarga de datos.
5. Prueba de humo antes de cada día de pruebas: `GET /api/v1/cursos` (endpoint público, responde 200 sin token) y un login por rol. La API no tiene hoy un endpoint `/health`.

## 4. Rendimiento (CP-NF-001 y 002)

| Elemento | Valor |
|---|---|
| Herramienta | k6 |
| Carga (CP-NF-001) | Rampa de 0 a 50 usuarios virtuales en 2 min, 10 min sostenidos y bajada de 1 min |
| Estrés (CP-NF-002) | De 50 a 200 usuarios en escalones de 25 cada 2 min, hasta que se degrade; luego bajar a 0 y comprobar que la API se recupera sin reiniciar |
| Endpoints | `POST /auth/login`, `GET /estudiantes/{id}/notas`, `GET /asistencia?fecha=<hoy>`, `POST /asistencia` (tipo «clase», que no tiene restricción de duplicado) |
| Usuarios | 50 cuentas de DS-02 (DS-08) para los GET; un docente para los POST |
| Metas (MC-01) | p95 ≤ 800 ms · errores < 1 % · ≥ 50 usuarios concurrentes. El tiempo promedio (≤ 400 ms) y la CPU (≤ 70 %) son metas de la plantilla, sin umbral en el MC-01: se registran |

Script propuesto (`tests/carga/carga_50.js` en el repositorio del backend):

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.QA_API;              // URL de QA con /api/v1
const PASSWORD = __ENV.QA_PASSWORD;     // secreto, nunca en el código
const USUARIOS = JSON.parse(open('./usuarios_ds02.json')); // [{correo, id_estudiante}]

export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '10m', target: 50 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const u = USUARIOS[(__VU - 1) % USUARIOS.length];
  const login = http.post(`${BASE}/auth/login`, JSON.stringify({ correo: u.correo, password: PASSWORD }),
                          { headers: { 'Content-Type': 'application/json' } });
  check(login, { 'login 200': (r) => r.status === 200 });
  const auth = { headers: { Authorization: `Bearer ${login.json('access_token')}` } };
  check(http.get(`${BASE}/estudiantes/${u.id_estudiante}/notas`, auth), { 'notas 200': (r) => r.status === 200 });
  sleep(1);
}
```

El docente que hace los `POST /asistencia` y `GET /asistencia?fecha=` va en un segundo escenario del mismo archivo (`scenarios`), con 5 usuarios virtuales.

## 5. Seguridad

### 5.1 Verificación OWASP Top 10 (Tabla 4 del PR-06)

| Riesgo | Prueba | Casos que la ejecutan | Hoy |
|---|---|---|---|
| A01 Control de acceso roto | Padre que pide datos de un estudiante ajeno; IDOR en `/padres/{id}`; permisos del docente; acceso por URL a módulos de otro rol | CP-INT-036 a 038, 050, 053, 059, 064, 065; CP-INT-047, 048, 056; CP-SIS de acceso por URL | Falla esperada (BE-04, BE-05, BE-07, BE-11) |
| A02 Fallas criptográficas | HTTPS en QA y producción; contraseñas con bcrypt (`hash_password`); tokens con `SECRET_KEY` de producción | Revisión de configuración + `tests/test_security.py` | Sin ejecutar (BE-01: rotar la `SECRET_KEY`) |
| A03 Inyección | SQLi y XSS en formularios y parámetros; avatar `.html` o `.svg` (XSS almacenado) | ZAP active scan de la API; CP-INT-072; CP-NF-014 | Falla esperada en el avatar (BE-14) |
| A04 Diseño inseguro | Revocación de sesiones que se desactiva si falla Redis; QR predecible (riesgo aceptado) | CP-INT-009; revisión de BE-17 | Falla esperada (BE-17) |
| A05 Configuración insegura | Cabeceras de seguridad, CORS (`CORS_ORIGINS` sin `*`), errores sin detalles internos, `/static` público | ZAP baseline; CP-INT-071; revisión de Azure | Falla esperada en `/static` (BE-15) |
| A06 Componentes vulnerables | `pip-audit` y `npm audit` | CP-NF-015 | Sin ejecutar |
| A07 Fallas de autenticación | Fuerza bruta (bloqueo tras 5 intentos), expiración de JWT, refresco de usuario desactivado, enlace de recuperación reutilizado | CP-INT-006, 010, 014; CP-NF-019 | Falla esperada (BE-16, BE-13) |
| A08 Integridad de software y datos | Firma del APK y actualización OTA | CP-NF-011 (planeación de la app) | Falla esperada (APP-01) |
| A09 Registro y monitoreo | Registro de inicios de sesión fallidos, bloqueos y errores 500 en los logs de Azure | Revisión de los logs durante S1 | Sin ejecutar |
| A10 SSRF | Rutas o imágenes que la API descargue por URL (fpdf2 lo permite si recibe HTML o imágenes de usuario) | Revisión de código: el boletín no usa imágenes ni HTML del usuario | Sin ejecutar |

### 5.2 Escaneo DAST de la API (CP-NF-003, parte API)

```bash
docker run --rm -v $(pwd)/evidencias/PR-06/api:/zap/wrk ghcr.io/zaproxy/zaproxy:stable \
  zap-api-scan.py -t "$QA_API/openapi.json" -f openapi \
  -z "-config replacer.full_list(0).matchtype=REQ_HEADER -config replacer.full_list(0).matchstr=Authorization \
      -config replacer.full_list(0).replacement='Bearer $TOKEN_ADMIN'" \
  -r S1_zap_api.html -J S1_zap_api.json
```

Meta: 0 alertas altas. Las medias y bajas se registran y se decide cada una en el PR-07.

### 5.3 Otros no funcionales de la API

| ID | Prueba | Meta | Hoy |
|---|---|---|---|
| CP-NF-012 | gitleaks en los tres repositorios y verificación en producción de las credenciales del seed (H-08), comparando hashes, sin iniciar sesión | 0 hallazgos sin rotar y documentar | Falla esperada (BE-01, H-08) |
| CP-NF-014 | Subir un avatar `.html`; pedir `/static/reportes/<archivo>` sin token | Avatar rechazado; reportes 404 | Falla esperada (BE-14, BE-15) |
| CP-NF-015 | `pip-audit -r requirements.txt` y `npm audit --omit=dev` | 0 críticas o altas | Sin ejecutar |
| CP-NF-016 | Quality Gate de SonarQube Cloud | Aprobado (se toma del PR-03) | Sin ejecutar |
| CP-NF-019 | El admin desactiva una cuenta con sesión abierta | La cuenta pierde el acceso al vencer el token de acceso (≤ 30 min) | Falla esperada (BE-13) |

## 6. Ejecución

| Corrida | Fecha | Qué mide |
|---|---|---|
| S1 | 17 – 19 nov 2026 (S9) | Carga, estrés, DAST, OWASP y no funcionales de la API |
| S2 (regresión) | 24 – 26 nov 2026 (S10) | Lo que falló en S1, después de corregir |

```bash
k6 run --env QA_API=$QA_API --env QA_PASSWORD=$QA_PASSWORD \
       --summary-export=evidencias/PR-06/api/S1_k6_carga.json tests/carga/carga_50.js
k6 run --env QA_API=$QA_API --env QA_PASSWORD=$QA_PASSWORD \
       --summary-export=evidencias/PR-06/api/S1_k6_estres.json tests/carga/estres.js
```

- La carga se corre fuera del horario de pruebas manuales para no afectar a la web y la app.
- Durante la carga se guarda una captura de las métricas de Azure (CPU, memoria y respuestas 5xx).

## 7. Criterios

| Indicador | Meta | Origen |
|---|---|---|
| p95 de la API | ≤ 800 ms con 50 usuarios | MC-01 |
| Errores con 50 usuarios | < 1 % | MC-01 |
| Alertas altas de ZAP | 0 | PR-02 (CP-NF-003) |
| Vulnerabilidades críticas o altas | 0 en código y dependencias | PR-01 / MC-01 |

## 8. Registro y defectos

- Resultados en las Tablas 3 (rendimiento) y 4 (OWASP) y en el recuadro de DAST del PR-06.
- Cada alerta alta, cada riesgo OWASP que falle y cada meta de rendimiento que no se cumpla es un bug en Azure Boards con la plantilla del PR-07.
- Las evidencias no deben contener tokens ni contraseñas: el reporte de ZAP se revisa antes de guardarlo.

## 9. Responsables y calendario

| Actividad | Fecha | Responsable |
|---|---|---|
| Preparación del entorno (sección 3) | 10 – 14 nov | Andrés Acero |
| Scripts de k6 y lista `usuarios_ds02.json` | 10 – 14 nov | Samuel Sierra |
| S1 (rendimiento, DAST, OWASP) | 17 – 19 nov | Samuel Sierra |
| S2 (regresión) | 24 – 26 nov | Samuel Sierra |
| Parte API del PR-06 | 21 nov y 26 nov | Samuel Sierra · revisa Mariana Cortés |

## 10. Definición de terminado

- [ ] Carga y estrés ejecutados en QA con el resumen de k6 y las métricas de Azure.
- [ ] ZAP de la API sin alertas altas abiertas, o con su bug registrado.
- [ ] Tabla OWASP Top 10 completa con el caso que respalda cada fila.
- [ ] Parte API del PR-06 diligenciada y revisada.
