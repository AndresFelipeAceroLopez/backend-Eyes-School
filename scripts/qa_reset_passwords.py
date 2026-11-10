"""Asigna a los usuarios de QA una contraseña conocida (BE-INF-2).

Los datos de QA se cargan con `seed_data.sql` y `seed_estudiantes_sinteticos.sql`, cuyas
contraseñas ya no deben conocerse ni estar en el repositorio. Este script les pone la de
`QA_PASSWORD` para que el equipo pueda iniciar sesión.

Cambia la contraseña de TODOS los usuarios de la base a la que se conecte, sin filtro. Por eso
tiene cuatro protecciones independientes (BE-INF-2), y ninguna sobra:

1. `ENVIRONMENT=qa`. Es la más débil: mira una variable, no la base.
2. `DATABASE_URL` tiene que venir del entorno del proceso. Si no está, el script termina. No se
   permite que caiga al `.env`, porque el `.env` de este repositorio apunta a **producción**.
3. `--base <nombre>` obligatorio, que se compara con `SELECT current_database()` ya conectado.
   Esta es la única protección que mira la base de verdad: producción y QA viven en el mismo
   Render, así que el host no distingue y `ENVIRONMENT` tampoco.
4. Antes de escribir imprime la base y cuántos usuarios va a cambiar.

Además: `QA_PASSWORD` debe cumplir la política de contraseñas de la API (BE-09), todo ocurre en
una transacción, y se imprime «correo · rol» de cada usuario, nunca la contraseña.

Uso:
    # PowerShell, con el .env de producción FUERA de la carpeta:
    $env:ENVIRONMENT='qa'; $env:DATABASE_URL=Read-Host 'URL de qaeyesschool'
    $env:QA_PASSWORD=Read-Host 'QA_PASSWORD'
    python -m scripts.qa_reset_passwords --base qaeyesschool
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from collections.abc import Awaitable, Callable

from sqlalchemy import select, update

ENTORNO_PERMITIDO = "qa"

# (correo, rol) de cada usuario actualizado
Reporte = list[tuple[str, str]]


async def reset_passwords(
    entorno: str,
    password: str | None,
    actualizar: Callable[[str], Awaitable[Reporte]],
    hash_fn: Callable[[str], str],
) -> Reporte:
    """Aplica la contraseña de QA solo si `entorno` es «qa».

    `actualizar` recibe el hash y devuelve el reporte; se inyecta para poder probar la
    decisión (¿se ejecuta o no?) sin base de datos.
    """
    if entorno != ENTORNO_PERMITIDO:
        return []
    if not password:
        raise SystemExit("Falta QA_PASSWORD.")

    from app.core.password_policy import validar_password

    fallos = validar_password(password)
    if fallos:
        raise SystemExit("QA_PASSWORD no cumple la política de contraseñas: " + ", ".join(fallos))
    return await actualizar(hash_fn(password))


def exigir_database_url_del_entorno() -> None:
    """Protección 2: `DATABASE_URL` tiene que venir del entorno, no del `.env`.

    `pydantic-settings` lee el `.env` cuando la variable no está en el proceso, y el `.env` de
    este repositorio apunta a producción. Se comprueba antes de importar la configuración de la
    app, porque ese import ya crea el motor de conexión.
    """
    if not os.environ.get("DATABASE_URL"):
        raise SystemExit(
            "Falta DATABASE_URL en el entorno. Fíjela en la terminal apuntando a la base de QA; "
            "este script no la toma del .env, que apunta a producción."
        )


def verificar_base(base_conectada: str, base_esperada: str) -> None:
    """Protección 3: la base realmente conectada tiene que ser la que se declaró en `--base`.

    Es la única comprobación que mira la base y no una variable. Producción y QA están en el
    mismo Render: el host no las distingue, el nombre sí.
    """
    if base_conectada != base_esperada:
        raise SystemExit(
            f"La base conectada es {base_conectada!r} y se esperaba {base_esperada!r}. "
            "No se cambió ninguna contraseña."
        )


async def _actualizar_en_base(password_hash: str, base_esperada: str) -> Reporte:
    from sqlalchemy import func

    from app.core.database import AsyncSessionLocal
    from app.infrastructure.models.usuario import RolModel, UsuarioModel

    async with AsyncSessionLocal() as session:
        base_conectada = await session.scalar(select(func.current_database()))
        verificar_base(base_conectada or "", base_esperada)

        total = await session.scalar(select(func.count()).select_from(UsuarioModel))
        print(f"Base conectada: {base_conectada} · usuarios que se van a cambiar: {total}")

        await session.execute(update(UsuarioModel).values(password=password_hash))
        filas = await session.execute(
            select(UsuarioModel.correo, RolModel.nombre_rol)
            .join(RolModel, RolModel.id_rol == UsuarioModel.id_rol)
            .order_by(UsuarioModel.id_usuario)
        )
        reporte = [(correo or "(sin correo)", rol) for correo, rol in filas.all()]
        await session.commit()
    return reporte


async def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Asigna QA_PASSWORD a los usuarios de QA.")
    parser.add_argument(
        "--base",
        required=True,
        help="Nombre de la base esperada (por ejemplo: qaeyesschool). Se compara con "
        "current_database() una vez conectado.",
    )
    args = parser.parse_args(argv)

    entorno = os.environ.get("ENVIRONMENT", "")
    if entorno != ENTORNO_PERMITIDO:
        print(f"ENVIRONMENT={entorno!r}: el script solo corre con ENVIRONMENT=qa. No se cambió nada.")
        return 0

    exigir_database_url_del_entorno()

    from app.core.security import hash_password

    async def actualizar(password_hash: str) -> Reporte:
        return await _actualizar_en_base(password_hash, args.base)

    reporte = await reset_passwords(
        entorno, os.environ.get("QA_PASSWORD"), actualizar, hash_password
    )
    for correo, rol in reporte:
        print(f"{correo} · {rol}")
    print(f"{len(reporte)} usuarios actualizados.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
