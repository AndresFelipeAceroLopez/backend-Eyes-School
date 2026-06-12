from fastapi import APIRouter

from app.application.auth.schemas import AccessTokenResponse, LoginRequest, MeResponse, RefreshRequest, TokenResponse
from app.application.auth.service import AuthService
from app.core.dependencies import AuthUser, DbSession, RedisClient

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: DbSession, redis: RedisClient):
    return await AuthService(db, redis).login(data)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(data: RefreshRequest, db: DbSession, redis: RedisClient):
    return await AuthService(db, redis).refresh(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(data: RefreshRequest, db: DbSession, redis: RedisClient):
    await AuthService(db, redis).logout(data.refresh_token)


@router.get("/me", response_model=MeResponse)
async def me(current_user: AuthUser, db: DbSession, redis: RedisClient):
    return await AuthService(db, redis).get_me(current_user.id_usuario)
