"""Asigna a los usuarios de QA una contraseña conocida (BE-INF-2).

Los datos de QA se cargan con `seed_data.sql` y `seed_estudiantes_sinteticos.sql`, cuyas
contraseñas ya no deben conocerse ni estar en el repositorio. Este script les pone la de
`QA_PASSWORD` para que el equipo pueda iniciar sesión.

- Solo corre con `ENVIRONMENT=qa`: en cualquier otro entorno (producción incluido) no toca nada.
- `QA_PASSWORD` debe cumplir la política de contraseñas de la API (BE-09).
- Imprime «correo · rol» de cada usuario; nunca la contraseña.

Uso:  ENVIRONMENT=qa QA_PASSWORD='...' python -m scripts.qa_reset_passwords
"""

from __future__ import annotations

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


async def _actualizar_en_base(password_hash: str) -> Reporte:
    from app.core.database import AsyncSessionLocal
    from app.infrastructure.models.usuario import RolModel, UsuarioModel

    async with AsyncSessionLocal() as session:
        await session.execute(update(UsuarioModel).values(password=password_hash))
        filas = await session.execute(
            select(UsuarioModel.correo, RolModel.nombre_rol)
            .join(RolModel, RolModel.id_rol == UsuarioModel.id_rol)
            .order_by(UsuarioModel.id_usuario)
        )
        reporte = [(correo or "(sin correo)", rol) for correo, rol in filas.all()]
        await session.commit()
    return reporte


async def main() -> int:
    from app.core.security import hash_password

    entorno = os.environ.get("ENVIRONMENT", "")
    reporte = await reset_passwords(
        entorno, os.environ.get("QA_PASSWORD"), _actualizar_en_base, hash_password
    )
    if entorno != ENTORNO_PERMITIDO:
        print(f"ENVIRONMENT={entorno!r}: el script solo corre con ENVIRONMENT=qa. No se cambió nada.")
        return 0
    for correo, rol in reporte:
        print(f"{correo} · {rol}")
    print(f"{len(reporte)} usuarios actualizados.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
