"""BC-01 · Verifica la rotación de la contraseña de la base (DEF-001, issue #22).

Lo corre quien rotó la contraseña, DESPUÉS de cambiarla en Render y en las dos Web Apps:

    python -m scripts.qa.verificar_rotacion --quien "Andrés Acero"

Pide la URL VIEJA de la base sin mostrarla (la que estaba en el `.env` filtrado) y comprueba:

1. Que con ella la conexión se RECHAZA (`password authentication failed`).
2. El preflight de producción y de QA: `/docs` 200, `/cursos/` 200, correo inexistente 401 y,
   si se define `QA_PASSWORD`, login del admin en QA 200.

Escribe `evidencias/PR-03/api/BC01_rotacion.txt` con la fecha, quién rotó y los códigos HTTP. En
el archivo nunca queda la contraseña ni la URL: solo el host y el nombre de la base.

Sale con código 0 solo si todo da lo esperado.
"""

import argparse
import asyncio
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ENTORNOS = {
    "producción": "https://api-eyesschool-hrf2gsg7hyf9dacq.westus3-01.azurewebsites.net",
    "QA": "https://apieyeschool-q-g4hfgrgvepbecacc.chilecentral-01.azurewebsites.net",
}
SALIDA = Path("evidencias/PR-03/api/BC01_rotacion.txt")


def _http(metodo: str, url: str, cuerpo: dict | None = None) -> int:
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    peticion = urllib.request.Request(
        url, data=datos, method=metodo, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(peticion, timeout=90) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def preflight(nombre: str, base: str, password_qa: str | None) -> list[tuple[str, int, int]]:
    """(prueba, esperado, obtenido) para un entorno."""
    api = f"{base}/api/v1"
    filas = [
        ("GET /docs", 200, _http("GET", f"{base}/docs")),
        ("GET /api/v1/cursos/", 200, _http("GET", f"{api}/cursos/")),
        ("POST /auth/login con correo inexistente", 401, _http(
            "POST", f"{api}/auth/login",
            {"correo": "no.existe.bc01@example.com", "password": "NoExiste#2026"},
        )),
    ]
    if nombre == "QA" and password_qa:
        filas.append(("POST /auth/login del admin", 200, _http(
            "POST", f"{api}/auth/login",
            {"correo": "admin@eyesschool.edu.co", "password": password_qa},
        )))
    return filas


async def probar_url_vieja(url: str) -> str:
    """'rechazada' si la base ya no acepta la contraseña vieja; cualquier otra cosa es fallo."""
    import asyncpg

    dsn = url.replace("postgresql+asyncpg://", "postgresql://").split("?")[0]
    try:
        conexion = await asyncpg.connect(dsn, ssl="require", timeout=30)
    except asyncpg.exceptions.InvalidPasswordError:
        return "rechazada"
    except Exception as e:  # noqa: BLE001 — se informa el tipo, nunca el mensaje (trae la URL)
        return f"error inesperado ({type(e).__name__})"
    await conexion.close()
    return "ACEPTADA"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quien", required=True, help="Quién rotó la contraseña")
    args = parser.parse_args()

    vieja = getpass.getpass("URL VIEJA de la base de producción (no se muestra): ").strip()
    if not vieja:
        print("Sin URL vieja no se puede verificar la rotación.")
        return 2
    destino = urlparse(vieja.replace("+asyncpg", ""))
    resultado_vieja = asyncio.run(probar_url_vieja(vieja))

    lineas = [
        "BC-01 · Verificación de la rotación de la contraseña de la base (DEF-001, #22)",
        f"Fecha (UTC): {datetime.now(timezone.utc):%Y-%m-%d %H:%M}",
        f"Rotó: {args.quien}",
        "",
        f"Contraseña vieja contra {destino.hostname} / {destino.path.lstrip('/')}: "
        f"{resultado_vieja} (esperado: rechazada)",
        "",
    ]
    todo_bien = resultado_vieja == "rechazada"
    for nombre, base in ENTORNOS.items():
        lineas.append(f"Preflight de {nombre} ({urlparse(base).hostname})")
        for prueba, esperado, obtenido in preflight(nombre, base, os.environ.get("QA_PASSWORD")):
            ok = esperado == obtenido
            todo_bien &= ok
            lineas.append(f"  {'OK ' if ok else 'MAL'} {prueba}: {obtenido} (esperado {esperado})")
        lineas.append("")
    lineas.append("RESULTADO: " + ("rotación verificada" if todo_bien else "NO verificada"))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))
    print(f"\nEvidencia: {SALIDA}")
    return 0 if todo_bien else 1


if __name__ == "__main__":
    sys.exit(main())
