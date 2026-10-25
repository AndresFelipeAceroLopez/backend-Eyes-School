"""Tokens y contraseñas: la base de toda la autorización de la API."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    JWTError,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_la_contrasena_se_guarda_con_hash_y_se_verifica():
    hashed = hash_password("clave-segura")

    assert hashed != "clave-segura"
    assert hashed.startswith("$2")
    assert verify_password("clave-segura", hashed)
    assert not verify_password("otra-clave", hashed)


def test_cada_tipo_de_token_lleva_su_tipo():
    access = decode_token(create_access_token({"sub": "7", "idRol": 2, "rol": "estudiante"}))
    refresh_token, jti = create_refresh_token({"sub": "7"})
    refresh = decode_token(refresh_token)
    reset = decode_token(create_password_reset_token(7))

    assert access["type"] == "access"
    assert access["rol"] == "estudiante"
    assert refresh["type"] == "refresh"
    assert refresh["jti"] == jti
    assert reset == {**reset, "type": "reset", "sub": "7"}


def test_un_token_alterado_se_rechaza():
    token = create_access_token({"sub": "1", "idRol": 3, "rol": "admin"})
    header, payload, signature = token.split(".")
    forged = f"{header}.{payload}.{signature[:-2]}xx"

    with pytest.raises(JWTError):
        decode_token(forged)


def test_un_token_firmado_con_otra_clave_se_rechaza():
    token = jwt.encode(
        {"sub": "1", "rol": "admin", "type": "access"}, "otra-clave-de-al-menos-32-bytes!!", "HS256"
    )

    with pytest.raises(JWTError):
        decode_token(token)


def test_un_token_vencido_se_rechaza():
    expired = jwt.encode(
        {"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.SECRET_KEY,
        settings.ALGORITHM,
    )

    with pytest.raises(JWTError):
        decode_token(expired)
