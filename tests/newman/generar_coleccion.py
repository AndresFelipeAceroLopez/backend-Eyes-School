"""Genera `eyes_school_api.postman_collection.json` (BE-IT-2) a partir de la tabla de casos.

    python tests/newman/generar_coleccion.py

Cada petición lleva el ID del caso del PR-02 en el nombre (por ejemplo «CP-INT-031 …») y
pruebas `pm.test` de código de estado, cuerpo y tiempo de respuesta (≤ 800 ms, la meta del
MC-01). La contraseña NO está en la colección: entra con `--env-var QA_PASSWORD=...`.

Los casos se infirieron del endpoint, de la corrección BE-xx asociada y del resultado esperado
de la planeación de integración; si el PR-02 define otro resultado, se ajusta aquí y se vuelve a
generar. La lista de IDs se valida contra la tabla de `docs/test/Integracion/...`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

AQUI = Path(__file__).parent
RAIZ = AQUI.parents[1]
PLANEACION = RAIZ / "docs/test/Integracion/planeacion-pruebas-integracion-backend.md"

# Rol → variable de colección con su access token (se llena en «00 Sesiones»).
TOKENS = {
    "admin": "token_admin", "docente": "token_docente", "docente2": "token_docente2",
    "estudiante": "token_estudiante", "padre1": "token_padre1", "padre2": "token_padre2",
    "temporal": "token_temporal",
}
LOGINS = {
    "admin": "correo_admin", "docente": "correo_docente", "docente2": "correo_docente2",
    "estudiante": "correo_estudiante", "padre1": "correo_padre1", "padre2": "correo_padre2",
}

CASOS: list[dict] = []


def caso(id_, nombre, metodo, ruta, rol=None, body=None, status=200, query=None, checks=(),
         capturar=None, form=None, sin_token=False, carpeta="Auth", pre=None):
    CASOS.append(dict(id=id_, nombre=nombre, metodo=metodo, ruta=ruta, rol=rol, body=body,
                      status=status, query=query or {}, checks=list(checks),
                      capturar=capturar or {}, form=form, carpeta=carpeta, sin_token=sin_token,
                      pre=pre))


def cuenta(sufijo_doc):
    return {"tipo_documento": "CC", "numero_documento": "{{doc_" + sufijo_doc + "}}",
            "primer_nombre": "Qa", "primer_apellido": "Newman", "password": "{{QA_PASSWORD}}"}


# ------------------------------- Auth
J = "json.access_token"
caso(1, "Login docente válido → 200", "POST", "/auth/login", body={"correo": "{{correo_docente}}", "password": "{{QA_PASSWORD}}"}, checks=["pm.expect(pm.response.json()).to.have.property('refresh_token')"])
caso(2, "Login con contraseña incorrecta → 401", "POST", "/auth/login", body={"correo": "{{correo_docente}}", "password": "Incorrecta#1"}, status=401, checks=["pm.expect(pm.response.json().detail).to.eql('Credenciales inválidas')"])
caso(3, "Login con correo inexistente → 401 genérico", "POST", "/auth/login", body={"correo": "nadie.{{sufijo}}@example.com", "password": "{{QA_PASSWORD}}"}, status=401, checks=["pm.expect(pm.response.json().detail).to.eql('Credenciales inválidas')"])
caso(4, "Login con campos vacíos → 422", "POST", "/auth/login", body={}, status=422)
caso(7, "Login con el correo en mayúsculas → 200 (BE-12)", "POST", "/auth/login", body={"correo": "{{correo_docente_mayus}}", "password": "{{QA_PASSWORD}}"})
caso(8, "Refresh con un refresh token válido → 200", "POST", "/auth/refresh", body={"refresh_token": "{{refresh_estudiante}}"}, checks=["pm.expect(pm.response.json()).to.have.property('access_token')"])
caso(11, "Recuperar contraseña: respuesta neutra → 200", "POST", "/auth/forgot-password", body={"correo": "nadie.{{sufijo}}@example.com"}, checks=["pm.expect(pm.response.json().message).to.include('Si el correo está registrado')"])
caso(16, "Registro de un docente → 201 e inactivo", "POST", "/auth/register", body={**cuenta("docente"), "correo": "docente.{{sufijo}}@example.com", "id_rol": 1}, status=201, capturar={"usuario_docente_id": "id_usuario"}, checks=["pm.expect(pm.response.json().estado).to.eql(false)"])
caso(5, "Login de un docente recién registrado (pendiente) → 403 con el motivo (N-31)", "POST", "/auth/login", body={"correo": "docente.{{sufijo}}@example.com", "password": "{{QA_PASSWORD}}"}, status=403, checks=["pm.expect(pm.response.json().detail).to.include('pendiente de validación')"])
caso(17, "Registro de un padre vinculado a un estudiante → 201", "POST", "/auth/register", body={**cuenta("padre"), "correo": "padre.{{sufijo}}@example.com", "id_rol": 4, "id_estudiante_vinculado": "{{id_estudiante_ds01}}", "parentesco": "Madre"}, status=201, capturar={"usuario_padre_id": "id_usuario"})
caso(18, "Registro con el correo repetido en otras mayúsculas → 409 (BE-12)", "POST", "/auth/register", body={**cuenta("dup"), "correo": "PADRE.{{sufijo}}@example.com", "id_rol": 4}, status=409)
caso(19, "Registro con documento repetido → 409", "POST", "/auth/register", body={**cuenta("padre"), "correo": "otro.{{sufijo}}@example.com", "id_rol": 4}, status=409)
caso(20, "Registro con contraseña débil → 422 (BE-09)", "POST", "/auth/register", body={**cuenta("dup"), "correo": "debil.{{sufijo}}@example.com", "id_rol": 4, "password": "Colegio2026"}, status=422)
caso(21, "Registro sin campos obligatorios → 422", "POST", "/auth/register", body={"correo": "x.{{sufijo}}@example.com"}, status=422)
caso(73, "GET /auth/me → 200", "GET", "/auth/me", rol="estudiante", checks=["pm.expect(pm.response.json().nombre_rol).to.eql('estudiante')"])
# ------------------------------- Usuarios
c = "Usuarios"
caso(22, "Admin crea un usuario → 201", "POST", "/usuarios", rol="admin", body={**cuenta("admin_crea"), "correo": "creado.{{sufijo}}@example.com", "id_rol": 2}, status=201, capturar={"usuario_creado_id": "id_usuario"}, carpeta=c)
caso(23, "Docente intenta crear un usuario → 403", "POST", "/usuarios", rol="docente", body={**cuenta("admin_crea"), "correo": "x.{{sufijo}}@example.com", "id_rol": 2}, status=403, carpeta=c)
caso(24, "Admin edita un usuario → 200", "PUT", "/usuarios/{{usuario_creado_id}}", rol="admin", body={"primer_nombre": "Editado"}, checks=["pm.expect(pm.response.json().primer_nombre).to.eql('Editado')"], carpeta=c)
caso(25, "Admin elimina un usuario → 204", "DELETE", "/usuarios/{{usuario_padre_id}}", rol="admin", status=204, carpeta=c)
caso(26, "Admin lista usuarios → 200", "GET", "/usuarios", rol="admin", checks=["pm.expect(pm.response.json()).to.be.an('array')"], carpeta=c)
caso(27, "Estudiante intenta listar usuarios → 403", "GET", "/usuarios", rol="estudiante", status=403, carpeta=c)
caso(28, "Cambiar la propia contraseña sin la actual → 400 (BE-09)", "PUT", "/usuarios/{{id_usuario_docente}}", rol="docente", body={"password": "Nueva#2026x"}, status=400, carpeta=c)
caso(77, "Admin crea un usuario con correo repetido en mayúsculas → 409 (BE-12)", "POST", "/usuarios", rol="admin", body={**cuenta("dup2"), "correo": "CREADO.{{sufijo}}@example.com", "id_rol": 2}, status=409, carpeta=c)
caso(78, "Admin crea un usuario con documento repetido → 409", "POST", "/usuarios", rol="admin", body={**cuenta("admin_crea"), "correo": "otro2.{{sufijo}}@example.com", "id_rol": 2}, status=409, carpeta=c)
caso(79, "Docente edita a otro usuario → 403", "PUT", "/usuarios/{{usuario_creado_id}}", rol="docente", body={"primer_nombre": "X"}, status=403, carpeta=c)
# ------------------------------- Asistencia
a = "Asistencia"
H = "{{hoy}}"
caso(30, "Primera entrada del día → 201", "POST", "/asistencia", rol="docente", body={"id_estudiante": "{{id_estudiante_ds03a}}", "fecha": H, "estado": "Presente", "tipo": "entrada"}, status=201, capturar={"asistencia_id": "id_asistencia"}, carpeta=a)
caso(31, "Segunda entrada el mismo día → 409 (BE-08)", "POST", "/asistencia", rol="docente", body={"id_estudiante": "{{id_estudiante_ds03a}}", "fecha": H, "estado": "Presente", "tipo": "entrada"}, status=409, carpeta=a)
caso(32, "Salida después de la entrada → 201", "POST", "/asistencia", rol="docente", body={"id_estudiante": "{{id_estudiante_ds03a}}", "fecha": H, "estado": "Presente", "tipo": "salida"}, status=201, capturar={"asistencia_salida_id": "id_asistencia"}, carpeta=a)
caso(33, "Segunda salida el mismo día → 409 (BE-08)", "POST", "/asistencia", rol="docente", body={"id_estudiante": "{{id_estudiante_ds03a}}", "fecha": H, "estado": "Presente", "tipo": "salida"}, status=409, carpeta=a)
caso(34, "Salida sin entrada previa → 400 (BE-08)", "POST", "/asistencia", rol="docente", body={"id_estudiante": "{{id_estudiante_ds01}}", "fecha": H, "estado": "Presente", "tipo": "salida"}, status=400, checks=["pm.expect(pm.response.json().detail).to.eql('No hay entrada registrada hoy para este estudiante')"], carpeta=a)
caso(35, "registrado_por sale del token, no del cuerpo (BE-10)", "POST", "/asistencia", rol="docente", body={"id_estudiante": "{{id_estudiante_ds03a}}", "fecha": H, "estado": "Presente", "tipo": "clase", "registrado_por": 999999}, status=201, capturar={"asistencia_clase_id": "id_asistencia"}, checks=["pm.expect(pm.response.json().registrado_por).to.eql(parseInt(pm.collectionVariables.get('id_usuario_docente')))"], carpeta=a)
caso(36, "Padre pide la asistencia de un estudiante ajeno → 403 (BE-04)", "GET", "/asistencia", rol="padre1", query={"id_estudiante": "{{id_estudiante_ds03a}}"}, status=403, carpeta=a)
caso(37, "Padre pide asistencia sin filtro → 400 (BE-04)", "GET", "/asistencia", rol="padre1", status=400, carpeta=a)
caso(38, "Padre pide el detalle de una asistencia ajena → 403 (BE-04)", "GET", "/asistencia/{{asistencia_id}}", rol="padre1", status=403, carpeta=a)
caso(39, "Padre lee la asistencia de su hijo → 200", "GET", "/estudiantes/{{id_estudiante_ds01}}/asistencia", rol="padre1", carpeta=a)
caso(40, "Admin anula un registro de asistencia → 204", "DELETE", "/asistencia/{{asistencia_clase_id}}", rol="admin", status=204, carpeta=a)
caso(81, "Admin lista la asistencia de hoy → 200", "GET", "/asistencia", rol="admin", query={"fecha": H}, carpeta=a)
# ------------------------------- Notas
n = "Notas"
NOTA = {"id_estudiante": "{{id_estudiante_ds03a}}", "id_materia": "{{id_materia_docente}}", "id_periodo": 4, "nota": 4.0}
caso(41, "Docente con asignación crea una nota → 201", "POST", "/notas", rol="docente", body=NOTA, status=201, capturar={"nota_id": "id_nota"}, carpeta=n)
caso(42, "Crear una nota sin autenticar → 401", "POST", "/notas", body=NOTA, status=401, sin_token=True, carpeta=n)
caso(43, "Nota de 5.1 → 422 (BE-06)", "POST", "/notas", rol="docente", body={**NOTA, "nota": 5.1, "id_periodo": 3}, status=422, carpeta=n)
caso(44, "Un padre intenta calificar → 403", "POST", "/notas", rol="padre1", body=NOTA, status=403, carpeta=n)
caso(45, "Nota repetida (estudiante, materia, periodo) → 409", "POST", "/notas", rol="docente", body=NOTA, status=409, carpeta=n)
caso(46, "Editar una nota a 5.1 → 422 (BE-06)", "PUT", "/notas/{{nota_id}}", rol="docente", body={"nota": 5.1}, status=422, carpeta=n)
caso(47, "Docente sin asignación califica la materia → 403 (BE-11)", "POST", "/notas", rol="docente2", body={**NOTA, "id_periodo": 3}, status=403, carpeta=n)
caso(48, "El docente solo lista notas de los cursos que dicta (BE-11)", "GET", "/notas", rol="docente2", query={"limit": 500}, checks=["pm.expect(pm.response.json().every(x => x.id_estudiante != parseInt(pm.collectionVariables.get('id_estudiante_ds03a')) || pm.collectionVariables.get('docente2_dicta_curso_ds03a') === 'true')).to.be.true"], carpeta=n)
caso(50, "Estudiante lee sus notas → 200", "GET", "/estudiantes/{{id_estudiante_ds01}}/notas", rol="estudiante", carpeta=n)
caso(51, "Boletín PDF del estudiante → 200 application/pdf", "GET", "/notas/estudiantes/{{id_estudiante_ds01}}/boletin/pdf", rol="estudiante", checks=["pm.expect(pm.response.headers.get('Content-Type')).to.include('application/pdf')"], carpeta=n)
caso(52, "Boletín de un estudiante sin notas → 404 con el mensaje (BE-19)", "GET", "/notas/estudiantes/{{id_estudiante_sin_notas}}/boletin/pdf", rol="admin", status=404, checks=["pm.expect(pm.environment.get('id_estudiante_sin_notas'), 'no se encontró ningún estudiante sin notas en este entorno').to.be.ok", "pm.expect(pm.response.json().detail).to.eql('No hay datos disponibles para generar el boletín.')"], carpeta=n)
caso(53, "Padre pide el boletín de un estudiante ajeno → 403", "GET", "/notas/estudiantes/{{id_estudiante_ds03a}}/boletin/pdf", rol="padre1", status=403, carpeta=n)
caso(80, "Periodo fuera de 1 a 4 → 422", "POST", "/notas", rol="docente", body={**NOTA, "id_periodo": 5}, status=422, carpeta=n)
caso(82, "Estudiante lee sus propias notas → 200", "GET", "/estudiantes/{{id_estudiante_ds01}}/notas", rol="estudiante", carpeta=n)
# ------------------------------- Novedades
v = "Novedades"
NOV = {"id_estudiante": "{{id_estudiante_ds01}}", "id_tipo_novedad": 1, "fecha": H, "descripcion": "Novedad de prueba Newman"}
caso(54, "Docente registra una novedad → 201", "POST", "/novedades", rol="docente", body=NOV, status=201, capturar={"novedad_id": "id_novedad"}, carpeta=v)
caso(55, "Estudiante intenta registrar una novedad → 403", "POST", "/novedades", rol="estudiante", body=NOV, status=403, carpeta=v)
caso(56, "Otro docente edita la novedad ajena → 403 (BE-11)", "PUT", "/novedades/{{novedad_id}}", rol="docente2", body={"descripcion": "Modificada"}, status=403, carpeta=v)
caso(59, "Padre lee las novedades de su hijo → 200", "GET", "/estudiantes/{{id_estudiante_ds01}}/novedades", rol="padre1", carpeta=v)
caso(83, "Admin lista las novedades → 200", "GET", "/novedades", rol="admin", carpeta=v)
# ------------------------------- Padres y dashboard
p = "Padres y dashboard"
caso(60, "Inicio del estudiante → 200, no 500 (BE-03)", "GET", "/dashboard/estudiante", rol="estudiante", carpeta=p)
caso(61, "Inicio del padre → 200", "GET", "/dashboard/padre", rol="padre1", carpeta=p)
caso(62, "Padre con dos hijos lista a los dos (BE-07)", "GET", "/padres/me/hijos", rol="padre2", checks=["pm.expect(pm.response.json()).to.have.lengthOf(2)"], carpeta=p)
caso(63, "GET /padres/me con dos hijos → 200, no 500 (BE-07)", "GET", "/padres/me", rol="padre2", carpeta=p)
caso(64, "Dashboard de un estudiante que no es su hijo → 403 (BE-07)", "GET", "/dashboard/padre", rol="padre2", query={"id_estudiante": "{{id_estudiante_ds02_ajeno}}"}, status=403, carpeta=p)
caso(65, "Padre lee el vínculo de otro padre → 403 (BE-05)", "GET", "/padres/{{id_padre_ajeno}}", rol="padre1", status=403, carpeta=p)
caso(74, "GET /estudiantes/me → 200", "GET", "/estudiantes/me", rol="estudiante", carpeta=p)
# ------------------------------- Horarios, asignaciones
h = "Horarios y asignaciones"
caso(66, "Horario de un curso → 200", "GET", "/horarios", rol="docente", query={"id_curso": "{{id_curso_ds01}}"}, carpeta=h)
caso(67, "Asignaciones del docente → 200", "GET", "/asignaciones", rol="docente", query={"id_profesor": "{{id_profesor_docente}}"}, carpeta=h)
# ------------------------------- Reportes y archivos
r = "Reportes y archivos"
caso(68, "Admin lista los reportes → 200", "GET", "/reportes", rol="admin", carpeta=r)
caso(69, "Subir el archivo de un reporte → 200", "POST", "/reportes/archivo", rol="admin", form="datos/reporte.pdf", capturar={"reporte_archivo": "$"}, carpeta=r)
caso(69, "Crear el reporte con el archivo subido → 201", "POST", "/reportes", rol="admin", body={"nombre_reporte": "Reporte Newman {{sufijo}}", "tipo_reporte": "Asistencia", "fecha_inicio": "2026-01-01", "fecha_fin": "2026-01-31", "id_administrador": "{{id_administrador}}", "archivo_generado": "{{reporte_archivo}}"}, status=201, capturar={"reporte_id": "id_reporte"}, carpeta=r)
caso(70, "Admin descarga el archivo del reporte → 200", "GET", "/reportes/{{reporte_id}}/archivo", rol="admin", carpeta=r)
caso(71, "Reporte por /static sin token → 404 (BE-15)", "GET", "{{reporte_archivo}}", status=404, sin_token=True, carpeta=r)

# ------------------------------- Sesión con cuenta temporal (BC-06, 13/11/2026)
# Estos seis casos estaban asignados a pytest local porque bloquean, desactivan o cambian la
# foto de la cuenta con la que se prueban. Ahora corren también contra QA, pero sobre una cuenta
# TEMPORAL que la carpeta crea al empezar y la limpieza borra al final: nunca se bloquea ni se
# desactiva una cuenta del seed. El orden importa: primero lo que necesita la cuenta activa
# (009, 072, 058), después la desactivación (029, 010), que usa una sesión abierta antes, y al
# final el bloqueo (006): los fallos se cuentan aunque la cuenta esté desactivada, y el bloqueo
# se evalúa antes que el estado, así que si fuera primero taparía el mensaje de N-31.
t = "Sesión con cuenta temporal"
REFRESH_TEMPORAL_1 = {"refresh_token": "{{refresh_temporal_1}}"}
LOGIN_TEMPORAL = {"correo": "qa.temporal.{{sufijo}}@example.com", "password": "{{QA_PASSWORD}}"}
CERRAR_SESION_1 = [
    "pm.sendRequest({ url: pm.environment.get('base_url') + '/auth/logout', method: 'POST',",
    "  header: { 'Content-Type': 'application/json' },",
    "  body: { mode: 'raw', raw: JSON.stringify({ refresh_token: pm.collectionVariables.get('refresh_temporal_1') }) }",
    "}, (err, res) => pm.collectionVariables.set('logout_temporal', err ? 'error' : String(res.code)));",
]
CINCO_FALLOS = [
    "const base = pm.environment.get('base_url');",
    "const correo = 'qa.temporal.' + pm.collectionVariables.get('sufijo') + '@example.com';",
    "const fallo = (i) => {",
    "  if (i >= 5) return;",
    "  pm.sendRequest({ url: base + '/auth/login', method: 'POST',",
    "    header: { 'Content-Type': 'application/json' },",
    "    body: { mode: 'raw', raw: JSON.stringify({ correo: correo, password: 'Incorrecta#1' }) }",
    "  }, () => fallo(i + 1));",
    "};",
    "fallo(0);",
]
# N-31: el login de la cuenta desactivada dice que está desactivada, no pendiente.
LOGIN_DESACTIVADA = [
    "pm.sendRequest({ url: pm.environment.get('base_url') + '/auth/login', method: 'POST',",
    "  header: { 'Content-Type': 'application/json' },",
    "  body: { mode: 'raw', raw: JSON.stringify({ correo: 'qa.temporal.' + pm.collectionVariables.get('sufijo') + '@example.com', password: pm.environment.get('QA_PASSWORD') }) }",
    "}, (err, res) => pm.collectionVariables.set('login_desactivada', err ? 'error' : res.code + ' ' + res.text()));",
]
caso(9, "Refresh después de cerrar sesión → 401 (BE-13, BE-17)", "POST", "/auth/refresh", body=REFRESH_TEMPORAL_1, status=401, pre=CERRAR_SESION_1, checks=["pm.expect(pm.collectionVariables.get('logout_temporal')).to.eql('204')"], carpeta=t)
caso(72, "Avatar que no es una imagen → 400 (BE-14)", "POST", "/auth/me/avatar", rol="temporal", form="datos/reporte.pdf", status=400, checks=["pm.expect(pm.response.json().detail).to.include('imagen')"], carpeta=t)
caso(58, "La cuenta registra su teléfono para notificaciones → 201 (BE-18)", "POST", "/dispositivos", rol="temporal", body={"token_fcm": "qa-newman-{{sufijo}}-dispositivo", "plataforma": "android"}, status=201, checks=["pm.expect(pm.response.json().token_fcm).to.eql('qa-newman-' + pm.collectionVariables.get('sufijo') + '-dispositivo')"], carpeta=t)
caso(29, "Admin desactiva la cuenta → 200 con estado false (BE-13)", "PATCH", "/usuarios/{{usuario_temporal_id}}/estado", rol="admin", query={"estado": "false"}, checks=["pm.expect(pm.response.json().estado).to.eql(false)"], carpeta=t)
caso(10, "Una cuenta desactivada no renueva su sesión → 401 (BE-13)", "POST", "/auth/refresh", body={"refresh_token": "{{refresh_temporal_2}}"}, status=401, pre=LOGIN_DESACTIVADA, checks=["pm.expect(pm.collectionVariables.get('login_desactivada')).to.include('Cuenta desactivada')"], carpeta=t)
caso(6, "Sexto intento con la clave CORRECTA tras 5 fallos → 429 (BE-16)", "POST", "/auth/login", body=LOGIN_TEMPORAL, status=429, pre=CINCO_FALLOS, checks=["pm.expect(pm.response.json().detail).to.include('Demasiados intentos')"], carpeta=t)

ORDEN = ["Auth", "Usuarios", "Asistencia", "Notas", "Novedades", "Padres y dashboard",
         "Horarios y asignaciones", "Reportes y archivos", "Sesión con cuenta temporal"]


def ids_de_la_planeacion() -> set[int]:
    ids = set()
    for linea in PLANEACION.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| CP-INT-(\d{3}) \|.*\| (Newman \(QA\)[^|]*) \|", linea)
        if m:
            ids.add(int(m.group(1)))
    return ids


def _script(lineas):
    return {"type": "text/javascript", "exec": lineas}


def _pruebas(c):
    ident = f"CP-INT-{c['id']:03d}"
    js = [f"pm.test('{ident} → {c['status']}', () => pm.response.to.have.status({c['status']}));",
          # Tiempo aparte del resultado funcional: el umbral sale de `umbral_ms` (800 ms por
          # defecto, el del MC-01; en QA se corre con 3000 por la decisión del PO del 10/11).
          f"pm.test('{ident} TIEMPO ≤ ' + (pm.environment.get('umbral_ms') || 800) + ' ms', () => pm.expect(pm.response.responseTime).to.be.below(Number(pm.environment.get('umbral_ms') || 800)));"]
    for chk in c["checks"]:
        js.append(f"pm.test('{ident} cuerpo', () => {{ {chk}; }});")
    for var, campo in c["capturar"].items():
        valor = "pm.response.text().replace(/\"/g, '')" if campo == "$" else f"pm.response.json().{campo}"
        js.append(f"if (pm.response.code < 300) pm.collectionVariables.set('{var}', {valor});")
    return js


def _peticion(c):
    ruta = c["ruta"]
    cabeceras = [{"key": "Content-Type", "value": "application/json"}] if c["body"] is not None else []
    if c["rol"] and not c["sin_token"]:
        cabeceras.append({"key": "Authorization", "value": "Bearer {{" + TOKENS[c["rol"]] + "}}"})
    if ruta.startswith("{{"):
        url = "{{base_host}}" + ruta
    else:
        url = {"raw": "{{base_url}}" + ruta, "host": ["{{base_url}}"],
               "path": [s for s in ruta.split("/") if s]}
    if c["query"] and isinstance(url, dict):
        url["query"] = [{"key": k, "value": str(val)} for k, val in c["query"].items()]
        url["raw"] += "?" + "&".join(f"{k}={val}" for k, val in c["query"].items())
    req = {"method": c["metodo"], "header": cabeceras, "url": url}
    if c["body"] is not None:
        req["body"] = {"mode": "raw", "raw": json.dumps(c["body"], ensure_ascii=False),
                       "options": {"raw": {"language": "json"}}}
    if c["form"]:
        req["body"] = {"mode": "formdata", "formdata": [{"key": "file", "type": "file", "src": c["form"]}]}
    return req


# CP-INT-052 necesita un estudiante SIN notas, y su id cambia de un entorno a otro. Antes se
# fijaba a mano en `id_estudiante_sin_notas` y, como nadie lo hacía, el caso se omitía siempre.
# Ahora, si la variable está vacía, el caso lo busca él mismo con el token de admin: lista los
# estudiantes y, empezando por los más nuevos (los menos probables de tener notas), se queda con
# el primero cuyo `GET /estudiantes/{id}/notas` devuelve `[]`, que es la misma condición con la
# que el boletín responde 404. Solo lee: no crea ni borra nada. Si se fija la variable, se respeta.
BUSCAR_ESTUDIANTE_SIN_NOTAS = [
    "if (!pm.environment.get('id_estudiante_sin_notas')) {",
    "  const base = pm.environment.get('base_url');",
    "  const auth = [{ key: 'Authorization', value: 'Bearer ' + pm.collectionVariables.get('token_admin') }];",
    "  pm.sendRequest({ url: base + '/estudiantes?limit=500', header: auth }, (err, res) => {",
    "    if (err || res.code !== 200) return;",
    "    const ids = res.json().map(e => e.id_estudiante).sort((a, b) => b - a).slice(0, 30);",
    "    const probar = (i) => {",
    "      if (i >= ids.length) return;",
    "      pm.sendRequest({ url: base + '/estudiantes/' + ids[i] + '/notas', header: auth }, (e2, r2) => {",
    "        if (!e2 && r2.code === 200 && r2.json().length === 0) {",
    "          pm.environment.set('id_estudiante_sin_notas', String(ids[i]));",
    "        } else { probar(i + 1); }",
    "      });",
    "    };",
    "    probar(0);",
    "  });",
    "}",
]


def _item(c):
    eventos = [{"listen": "test", "script": _script(_pruebas(c))}]
    if c["id"] == 52:
        eventos.insert(0, {"listen": "prerequest", "script": _script(BUSCAR_ESTUDIANTE_SIN_NOTAS)})
    elif c.get("pre"):
        eventos.insert(0, {"listen": "prerequest", "script": _script(c["pre"])})
    return {"name": f"CP-INT-{c['id']:03d} {c['nombre']}", "event": eventos, "request": _peticion(c)}


def _sesiones():
    prereq = [
        "pm.collectionVariables.set('sufijo', Date.now().toString().slice(-9));",
        "pm.collectionVariables.set('hoy', new Date().toISOString().slice(0, 10));",
        "['dup','dup2','docente','padre','admin_crea','temporal'].forEach((k, i) =>",
        "  pm.collectionVariables.set('doc_' + k, '8' + (Date.now() % 100000000 + i)));",
        "pm.collectionVariables.set('correo_docente_mayus', (pm.environment.get('correo_docente') || '').toUpperCase());",
    ]
    items = []
    for i, (rol, var) in enumerate(LOGINS.items()):
        ev = [f"pm.test('00 Sesión {rol} → 200', () => pm.response.to.have.status(200));",
              f"pm.collectionVariables.set('{TOKENS[rol]}', pm.response.json().access_token);",
              f"pm.collectionVariables.set('refresh_{rol}', pm.response.json().refresh_token);",
              "const p = JSON.parse(atob(pm.response.json().access_token.split('.')[1]));",
              f"pm.collectionVariables.set('id_usuario_{rol}', p.sub);"]
        item = {"name": f"00 Sesión {rol}",
                "event": [{"listen": "test", "script": _script(ev)}],
                "request": {"method": "POST", "header": [{"key": "Content-Type", "value": "application/json"}],
                            "url": {"raw": "{{base_url}}/auth/login", "host": ["{{base_url}}"], "path": ["auth", "login"]},
                            "body": {"mode": "raw", "options": {"raw": {"language": "json"}},
                                     "raw": json.dumps({"correo": "{{" + var + "}}", "password": "{{QA_PASSWORD}}"})}}}
        if i == 0:
            item["event"].insert(0, {"listen": "prerequest", "script": _script(prereq)})
        items.append(item)
    return {"name": "00 Sesiones", "item": items}


def _preparar_cuenta_temporal() -> list[dict]:
    """La cuenta que usan los casos de «Sesión con cuenta temporal», con dos sesiones abiertas."""
    json_h = [{"key": "Content-Type", "value": "application/json"}]
    cuerpo = {"mode": "raw", "options": {"raw": {"language": "json"}}}

    def login(nombre, refresh):
        return {"name": nombre,
                "event": [{"listen": "test", "script": _script([
                    f"pm.test('{nombre} → 200', () => pm.response.to.have.status(200));",
                    "pm.collectionVariables.set('token_temporal', pm.response.json().access_token);",
                    f"pm.collectionVariables.set('{refresh}', pm.response.json().refresh_token);"])}],
                "request": {"method": "POST", "header": json_h,
                            "url": {"raw": "{{base_url}}/auth/login", "host": ["{{base_url}}"],
                                    "path": ["auth", "login"]},
                            "body": {**cuerpo, "raw": json.dumps(LOGIN_TEMPORAL)}}}

    datos = {**cuenta("temporal"), "correo": LOGIN_TEMPORAL["correo"], "id_rol": 2}
    crear = {"name": "T1 Admin crea la cuenta temporal",
             "event": [{"listen": "test", "script": _script([
                 "pm.test('T1 cuenta temporal → 201', () => pm.response.to.have.status(201));",
                 "pm.collectionVariables.set('usuario_temporal_id', pm.response.json().id_usuario);"])}],
             "request": {"method": "POST",
                         "header": json_h + [{"key": "Authorization", "value": "Bearer {{token_admin}}"}],
                         "url": {"raw": "{{base_url}}/usuarios", "host": ["{{base_url}}"], "path": ["usuarios"]},
                         "body": {**cuerpo, "raw": json.dumps(datos, ensure_ascii=False)}}}
    return [crear, login("T2 Sesión 1 de la cuenta temporal", "refresh_temporal_1"),
            login("T3 Sesión 2 de la cuenta temporal", "refresh_temporal_2")]


def _limpieza():
    # Las peticiones de borrado se omiten si la variable quedó vacía (el caso no corrió).
    def borrar(nombre, ruta, rol, var):
        return {"name": nombre,
                "event": [{"listen": "prerequest", "script": _script([f"if (!pm.collectionVariables.get('{var}')) pm.execution.skipRequest();"])}],
                "request": {"method": "DELETE", "header": [{"key": "Authorization", "value": "Bearer {{" + TOKENS[rol] + "}}"}],
                            "url": {"raw": "{{base_url}}" + ruta, "host": ["{{base_url}}"], "path": [s for s in ruta.split("/") if s]}}}
    return {"name": "99 Limpieza", "item": [
        borrar("Borrar novedad de prueba", "/novedades/{{novedad_id}}", "docente", "novedad_id"),
        borrar("Borrar nota de prueba", "/notas/{{nota_id}}", "docente", "nota_id"),
        borrar("Anular entrada de prueba", "/asistencia/{{asistencia_id}}", "admin", "asistencia_id"),
        borrar("Anular salida de prueba", "/asistencia/{{asistencia_salida_id}}", "admin", "asistencia_salida_id"),
        borrar("Borrar usuario creado por el admin", "/usuarios/{{usuario_creado_id}}", "admin", "usuario_creado_id"),
        borrar("Borrar docente registrado", "/usuarios/{{usuario_docente_id}}", "admin", "usuario_docente_id"),
        borrar("Borrar padre registrado", "/usuarios/{{usuario_padre_id}}", "admin", "usuario_padre_id"),
        borrar("Borrar reporte de prueba", "/reportes/{{reporte_id}}", "admin", "reporte_id"),
        borrar("Borrar el teléfono de la cuenta temporal", "/dispositivos/qa-newman-{{sufijo}}-dispositivo", "temporal", "usuario_temporal_id"),
        borrar("Borrar la cuenta temporal", "/usuarios/{{usuario_temporal_id}}", "admin", "usuario_temporal_id"),
    ]}


def construir() -> dict:
    faltan = ids_de_la_planeacion() - {c["id"] for c in CASOS}
    sobran = {c["id"] for c in CASOS} - ids_de_la_planeacion()
    assert not faltan, f"Casos de la planeación sin definir: {sorted(faltan)}"
    assert not sobran, f"Casos que no están en la planeación: {sorted(sobran)}"
    carpetas = [_sesiones()]
    for nombre in ORDEN:
        items = [_item(c) for c in CASOS if c["carpeta"] == nombre]
        if nombre == t:
            items = _preparar_cuenta_temporal() + items
        carpetas.append({"name": nombre, "item": items})
    carpetas.append(_limpieza())
    return {
        "info": {"name": "Eyes School API · integración (PR-05)",
                 "description": "75 casos CP-INT de la API contra QA (los otros 6 de los 81 son de pytest). La contraseña entra con --env-var QA_PASSWORD.",
                 "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
        "item": carpetas,
        "variable": [],
    }


def entorno() -> dict:
    valores = {
        "base_host": "http://localhost:8000", "base_url": "http://localhost:8000/api/v1",
        "correo_admin": "admin@eyesschool.edu.co", "correo_docente": "carlos.jimenez@eyes.edu.co",
        "correo_docente2": "lucia.soto@eyes.edu.co", "correo_estudiante": "juan.perez@student.eyes.co",
        "correo_padre1": "roberto.diaz@gmail.com", "correo_padre2": "rosa.perez@gmail.com",
        "id_estudiante_ds01": "2", "id_estudiante_ds03a": "1", "id_estudiante_ds02_ajeno": "2",
        "id_materia_docente": "1", "id_curso_ds01": "1", "id_profesor_docente": "1",
        "id_padre_ajeno": "1", "id_estudiante_sin_notas": "",
        "id_administrador": "1", "umbral_ms": "800",
    }
    return {"id": "eyes-school-qa", "name": "Eyes School · QA",
            "values": [{"key": k, "value": val, "enabled": True} for k, val in valores.items()],
            "_postman_variable_scope": "environment"}


if __name__ == "__main__":
    (AQUI / "eyes_school_api.postman_collection.json").write_text(
        json.dumps(construir(), ensure_ascii=False, indent=2), encoding="utf-8")
    (AQUI / "qa.postman_environment.json").write_text(
        json.dumps(entorno(), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(CASOS)} casos generados")
