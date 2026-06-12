from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.redis import get_redis
from app.core.security import decode_token

security = HTTPBearer()

DbSession = Annotated[AsyncSession, Depends(get_db)]
RedisClient = Annotated[Redis, Depends(get_redis)]


class CurrentUser:
    def __init__(self, id_usuario: int, id_rol: int, nombre_rol: str):
        self.id_usuario = id_usuario
        self.id_rol = id_rol
        self.nombre_rol = nombre_rol


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    redis: RedisClient,
) -> CurrentUser:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise UnauthorizedException("Token inválido")
        return CurrentUser(
            id_usuario=int(payload["sub"]),
            id_rol=int(payload["idRol"]),
            nombre_rol=payload["rol"],
        )
    except (JWTError, KeyError, ValueError):
        raise UnauthorizedException("Token inválido o expirado")


AuthUser = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: str):
    def dependency(current_user: AuthUser) -> CurrentUser:
        if current_user.nombre_rol not in roles:
            raise ForbiddenException()
        return current_user

    return Depends(dependency)
