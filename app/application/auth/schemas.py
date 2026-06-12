from pydantic import BaseModel, EmailStr, field_validator


class LoginRequest(BaseModel):
    correo: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id_usuario: int
    primer_nombre: str
    primer_apellido: str
    correo: str | None
    nombre_rol: str
    id_rol: int
    estado: bool
