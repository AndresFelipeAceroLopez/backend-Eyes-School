from datetime import datetime, timezone

from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.schemas import AccessTokenResponse, LoginRequest, MeResponse, TokenResponse
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

REFRESH_PREFIX = "refresh:"


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis):
        self.repo = UsuarioRepository(session)
        self.session = session
        self.redis = redis

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.repo.get_by_correo(data.correo)
        if not user or not user.password:
            raise UnauthorizedException("Credenciales inválidas")
        if not verify_password(data.password, user.password):
            raise UnauthorizedException("Credenciales inválidas")
        if not user.estado:
            raise UnauthorizedException("Usuario inactivo")

        payload = {"sub": str(user.id_usuario), "idRol": user.id_rol, "rol": user.rol.nombre_rol}
        access_token = create_access_token(payload)
        refresh_token, jti = create_refresh_token(payload)

        from app.core.config import settings
        ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.redis.setex(f"{REFRESH_PREFIX}{jti}", ttl, str(user.id_usuario))

        user.ultimo_acceso = datetime.now(timezone.utc)
        await self.session.flush()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise UnauthorizedException("Token inválido")
            jti = payload.get("jti")
            stored = await self.redis.get(f"{REFRESH_PREFIX}{jti}")
            if not stored:
                raise UnauthorizedException("Token expirado o revocado")
        except (JWTError, KeyError):
            raise UnauthorizedException("Token inválido")

        new_payload = {"sub": payload["sub"], "idRol": payload["idRol"], "rol": payload["rol"]}
        access_token = create_access_token(new_payload)
        return AccessTokenResponse(access_token=access_token)

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
            jti = payload.get("jti")
            if jti:
                await self.redis.delete(f"{REFRESH_PREFIX}{jti}")
        except JWTError:
            pass

    async def get_me(self, id_usuario: int) -> MeResponse:
        user = await self.repo.get_by_id_with_rol(id_usuario)
        if not user:
            raise UnauthorizedException("Usuario no encontrado")
        return MeResponse(
            id_usuario=user.id_usuario,
            primer_nombre=user.primer_nombre,
            primer_apellido=user.primer_apellido,
            correo=user.correo,
            nombre_rol=user.rol.nombre_rol,
            id_rol=user.id_rol,
            estado=user.estado,
        )
