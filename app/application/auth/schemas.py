from pydantic import BaseModel, EmailStr, field_validator
from app.application.usuarios.schemas import UsuarioCreate

class LoginRequest(BaseModel):
    correo: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    correo: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


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


class RegisterRequest(UsuarioCreate):
    # Campos para Administrador
    cargo: str | None = None
    
    # Campos para Estudiante
    id_curso_actual: int | None = None
    
    # Campos para Padre
    id_estudiante_vinculado: int | None = None
    parentesco: str | None = None
    
    # Campos para Profesor
    titulo: str | None = None
    nivel_estudios: str | None = None
    id_especializacion: int | None = None
    institucion: str | None = None
