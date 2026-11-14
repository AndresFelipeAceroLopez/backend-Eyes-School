"""BC-09 · Prueba de humo de producción después de desplegar v1.1.0.

    python -m scripts.qa.humo_produccion

Solo lectura, salvo el bloqueo por intentos (BE-16): para no bloquear a nadie real, se registra
una cuenta TEMPORAL de padre (sin vínculo con ningún estudiante), se le hacen 6 intentos fallidos y se borra al final con el token
del administrador de producción, que se pide sin mostrarlo.

Comprueba lo que a producción le faltaba antes de este despliegue:
- `/docs` 200 y `/openapi.json` con `/padres/me/hijos` (padre con varios hijos, APP-03/APP-08).
- `/cursos/` 200 y correo inexistente 401.
- La cabecera `X-Content-Type-Options: nosniff` (CP-NF-003).
- 6 intentos fallidos → 429 (BE-16).

Escribe `evidencias/PR-06/api/BC09_humo_produccion.txt`. Sale con 0 solo si todo pasa.

Sin consola (CI, agentes): `PROD_ADMIN_CORREO` y `PROD_ADMIN_PASSWORD` por variable de entorno. Si
no están y no hay consola, la prueba del bloqueo NO se hace (no se crea la cuenta temporal que
después no se podría borrar) y queda anotada como pendiente.
"""

import getpass
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

PRODUCCION = "https://api-eyesschool-hrf2gsg7hyf9dacq.westus3-01.azurewebsites.net"
API = f"{PRODUCCION}/api/v1"
SALIDA = Path("evidencias/PR-06/api/BC09_humo_produccion.txt")


def _pedir(metodo, url, cuerpo=None, token=None):
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(url, data=datos, method=metodo, headers=cabeceras)
    try:
        with urllib.request.urlopen(peticion, timeout=90) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()


def main() -> int:
    filas: list[tuple[str, bool, str]] = []

    def anotar(prueba, ok, detalle):
        filas.append((prueba, ok, detalle))

    codigo, _, _ = _pedir("GET", f"{PRODUCCION}/docs")
    anotar("GET /docs → 200", codigo == 200, str(codigo))

    codigo, _, cuerpo = _pedir("GET", f"{PRODUCCION}/openapi.json")
    rutas = json.loads(cuerpo).get("paths", {}) if codigo == 200 else {}
    anotar("openapi.json incluye /padres/me/hijos", "/api/v1/padres/me/hijos" in rutas, str(codigo))

    codigo, cabeceras, _ = _pedir("GET", f"{API}/cursos")
    anotar("GET /cursos → 200", codigo == 200, str(codigo))
    nosniff = {k.lower(): v for k, v in cabeceras.items()}.get("x-content-type-options")
    anotar("X-Content-Type-Options: nosniff", nosniff == "nosniff", str(nosniff))

    codigo, _, _ = _pedir("POST", f"{API}/auth/login",
                          {"correo": "no.existe.humo@example.com", "password": "NoExiste#2026"})
    anotar("Login con correo inexistente → 401", codigo == 401, str(codigo))

    # BE-16 con una cuenta temporal. Primero las credenciales del admin: sin ellas la cuenta no se
    # podría borrar, así que ni se crea.
    admin = os.environ.get("PROD_ADMIN_CORREO")
    password = os.environ.get("PROD_ADMIN_PASSWORD")
    if not (admin and password) and sys.stdin.isatty():
        admin = input("Correo del administrador de producción: ").strip()
        password = getpass.getpass("Contraseña del administrador (no se muestra): ")
    if not (admin and password):
        anotar("Bloqueo tras 6 intentos (BE-16): PENDIENTE, sin credenciales de admin", False, "-")
        return _escribir(filas)
    codigo, _, cuerpo = _pedir("POST", f"{API}/auth/login", {"correo": admin, "password": password})
    token = json.loads(cuerpo).get("access_token") if codigo == 200 else None
    anotar("Login del administrador de producción", token is not None, str(codigo))
    if not token:
        return _escribir(filas)

    correo = f"qa.humo.{uuid.uuid4().hex[:8]}@example.com"
    clave = f"Humo#{uuid.uuid4().hex[:10]}A1"
    codigo, _, cuerpo = _pedir("POST", f"{API}/auth/register", {
        "tipo_documento": "CC", "numero_documento": str(uuid.uuid4().int)[:10],
        "primer_nombre": "Qa", "primer_apellido": "Humo", "correo": correo,
        "password": clave, "id_rol": 4,  # padre sin vínculo: no crea perfil ni toca datos
    })
    id_temporal = json.loads(cuerpo).get("id_usuario") if codigo == 201 else None
    anotar("Cuenta temporal creada", codigo == 201, str(codigo))
    if id_temporal:
        for _ in range(5):
            _pedir("POST", f"{API}/auth/login", {"correo": correo, "password": "Incorrecta#1"})
        codigo, _, _ = _pedir("POST", f"{API}/auth/login", {"correo": correo, "password": clave})
        anotar("6.º intento con la clave correcta tras 5 fallos → 429", codigo == 429, str(codigo))

        borrado = _pedir("DELETE", f"{API}/usuarios/{id_temporal}", token=token)[0]
        anotar("Cuenta temporal borrada", borrado == 204, str(borrado))
    return _escribir(filas)


def _escribir(filas) -> int:
    lineas = [
        "BC-09 · Prueba de humo de producción",
        f"Fecha (UTC): {datetime.now(timezone.utc):%Y-%m-%d %H:%M}",
        f"API: {PRODUCCION}",
        "",
        *[f"  {'OK ' if ok else 'MAL'} {prueba} ({detalle})" for prueba, ok, detalle in filas],
        "",
        "RESULTADO: " + ("humo en verde" if all(ok for _, ok, _ in filas) else "HAY FALLOS"),
    ]
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    print(f"\nEvidencia: {SALIDA}")
    return 0 if all(ok for _, ok, _ in filas) else 1


if __name__ == "__main__":
    sys.exit(main())
