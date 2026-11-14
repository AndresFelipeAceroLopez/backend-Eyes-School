"""Hora actual inyectable: los servicios reciben un `Reloj` para que las pruebas lo controlen."""

from collections.abc import Callable
from datetime import datetime, timezone

Reloj = Callable[[], datetime]


def ahora_utc() -> datetime:
    """Hora UTC sin zona horaria (las columnas `timestamp` de la base son naive)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
