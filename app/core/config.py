from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/eyesschool"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"

    # Recuperación de contraseña / envío de correo (Resend).
    RESEND_API_KEY: str = ""
    MAIL_FROM: str = "EyeSchool <onboarding@resend.dev>"
    FRONTEND_URL: str = "http://localhost:3000"


settings = Settings()
