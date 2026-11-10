"""La configuración no debe permitir desplegar con la clave de ejemplo."""

import pytest
from pydantic import ValidationError

from app.core.config import DEFAULT_SECRET_KEY, Settings


def test_produccion_sin_secret_key_no_arranca():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None, SECRET_KEY=DEFAULT_SECRET_KEY, ENVIRONMENT="production")


def test_desarrollo_con_la_clave_por_defecto_solo_avisa(caplog):
    settings = Settings(_env_file=None, SECRET_KEY=DEFAULT_SECRET_KEY, ENVIRONMENT="development")

    assert settings.SECRET_KEY == DEFAULT_SECRET_KEY
    assert "SECRET_KEY" in caplog.text


def test_produccion_con_secret_key_propia_arranca():
    settings = Settings(_env_file=None, SECRET_KEY="una-clave-larga-y-propia", ENVIRONMENT="production")

    assert settings.ENVIRONMENT == "production"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("*", ["*"]),
        ("", ["*"]),
        ("https://eyesschool.app, http://localhost:3000", ["https://eyesschool.app", "http://localhost:3000"]),
    ],
)
def test_cors_origins_se_lee_como_lista(raw, expected):
    assert Settings(_env_file=None, CORS_ORIGINS=raw).cors_origins == expected
