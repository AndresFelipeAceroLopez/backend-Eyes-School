import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"


async def send_email(to: str, subject: str, html: str) -> bool:
    """Envía un correo vía la API HTTP de Resend.

    Devuelve True si se envió, False si no hay API key configurada o falló el envío.
    No lanza excepciones: el llamador no debe romper su flujo por un fallo de correo.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY no configurada; no se envió correo a %s", to)
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                RESEND_ENDPOINT,
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={"from": settings.MAIL_FROM, "to": [to], "subject": subject, "html": html},
            )
        resp.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001 — el correo es best-effort
        logger.error("Error enviando correo a %s: %s", to, exc)
        return False


def build_reset_email_html(nombre: str, reset_url: str) -> str:
    saludo = f"Hola {nombre}," if nombre else "Hola,"
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; color: #1e293b;">
      <h2 style="color: #2563eb;">Restablece tu contraseña</h2>
      <p>{saludo}</p>
      <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en EyeSchool.
         Haz clic en el botón para crear una nueva contraseña:</p>
      <p style="text-align: center; margin: 28px 0;">
        <a href="{reset_url}"
           style="background: #2563eb; color: #fff; padding: 12px 24px; border-radius: 10px;
                  text-decoration: none; font-weight: bold; display: inline-block;">
          Restablecer contraseña
        </a>
      </p>
      <p style="font-size: 12px; color: #64748b;">
        Si el botón no funciona, copia y pega este enlace en tu navegador:<br/>
        <a href="{reset_url}">{reset_url}</a>
      </p>
      <p style="font-size: 12px; color: #64748b;">
        El enlace expira en {settings.RESET_TOKEN_EXPIRE_MINUTES} minutos. Si no solicitaste esto, ignora este correo.
      </p>
    </div>
    """
