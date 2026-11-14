"""Escritura de archivos para los endpoints asíncronos.

`open()` y `write()` bloquean el hilo. Dentro de una función `async` eso congela el bucle de
eventos: mientras se escribe un avatar de 2 MB, **ninguna otra petición avanza**. Con la API ya
rozando su techo de throughput bajo carga (ver el PR-06), bloquear el bucle es justo lo que no
conviene.

Por eso la escritura vive aquí, en una función síncrona normal, y quien la llama la ejecuta en un
hilo aparte con `anyio.to_thread.run_sync`. `anyio` ya viene con FastAPI, así que no agrega
dependencias.

Esto además resuelve el issue `python:S7493` de SonarQube («Async functions should not contain
synchronous file operations»), que marcaba la reliability del proyecto en C.
"""

from __future__ import annotations

import os


def guardar_archivo(ruta: str, contenido: bytes, carpeta: str | None = None) -> None:
    """Escribe `contenido` en `ruta`, creando antes `carpeta` si hace falta.

    Síncrona a propósito: se ejecuta en un hilo con `anyio.to_thread.run_sync`.
    """
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(contenido)
