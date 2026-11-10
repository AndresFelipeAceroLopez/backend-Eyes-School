# Planeación de pruebas de aceptación (UAT) — Backend (API FastAPI) · Eyes School

> **Tipo de documento:** planeación de QA para el PR-08 (Informe de pruebas de aceptación y acta). La API no tiene pantallas: el PO la acepta a través de la web y de la app. Esta planeación describe lo que el backend debe dejar listo y vigilar para que la UAT de la web y de la app se pueda hacer y su resultado sea confiable. No contiene resultados.
> **Pensado para:** cualquier integrante del equipo o una IA que no conoce el proyecto.
> **Elaboró:** Mariana Cortés (QA) · **Revisa:** Samuel Sierra (líder de pruebas) · **Aprueba:** Sergio Gómez (PO)
> **Plazo:** preparación en S9 y soporte durante la sesión de UAT en S10 (22 – 28 nov 2026).

---

## 1. Correcciones de la API que condicionan escenarios de aceptación

Si una corrección no está fusionada y desplegada en QA antes de la sesión, sus escenarios no se pueden aceptar. Esta tabla sale del PR-02 v0.2 (escenarios con falla esperada por una corrección del backend):

| Corrección | Sprint planeado | Escenarios CP-ACE que dependen de ella |
|---|---|---|
| BE-03 | S7 (día 1) | CP-ACE-001, CP-ACE-007 |
| BE-04 | S7 | CP-ACE-050, CP-ACE-052, CP-ACE-053 |
| BE-06 | S7 | CP-ACE-055 |
| BE-07 | S8 | CP-ACE-075, CP-ACE-076 |
| BE-08 | S7 | CP-ACE-039, CP-ACE-041, CP-ACE-044, CP-ACE-045 |
| BE-09 | S7 | CP-ACE-017 |
| BE-12 | S7 | CP-ACE-001, CP-ACE-011, CP-ACE-022 |
| BE-13 | S8 | CP-ACE-017, CP-ACE-019 |
| BE-15 | S8 | CP-ACE-091 |
| BE-16 | S8 | CP-ACE-002 |
| BE-17 | S7 | CP-ACE-019 |
| BE-18 | S8 | CP-ACE-067, CP-ACE-085, CP-ACE-086 |
| BE-19 | S8 | CP-ACE-092 |

Una semana antes de la UAT (fin de S9), el líder de pruebas confirma con esta tabla qué escenarios llegan listos y se lo informa al PO.

## 2. Preparación del entorno (S9)

| # | Tarea | Detalle |
|---|---|---|
| 1 | Versión congelada | Desplegar en QA la versión que se va a aceptar y anotar el commit. No se despliega nada durante la sesión |
| 2 | Respaldo | Respaldo de la base de QA antes de la sesión (`pg_dump`), para poder volver al estado inicial si una prueba deja datos inconsistentes |
| 3 | Datos | La mañana de la sesión: `schema.sql` → `seed_data.sql` → `seed_estudiantes_sinteticos.sql` → `scripts/qa_reset_passwords.py` (BE-INF-2). Solo datos sintéticos: ningún dato real de estudiantes menores de edad |
| 4 | Usuarios por rol | DS-01 (un usuario por rol; padre de un hijo) y DS-03 (padre de dos hijos). La contraseña se entrega en la sesión por canal privado y se cambia al terminar |
| 5 | Notificaciones | `FIREBASE_CREDENTIALS_JSON` configurado en la API de QA y prueba previa de una notificación al POCO X7 |
| 6 | Prueba de humo | `GET /api/v1/cursos` responde 200 y cada rol inicia sesión y ve su inicio |
| 7 | Monitoreo | Registro de la API (Azure → Log stream) abierto durante la sesión para ver errores 500 en el momento |

## 3. Soporte durante la sesión

- Andrés Acero acompaña la sesión con acceso a Azure y a la base de QA.
- Si aparece un error 500 o un dato inconsistente, se anota el escenario, la hora y el registro de la API (sin tokens) para el bug, y se sigue con el siguiente escenario. **No se corrige código durante la sesión.**
- Si la API de QA no responde por más de 30 min, la sesión se suspende y se reprograma dentro de S10 (criterio de suspensión del PR-01, adaptado a la sesión).

## 4. Después de la sesión

1. Registrar en Azure Boards (etiqueta `uat`) los bugs de la API detectados en la sesión.
2. Cambiar `QA_PASSWORD` y volver a ejecutar `scripts/qa_reset_passwords.py`.
3. Si el acta se firma con observaciones, planear las correcciones de la API con fecha antes del plazo del acta.

## 5. Responsables y calendario

| Actividad | Fecha | Responsable |
|---|---|---|
| Confirmar qué correcciones llegan a la UAT (tabla de la sección 1) | Fin de S9 (21 nov) | Samuel Sierra · Andrés Acero |
| Preparación del entorno (sección 2) | Día de la sesión, antes de empezar | Andrés Acero |
| Soporte en la sesión | Sesión de UAT (S10) | Andrés Acero |
| Bugs de la API y cambio de contraseña | Mismo día de la sesión | Andrés Acero · Mariana Cortés |

## 6. Definición de terminado

- [ ] Versión congelada y respaldo de la base de QA antes de la sesión.
- [ ] Prueba de humo y notificación de prueba superadas.
- [ ] Bugs de la API de la sesión registrados y contraseña de QA cambiada.
