import logging

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-in-production"

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/eyesschool"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = DEFAULT_SECRET_KEY
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"

    # Orígenes del navegador que pueden llamar a la API, separados por coma.
    # "*" acepta cualquiera; en ese caso no se envían credenciales (cookies),
    # que la web y la app no usan: se autentican con el encabezado Bearer.
    CORS_ORIGINS: str = "*"

    # Recuperación de contraseña / envío de correo (Resend).
    RESEND_API_KEY: str = ""
    MAIL_FROM: str = "EyeSchool <onboarding@resend.dev>"
    FRONTEND_URL: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> list[str]:
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
