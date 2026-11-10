"""Política de contraseñas de la plataforma.

Son las mismas cinco reglas que aplica la web (`src/lib/utils/password.ts`), de modo que
una contraseña válida en un cliente lo sea también en la API.
"""

import re

MIN_LONGITUD = 8

REGLAS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("mayúscula", re.compile(r"[A-Z]")),
    ("minúscula", re.compile(r"[a-z]")),
    ("número", re.compile(r"\d")),
    ("carácter especial", re.compile(r"[^A-Za-z0-9]")),
)


def validar_password(pwd: str) -> list[str]:
    """Devuelve las reglas que la contraseña incumple (lista vacía si cumple todas)."""
    fallos: list[str] = []
    if len(pwd) < MIN_LONGITUD:
        fallos.append(f"longitud mínima de {MIN_LONGITUD} caracteres")
    for nombre, patron in REGLAS:
        if not patron.search(pwd):
            fallos.append(nombre)
    return fallos


def exigir_password_valida(pwd: str) -> str:
    """Validador para Pydantic: lanza `ValueError` con las reglas incumplidas."""
    fallos = validar_password(pwd)
    if fallos:
        raise ValueError("La contraseña incumple: " + ", ".join(fallos))
    return pwd
