import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-in-production"

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/eyesschool"
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    # Cuántos hash de bcrypt pueden correr a la vez (login, registro, cambio de contraseña).
    # Ver app/core/security.py: más allá de esto esperan turno sin bloquear el resto de la API.
    BCRYPT_CONCURRENCIA: int = 2
    ENVIRONMENT: str = "development"

    # Orígenes del navegador que pueden llamar a la API, separados por coma.
    # "*" acepta cualquiera; en ese caso no se envían credenciales (cookies),
    # que la web y la app no usan: se autentican con el encabezado Bearer.
    CORS_ORIGINS: str = "*"

    # Recuperación de contraseña / envío de correo (Resend).
    RESEND_API_KEY: str = ""
    MAIL_FROM: str = "EyeSchool <onboarding@resend.dev>"
    FRONTEND_URL: str = "http://localhost:3000"

    # Credencial de la cuenta de servicio de Firebase (JSON completo) para las notificaciones
    # push. Vive solo en la configuración de Azure, nunca en el repositorio. Vacía = sin push.
    FIREBASE_CREDENTIALS_JSON: str = ""

    # Bloqueo de inicio de sesión (BE-16): intentos fallidos y minutos de bloqueo.
    # Pool de conexiones a PostgreSQL (DEF-038). Configurables para poder ajustarlos sin tocar
    # el código: el techo de peticiones por segundo de la API es, en la práctica,
    # (DB_POOL_SIZE + DB_MAX_OVERFLOW) dividido por lo que tarde cada consulta. Subirlos solo
    # ayuda si el plan de PostgreSQL admite esas conexiones; si no, las rechaza y empeora.
    # Medido dentro del contenedor de QA el 10/11/2026: abrir una conexión cuesta 1 233 ms
    # (TCP + TLS + autenticación a otro continente) y una consulta sobre una conexión ya abierta,
    # 164 ms. Siete veces más. Por eso el pool se dimensiona al revés de lo habitual: muchas
    # conexiones FIJAS, que se abren una vez y duran, y poco desbordamiento, porque cada conexión
    # de desbordamiento se abre durante el pico y le cobra 1,2 s a la petición que la provocó.
    #
    # TECHO DEL SERVIDOR (13/11/2026). QA y producción comparten UN servidor de Render con
    # 0,1 CPU, 256 MB y un límite de 97 conexiones. Con 30 + 10 por API, las dos podían pedir 80;
    # en una carga de 50 usuarios la base (una décima de núcleo) encola las consultas, las
    # conexiones se acumulan, se llega al límite y TODA conexión nueva falla, en las dos APIs a
    # la vez: es la caída de ~90 s de DEF-038. Más conexiones que CPU no dan velocidad, solo
    # fila. Por eso: 12 fijas y ninguna de desbordamiento → como mucho 24 entre QA y producción.
    # Si se sube el plan de Render, se puede volver a subir esto (y debe sumar < límite − 10).
    DB_POOL_SIZE: int = 12
    DB_MAX_OVERFLOW: int = 0
    # `pool_pre_ping` hace un «SELECT 1» antes de entregar cada conexión. Con la base en otro
    # continente eso cuesta un viaje de ida y vuelta (~200 ms) en CADA petición. Se desactiva y
    # se reciclan las conexiones antes de que el servidor las cierre por inactividad. Si
    # aparecen errores de «connection closed», vuelva a ponerlo en true.
    DB_POOL_PRE_PING: bool = False
    # Reciclar también cuesta 1 233 ms, así que se hace cada media hora y no cada cinco minutos.
    DB_POOL_RECYCLE: int = 1800

    LOGIN_MAX_INTENTOS: int = 5
    LOGIN_BLOQUEO_MINUTOS: int = 15

    @property
    def origenes_cors(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()] or ["*"]

    @model_validator(mode="after")
    def _secret_key_must_be_set(self) -> "Settings":
        # Con la clave por defecto cualquiera puede firmar un token de administrador.
        if self.SECRET_KEY == DEFAULT_SECRET_KEY:
            if self.ENVIRONMENT == "production":
                raise ValueError("SECRET_KEY no está configurada: defínala antes de desplegar.")
            logger.warning("SECRET_KEY usa el valor por defecto; solo es aceptable en desarrollo.")
        return self


settings = Settings()
