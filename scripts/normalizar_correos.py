"""Pasa los correos de `usuario` a minúsculas sin espacios (BE-12).

Antes de crear el índice único sobre `lower(correo)` (migración b7d2e9a41c03) hay que revisar
que no existan dos cuentas cuyo correo solo se diferencie en mayúsculas.

    python -m scripts.normalizar_correos            # solo reporta
    python -m scripts.normalizar_correos --aplicar  # normaliza si no hay choques

Si hay choques no cambia nada: cada uno debe resolverse a mano (fusionar o corregir el correo
de una de las cuentas), porque no se puede decidir automáticamente cuál es la cuenta real.
"""

from __future__ import annotations

import asyncio
import sys
from collections import defaultdict


def normalizar(correo: str) -> str:
    return correo.strip().lower()


def detectar_choques(usuarios: list[tuple[int, str]]) -> dict[str, list[int]]:
    """Agrupa por correo normalizado; devuelve solo los que tienen más de una cuenta."""
    grupos: dict[str, list[int]] = defaultdict(list)
    for id_usuario, correo in usuarios:
        grupos[normalizar(correo)].append(id_usuario)
    return {correo: ids for correo, ids in grupos.items() if len(ids) > 1}


def pendientes_de_normalizar(usuarios: list[tuple[int, str]]) -> list[int]:
    return [i for i, correo in usuarios if correo != normalizar(correo)]


async def main(aplicar: bool) -> int:
    from sqlalchemy import select, update

    from app.core.database import AsyncSessionLocal
    from app.infrastructure.models.usuario import UsuarioModel

    async with AsyncSessionLocal() as session:
        filas = await session.execute(
            select(UsuarioModel.id_usuario, UsuarioModel.correo).where(UsuarioModel.correo.isnot(None))
        )
        usuarios = [(i, c) for i, c in filas.all()]

        choques = detectar_choques(usuarios)
        pendientes = pendientes_de_normalizar(usuarios)
        print(f"{len(usuarios)} usuarios con correo; {len(pendientes)} por normalizar.")
        for correo, ids in choques.items():
            print(f"CHOQUE: {correo} -> usuarios {ids}")

        if choques:
            print("Hay choques: resuélvalos a mano antes de aplicar. No se cambió nada.")
            return 1
        if not aplicar:
            print("Sin choques. Use --aplicar para normalizar.")
            return 0

        for id_usuario in pendientes:
            correo = next(c for i, c in usuarios if i == id_usuario)
            await session.execute(
                update(UsuarioModel)
                .where(UsuarioModel.id_usuario == id_usuario)
                .values(correo=normalizar(correo))
            )
        await session.commit()
        print(f"{len(pendientes)} correos normalizados.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main("--aplicar" in sys.argv)))
