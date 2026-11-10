// CP-NF-002 · Estrés: de 50 a 200 usuarios en escalones de 25 cada 2 min, hasta que la API se
// degrade; luego baja a 0 y se comprueba que se recupera sin reiniciar.
//
//   k6 run --env QA_API=https://<qa>/api/v1 --env QA_PASSWORD=$QA_PASSWORD \
//          --summary-export=evidencias/PR-06/api/S1_k6_estres.json tests/carga/estres.js
//
// NUNCA contra producción. Se corre fuera del horario de pruebas manuales.
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.QA_API;
const PASSWORD = __ENV.QA_PASSWORD;
const USUARIOS = JSON.parse(open('./usuarios_ds02.json'));
const JSON_HEADERS = { 'Content-Type': 'application/json' };

const escalones = [];
for (let vus = 50; vus <= 200; vus += 25) {
  escalones.push({ duration: '2m', target: vus });
}

export const options = {
  stages: [
    ...escalones,
    { duration: '2m', target: 0 },     // bajada
    { duration: '2m', target: 5 },     // recuperación: debe volver a responder sin reiniciar
  ],
  // En estrés no se aborta: interesa ver en qué punto se degrada, no que pase el umbral.
  thresholds: {
    http_req_failed: [{ threshold: 'rate<0.05', abortOnFail: false }],
  },
};

export default function () {
  const u = USUARIOS[(__VU - 1) % USUARIOS.length];
  const login = http.post(`${BASE}/auth/login`, JSON.stringify({ correo: u.correo, password: PASSWORD }),
                          { headers: JSON_HEADERS, tags: { name: 'POST /auth/login' } });
  check(login, { 'login 200': (r) => r.status === 200 });
  if (login.status !== 200) { sleep(1); return; }

  const auth = { headers: { Authorization: `Bearer ${login.json('access_token')}` } };
  const notas = http.get(`${BASE}/estudiantes/${u.id_estudiante}/notas`,
                         { ...auth, tags: { name: 'GET /estudiantes/{id}/notas' } });
  check(notas, { 'notas 200': (r) => r.status === 200 });
  sleep(1);
}
