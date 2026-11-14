"""Recorta el openapi.json de un entorno a sus operaciones GET, para schemathesis.

    python -m scripts.qa.openapi_solo_lectura <url-del-entorno> <salida.json>
    schemathesis run <salida.json> --url <url-del-entorno> -H "Authorization: Bearer $TOKEN_ADMIN" --checks all

Por qué un archivo y no los filtros de la CLI: el 13/11/2026 una corrida con `--include-method GET`
y `--include-path-regex` seleccionó también 11 operaciones de escritura (schemathesis combina esos
filtros con OR) y alteró datos de QA con el token de administrador. Con un contrato que solo tiene
GET es imposible que mande un POST, PUT, PATCH o DELETE.
"""

import json
import sys
import urllib.request


def recortar(esquema: dict) -> dict:
    esquema["paths"] = {
        ruta: {"get": operaciones["get"]}
        for ruta, operaciones in esquema.get("paths", {}).items()
        if "get" in operaciones
    }
    return esquema


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    base, salida = sys.argv[1].rstrip("/"), sys.argv[2]
    with urllib.request.urlopen(f"{base}/openapi.json", timeout=60) as respuesta:
        esquema = recortar(json.load(respuesta))
    with open(salida, "w", encoding="utf-8") as archivo:
        json.dump(esquema, archivo)
    metodos = {m for operaciones in esquema["paths"].values() for m in operaciones}
    print(f"{len(esquema['paths'])} operaciones de lectura en {salida} (métodos: {sorted(metodos)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
