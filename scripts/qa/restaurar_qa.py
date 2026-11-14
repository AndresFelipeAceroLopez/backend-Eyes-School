"""Corre `restaurar_qa_2026-11-13.sql` contra la base de QA desde la consola SSH de Azure.

En `apieyeschool-q` no hay `psql`, y Render solo acepta conexiones desde Azure, así que se corre
con Python usando la misma `DATABASE_URL` que tiene la app:

    python -m scripts.qa.restaurar_qa

El SQL se niega a correr si la base no es `qaeyesschool` y es idempotente.
"""

import asyncio
from pathlib import Path

import asyncpg

from app.core.config import settings

# Render exige TLS; una base local de pruebas no lo tiene.
SSL = "disable" if "127.0.0.1" in settings.DATABASE_URL or "localhost" in settings.DATABASE_URL else "require"
SQL = Path(__file__).with_name("restaurar_qa_2026-11-13.sql")


async def main() -> None:
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").split("?")[0]
    conexion = await asyncpg.connect(dsn, ssl=SSL)
    try:
        print("Base:", await conexion.fetchval("SELECT current_database()"))
        await conexion.execute(SQL.read_text(encoding="utf-8"))
        activas = await conexion.fetchval(
            "SELECT count(*) FROM public.especializaciones WHERE activo"
        )
        novedades = await conexion.fetchval(
            'SELECT array_agg("idNovedad" ORDER BY "idNovedad") FROM public.novedades '
            'WHERE "idNovedad" <= 10'
        )
        print(f"Especializaciones activas: {activas} (esperado 10)")
        print(f"Novedades 1 a 10: {novedades}")
    finally:
        await conexion.close()


if __name__ == "__main__":
    asyncio.run(main())
