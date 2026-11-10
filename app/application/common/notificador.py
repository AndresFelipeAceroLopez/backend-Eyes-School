"""Puerto para enviar notificaciones push.

La lógica de negocio depende solo de esta interfaz; la implementación real (Firebase) vive
en `app/infrastructure/notificador_firebase.py` y en las pruebas se reemplaza por un doble.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Notificador(ABC):
    @abstractmethod
    async def enviar(
        self, tokens: list[str], titulo: str, cuerpo: str, datos: dict[str, str] | None = None
    ) -> None:
        """Envía una notificación a los dispositivos con esos tokens FCM."""


class NotificadorNulo(Notificador):
    """No envía nada (sin credenciales de Firebase configuradas): solo deja constancia."""

    async def enviar(
        self, tokens: list[str], titulo: str, cuerpo: str, datos: dict[str, str] | None = None
    ) -> None:
        logger.warning(
            "FIREBASE_CREDENTIALS_JSON no configurada; no se enviaron %d notificaciones", len(tokens)
        )
