"""Corre `restaurar_qa_2026-11-13.sql` contra la base de QA desde la consola SSH de Azure.

En `apieyeschool-q` no hay `psql`, y Render solo acepta conexiones desde Azure, así que se corre
con Python usando la misma `DATABASE_URL` que tiene la app:

    python -m scripts.qa.restaurar_qa --base <nombre-de-la-base-de-QA>

Dos protecciones, porque el 14/11 este script se corrió primero en la consola de PRODUCCIÓN
(base `eyesschool_wru2`) creyendo que era la de QA; el guardia del SQL lo detuvo:
1. En Azure, la Web App tiene que ser `apieyeschool-q` (variable `WEBSITE_SITE_NAME`).
2. La base conectada tiene que ser la que se pasa en `--base`; el SQL lo vuelve a comprobar.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import asyncpg

from app.core.config import settings

WEB_APP_DE_QA = "apieyeschool-q"
SQL = Path(__file__).with_name("restaurar_qa_2026-11-13.sql")
# Render exige TLS; una base local de pruebas no lo tiene.
SSL = "disable" if "127.0.0.1" in settings.DATABASE_URL or "localhost" in settings.DATABASE_URL else "require"


async def main(base: str) -> int:
    sitio = os.environ.get("WEBSITE_SITE_NAME")
    if sitio is not None and sitio.lower() != WEB_APP_DE_QA:
        print(f"Esto no es la Web App de QA ({sitio}). No se toca nada.")
        return 1

    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").split("?")[0]
    conexion = await asyncpg.connect(dsn, ssl=SSL)
    try:
        actual = await conexion.fetchval("SELECT current_database()")
        servidor = urlparse(dsn).hostname
        print(f"Web App: {sitio or '(local)'} · servidor: {servidor}")
        print(f"Base conectada: {actual} · base declarada: {base}")
        if actual != base:
            print("La base conectada no es la declarada. No se toca nada.")
            return 1
        await conexion.execute("SELECT set_config('eyes.base_qa', $1, false)", base)
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
        return 0
    finally:
        await conexion.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restaura los datos de QA del 13/11/2026")
    parser.add_argument("--base", required=True, help="Nombre de la base de QA")
    sys.exit(asyncio.run(main(parser.parse_args().base)))
