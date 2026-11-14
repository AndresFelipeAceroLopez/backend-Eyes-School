"""Genera `usuarios_ds02.json` (DS-08): las cuentas de estudiante para las pruebas de carga.

Toma los estudiantes de la API de QA con un token de administrador y escribe
`[{"correo": ..., "id_estudiante": ...}]` con hasta 50 cuentas. La contraseña no se escribe:
k6 la recibe en QA_PASSWORD (la que fijó scripts/qa_reset_passwords.py).

    python tests/carga/generar_usuarios_ds02.py https://<qa>/api/v1 admin@eyesschool.edu.co
    (pide QA_PASSWORD por variable de entorno)
"""

import json
import os
import sys
from pathlib import Path

import httpx


def main(base: str, correo_admin: str, cantidad: int = 50) -> None:
    password = os.environ["QA_PASSWORD"]
    with httpx.Client(base_url=base, timeout=30) as api:
        token = api.post("/auth/login", json={"correo": correo_admin, "password": password})
        token.raise_for_status()
        headers = {"Authorization": f"Bearer {token.json()['access_token']}"}

        estudiantes = api.get("/estudiantes", params={"limit": 500}, headers=headers).json()
        usuarios = {u["id_usuario"]: u for u in api.get(
            "/usuarios", params={"id_rol": 2, "limit": 500}, headers=headers).json()}

    cuentas = [
        {"correo": usuarios[e["id_usuario"]]["correo"], "id_estudiante": e["id_estudiante"]}
        for e in estudiantes if e["id_usuario"] in usuarios and usuarios[e["id_usuario"]]["correo"]
    ][:cantidad]
    destino = Path(__file__).with_name("usuarios_ds02.json")
    destino.write_text(json.dumps(cuentas, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(cuentas)} cuentas escritas en {destino.name}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
