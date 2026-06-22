from datetime import datetime, timezone

from jose import JWTError
from fastapi import UploadFile
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
import os
import uuid

from app.application.auth.schemas import AccessTokenResponse, LoginRequest, MeResponse, TokenResponse
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.application.usuarios.service import UsuarioService
from app.application.usuarios.schemas import UsuarioCreate, UsuarioOut
from app.application.auth.schemas import RegisterRequest
from app.infrastructure.repositories.actores_repository import AdministradorRepository, EstudianteRepository, PadreRepository, ProfesorRepository
from app.infrastructure.repositories.academico_repository import ProfesorEspecializacionRepository

REFRESH_PREFIX = "refresh:"


class AuthService:
    def __init__(self, session: AsyncSession, redis: Redis | None = None):
        self.repo = UsuarioRepository(session)
        self.session = session
        self.redis = redis

    async def register(self, data: RegisterRequest) -> UsuarioOut:
        user_service = UsuarioService(self.session)
        user_data = UsuarioCreate.model_validate(data.model_dump())
        user_out = await user_service.create(user_data)
        
        rol_nombre = user_out.rol.nombre_rol.lower() if user_out.rol else ""
        from datetime import date
        
        if rol_nombre == "estudiante":
            est_repo = EstudianteRepository(self.session)
            await est_repo.create({
                "id_usuario": user_out.id_usuario,
                "codigo_estudiante": data.numero_documento,
                "fecha_ingreso": date.today(),
                "id_curso_actual": data.id_curso_actual
            })
        elif rol_nombre == "profesor":
            prof_repo = ProfesorRepository(self.session)
            prof = await prof_repo.create({
                "id_usuario": user_out.id_usuario,
                "codigo_profesor": data.numero_documento,
                "titulo": data.titulo or "N/A",
                "nivel_estudios": data.nivel_estudios or "N/A",
                "fecha_vinculacion": date.today()
            })
            if data.id_especializacion and data.institucion:
                espec_repo = ProfesorEspecializacionRepository(self.session)
                await espec_repo.create({
                    "id_profesor": prof.id_profesor,
                    "id_especializacion": data.id_especializacion,
                    "institucion": data.institucion
                })
        elif rol_nombre == "padre":
            if data.id_estudiante_vinculado and data.parentesco:
                padre_repo = PadreRepository(self.session)
                await padre_repo.create({
                    "id_usuario": user_out.id_usuario,
                    "id_estudiante": data.id_estudiante_vinculado,
                    "parentesco": data.parentesco,
                    "ocupacion": None
                })
        elif rol_nombre == "administrador":
            admin_repo = AdministradorRepository(self.session)
            await admin_repo.create({
                "id_usuario": user_out.id_usuario,
                "cargo": data.cargo or "Administrador",
                "fecha_asignacion": date.today()
            })
            
        await self.session.commit()
        return user_out

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

        try:
            from app.core.config import settings
            ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
            await self.redis.setex(f"{REFRESH_PREFIX}{jti}", ttl, str(user.id_usuario))
        except Exception:
            pass  # Redis unavailable — refresh token revocation disabled

        user.ultimo_acceso = datetime.now(timezone.utc).replace(tzinfo=None)
        await self.session.flush()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise UnauthorizedException("Token inválido")
            jti = payload.get("jti")
            try:
                stored = await self.redis.get(f"{REFRESH_PREFIX}{jti}")
                if not stored:
                    raise UnauthorizedException("Token expirado o revocado")
            except UnauthorizedException:
                raise
            except Exception:
                pass  # Redis unavailable — skip revocation check
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
                try:
                    await self.redis.delete(f"{REFRESH_PREFIX}{jti}")
                except Exception:
                    pass  # Redis unavailable
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

    async def upload_avatar(self, id_usuario: int, file: UploadFile) -> str:
        user = await self.repo.get_by_id_with_rol(id_usuario)
        if not user:
            raise UnauthorizedException("Usuario no encontrado")
            
        if not file.content_type.startswith("image/"):
            from app.core.exceptions import ConflictException
            raise ConflictException("El archivo debe ser una imagen")
            
        ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join("static/avatars", filename)
        
        with open(filepath, "wb") as f:
            f.write(await file.read())
            
        await self.repo.update(user, {"foto_perfil": f"/static/avatars/{filename}"})
        return f"/static/avatars/{filename}"
