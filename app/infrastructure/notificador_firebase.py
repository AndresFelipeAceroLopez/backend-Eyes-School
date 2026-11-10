import asyncio
import json
import logging
from functools import lru_cache

from app.application.common.notificador import Notificador, NotificadorNulo
from app.core.config import settings

logger = logging.getLogger(__name__)

# FCM acepta como máximo 500 mensajes por lote.
_LOTE_FCM = 500


class NotificadorFirebase(Notificador):
    """Envía push con Firebase Cloud Messaging (firebase-admin)."""

    def __init__(self, credenciales_json: str):
        import firebase_admin
        from firebase_admin import credentials

        try:
            self._app = firebase_admin.get_app()
        except ValueError:
            self._app = firebase_admin.initialize_app(
                credentials.Certificate(json.loads(credenciales_json))
            )

    async def enviar(
        self, tokens: list[str], titulo: str, cuerpo: str, datos: dict[str, str] | None = None
    ) -> None:
        from firebase_admin import messaging

        for i in range(0, len(tokens), _LOTE_FCM):
            lote = tokens[i : i + _LOTE_FCM]
            mensaje = messaging.MulticastMessage(
                tokens=lote,
                notification=messaging.Notification(title=titulo, body=cuerpo),
                data=datos or {},
            )
            # El SDK de Firebase es síncrono: se saca del bucle de eventos.
            respuesta = await asyncio.to_thread(
                messaging.send_each_for_multicast, mensaje, app=self._app
            )
            if respuesta.failure_count:
                logger.warning(
                    "FCM: %d de %d notificaciones fallaron", respuesta.failure_count, len(lote)
                )


@lru_cache
def get_notificador() -> Notificador:
    """Dependencia de FastAPI: Firebase si hay credenciales, si no un notificador que no envía."""
    if not settings.FIREBASE_CREDENTIALS_JSON:
        return NotificadorNulo()
    return NotificadorFirebase(settings.FIREBASE_CREDENTIALS_JSON)
