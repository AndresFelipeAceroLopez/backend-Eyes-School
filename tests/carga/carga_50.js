// CP-NF-001 · Carga: 0→50 usuarios virtuales en 2 min, 10 min sostenidos, bajada de 1 min.
// Metas (MC-01): p95 ≤ 800 ms · errores < 1 % · ≥ 50 usuarios concurrentes.
//
//   k6 run --env QA_API=https://<qa>/api/v1 --env QA_PASSWORD=$QA_PASSWORD \
//          --summary-export=evidencias/PR-06/api/S1_k6_carga.json tests/carga/carga_50.js
//
// NUNCA contra producción. La contraseña entra por variable de entorno, no está en el código.
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
  },
  thresholds: {
    http_req_duration: ['p(95)<800'],
    http_req_failed: ['rate<0.01'],
    checks: ['rate>0.99'],
  },
};

function iniciarSesion(correo) {
  const r = http.post(`${BASE}/auth/login`, JSON.stringify({ correo, password: PASSWORD }),
                      { headers: JSON_HEADERS, tags: { name: 'POST /auth/login' } });
  check(r, { 'login 200': (x) => x.status === 200 });
  return { headers: { ...JSON_HEADERS, Authorization: `Bearer ${r.json('access_token')}` } };
}

export function estudiante() {
  const u = USUARIOS[(__VU - 1) % USUARIOS.length];
  const auth = iniciarSesion(u.correo);
  const notas = http.get(`${BASE}/estudiantes/${u.id_estudiante}/notas`,
                         { ...auth, tags: { name: 'GET /estudiantes/{id}/notas' } });
  check(notas, { 'notas 200': (r) => r.status === 200 });
  sleep(1);
}

export function docente() {
  const auth = iniciarSesion(CORREO_DOCENTE);
  const hoy = new Date().toISOString().slice(0, 10);

  const lista = http.get(`${BASE}/asistencia?fecha=${hoy}`,
                         { ...auth, tags: { name: 'GET /asistencia?fecha' } });
  check(lista, { 'asistencia 200': (r) => r.status === 200 });

  // «clase» no tiene restricción de duplicado por día, así que se puede repetir bajo carga.
  const registro = http.post(`${BASE}/asistencia`, JSON.stringify({
    id_estudiante: Number(ID_ESTUDIANTE_CLASE), fecha: hoy, estado: 'Presente', tipo: 'clase',
  }), { ...auth, tags: { name: 'POST /asistencia' } });
  check(registro, { 'asistencia creada 201': (r) => r.status === 201 });
  sleep(1);
}
