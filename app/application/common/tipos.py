"""Tipos compartidos por los esquemas Pydantic."""

import re
from datetime import date, datetime, time, timezone
from typing import Annotated

import annotated_types
from pydantic import AfterValidator, BeforeValidator, WithJsonSchema


def _como_utc(valor: datetime) -> datetime:
    # Las columnas `timestamp` de la base son naive y guardan UTC (ver core/reloj.py).
    return valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)


# Fecha y hora de los esquemas `Out`: sale como `2026-11-03T03:03:37+00:00`. Sin la zona no es
# un `date-time` válido de OpenAPI (RFC 3339) y schemathesis lo marcaba como ST108 (BC-07).
FechaHoraUTC = Annotated[datetime, AfterValidator(_como_utc)]


_FECHA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _solo_iso(valor):
    # Pydantic acepta por defecto un número como fecha (segundos desde 1970): `?fecha=0` era
    # 1970-01-01 y la API respondía 200 con una lista vacía (schemathesis ST201, BC-07).
    if isinstance(valor, str) and not _FECHA_ISO.match(valor):
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD")
    return valor


# Fecha recibida en la query o en el cuerpo: solo `AAAA-MM-DD`, como declara el contrato.
FechaISO = Annotated[date, BeforeValidator(_solo_iso)]


# Rango de `integer` de PostgreSQL, que es el tipo de todos los ids. Declararlo en el parámetro
# hace que FastAPI rechace el valor con 422 ANTES de consultar la base, y que el contrato OpenAPI
# lo publique (`minimum`/`maximum`). Sin esto, `?id_estudiante=9223372036854775808` llegaba a la
# consulta (DEF-039) y el contrato decía que era un valor válido (schemathesis ST202, BC-07).
ENTERO32_MAX = 2**31 - 1
Entero32 = Annotated[int, annotated_types.Interval(ge=-(2**31), le=ENTERO32_MAX)]


# Hora de clase del colegio: es hora LOCAL (America/Bogota) y no lleva zona a propósito. El formato
# `time` de OpenAPI es el `full-time` de RFC 3339, que exige zona, así que `"07:00:00"` no lo
# cumplía (schemathesis ST108, BC-07). Añadir "Z" sería falso: las 07:00 son las 07:00 del
# colegio, no de Greenwich. Se documenta como lo que es: una hora local con su patrón.
HoraLocal = Annotated[
    time,
    WithJsonSchema({
        "type": "string",
        "pattern": r"^\d{2}:\d{2}(:\d{2}(\.\d+)?)?$",
        "description": "Hora local del colegio (America/Bogota), sin zona horaria",
        "examples": ["07:00:00"],
    }),
]
