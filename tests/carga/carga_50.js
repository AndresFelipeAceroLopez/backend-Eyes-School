// CP-NF-001 · Carga: 0→50 usuarios virtuales en 2 min, 10 min sostenidos, bajada de 1 min.
// Metas (MC-01): p95 ≤ 800 ms · errores < 1 % · ≥ 50 usuarios concurrentes.
//
//   k6 run --env QA_API=https://<qa>/api/v1 --env QA_PASSWORD=$QA_PASSWORD \
//          --summary-export=evidencias/PR-06/api/S1_k6_carga.json tests/carga/carga_50.js
//
// NUNCA contra producción. La contraseña entra por variable de entorno, no está en el código.
//
// POR QUÉ CADA USUARIO VIRTUAL INICIA SESIÓN UNA SOLA VEZ (cambio del 09/11/2026)
// ------------------------------------------------------------------------------
// La primera versión hacía `POST /auth/login` en CADA iteración. Medido en QA, ese endpoint
// tarda ~3 s porque bcrypt es caro por diseño, mientras una consulta normal tarda ~1 s: con un
// login por iteración, dos tercios del p95 eran bcrypt y la prueba medía sobre todo el costo de
// hashear, no el de servir la aplicación. Ningún cliente real hace eso: la app y la web inician
// sesión una vez y reutilizan el token 30 minutos.
//
// Ahora: cada VU inicia sesión en su primera iteración y guarda el token (k6 da un contexto JS
// por VU, así que la variable `sesion` es de ese VU). El endpoint de login se sigue midiendo,
// pero en su propio escenario y a un ritmo realista: 6 inicios de sesión por minuto.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.QA_API;              // URL de QA con /api/v1
const PASSWORD = __ENV.QA_PASSWORD;     // secreto
const CORREO_DOCENTE = __ENV.QA_DOCENTE || 'carlos.jimenez@eyes.edu.co';
const ID_ESTUDIANTE_CLASE = __ENV.QA_ID_ESTUDIANTE_CLASE || '1';
const USUARIOS = JSON.parse(open('./usuarios_ds02.json')); // [{correo, id_estudiante}] (DS-08)
const JSON_HEADERS = { 'Content-Type': 'application/json' };

export const options = {
  scenarios: {
    estudiantes: {
      executor: 'ramping-vus',
      exec: 'estudiante',
      stages: [
        { duration: '2m', target: 50 },
        { duration: '10m', target: 50 },
        { duration: '1m', target: 0 },
      ],
    },
    docente: {
      executor: 'constant-vus',
      exec: 'docente',
      vus: 5,
      duration: '13m',
    },
    // El login se mide aparte, a ritmo de uso real: 6 por minuto durante toda la prueba.
    inicios_de_sesion: {
      executor: 'constant-arrival-rate',
      exec: 'soloLogin',
      rate: 6,
      timeUnit: '1m',
      duration: '13m',
      preAllocatedVUs: 5,
      maxVUs: 20,
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.99'],
    // Desglose para el PR-06: el login es caro por diseño y se reporta aparte de la navegación.
    'http_req_duration{name:POST /auth/login}': ['p(95)<4000'],
    'http_req_duration{escenario:navegacion}': ['p(95)<800'],
  },
};

function iniciarSesion(correo) {
  const r = http.post(`${BASE}/auth/login`, JSON.stringify({ correo, password: PASSWORD }),
                      { headers: JSON_HEADERS, tags: { name: 'POST /auth/login' } });
  check(r, { 'login 200': (x) => x.status === 200 });
  if (r.status !== 200) return null;
  return { headers: { ...JSON_HEADERS, Authorization: `Bearer ${r.json('access_token')}` } };
}

// Contexto por usuario virtual: k6 crea un runtime JS por VU, así que esto NO se comparte.
let sesion = null;

function sesionDe(correo) {
  if (sesion === null) sesion = iniciarSesion(correo);
  return sesion;
}

export function estudiante() {
  const u = USUARIOS[(__VU - 1) % USUARIOS.length];
  const auth = sesionDe(u.correo);
  if (!auth) { sleep(1); return; }

  const notas = http.get(`${BASE}/estudiantes/${u.id_estudiante}/notas`,
                         { ...auth, tags: { name: 'GET /estudiantes/{id}/notas', escenario: 'navegacion' } });
  check(notas, { 'notas 200': (r) => r.status === 200 });
  sleep(1);
}

export function docente() {
  const auth = sesionDe(CORREO_DOCENTE);
  if (!auth) { sleep(1); return; }
  const hoy = new Date().toISOString().slice(0, 10);

  const lista = http.get(`${BASE}/asistencia?fecha=${hoy}`,
                         { ...auth, tags: { name: 'GET /asistencia?fecha', escenario: 'navegacion' } });
  check(lista, { 'asistencia 200': (r) => r.status === 200 });

  // «clase» no tiene restricción de duplicado por día, así que se puede repetir bajo carga.
  const registro = http.post(`${BASE}/asistencia`, JSON.stringify({
    id_estudiante: Number(ID_ESTUDIANTE_CLASE), fecha: hoy, estado: 'Presente', tipo: 'clase',
  }), { ...auth, tags: { name: 'POST /asistencia', escenario: 'navegacion' } });
  check(registro, { 'asistencia creada 201': (r) => r.status === 201 });
  sleep(1);
}

// Tráfico de inicio de sesión, separado para que su costo (bcrypt) no se confunda con el de
// navegar. Cada iteración usa una cuenta distinta y no reutiliza token a propósito.
export function soloLogin() {
  const u = USUARIOS[Math.floor(Math.random() * USUARIOS.length)];
  iniciarSesion(u.correo);
}
