import io
import logging
import os
import uuid
from datetime import date, timedelta

import anyio
from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    TokenResponse,
)
from app.application.common.archivos import guardar_archivo
from app.application.usuarios.schemas import UsuarioCreate, UsuarioOut
from app.application.usuarios.service import UsuarioService
from app.core.config import settings
from app.core.email import build_reset_email_html, send_email
from app.core.exceptions import (
    BusinessRuleException,
    TooManyRequestsException,
    UnauthorizedException,
)
from app.core.reloj import Reloj, ahora_utc
from app.core.security import (
    JWTError,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    sello_password,
    verify_password,
)
from app.infrastructure.repositories.academico_repository import ProfesorEspecializacionRepository
from app.infrastructure.repositories.actores_repository import (
    AdministradorRepository,
    EstudianteRepository,
    PadreRepository,
    ProfesorRepository,
)
from app.infrastructure.repositories.sesion_repository import SesionRepository
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

logger = logging.getLogger(__name__)

# Avatares (BE-14): carpeta pública, formatos reales permitidos y tamaño máximo.
AVATAR_DIR = "static/avatars"
AVATAR_MAX_BYTES = 2 * 1024 * 1024
AVATAR_FORMATOS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

# id_rol de la tabla roles (ver seed_data.sql).
ROL_DOCENTE = 1
ROL_ESTUDIANTE = 2
ROL_ADMIN = 3
ROL_PADRE = 4


class AuthService:
    def __init__(self, session: AsyncSession, reloj: Reloj = ahora_utc):
        self.repo = UsuarioRepository(session)
        self.sesiones = SesionRepository(session)
        self.session = session
        self.reloj = reloj

    async def register(self, data: RegisterRequest) -> UsuarioOut:
        user_service = UsuarioService(self.session)
        user_data = UsuarioCreate.model_validate(data.model_dump())
        user_out = await user_service.create(user_data)

        # El perfil se elige por id_rol, igual que la regla de activación de
        # abajo: en la BD los roles se llaman 'docente'/'admin', así que comparar
        # por nombre contra 'profesor'/'administrador' nunca creaba esos perfiles.
        id_rol = user_out.id_rol

        if id_rol == ROL_ESTUDIANTE:
            est_repo = EstudianteRepository(self.session)
            await est_repo.create({
                "id_usuario": user_out.id_usuario,
                "codigo_estudiante": data.numero_documento,
                "fecha_ingreso": date.today(),
                "id_curso_actual": data.id_curso_actual
            })
        elif id_rol == ROL_DOCENTE:
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
        elif id_rol == ROL_PADRE:
            if data.id_estudiante_vinculado and data.parentesco:
                padre_repo = PadreRepository(self.session)
                await padre_repo.create({
                    "id_usuario": user_out.id_usuario,
                    "id_estudiante": data.id_estudiante_vinculado,
                    "parentesco": data.parentesco,
                    "ocupacion": None
                })
        elif id_rol == ROL_ADMIN:
            admin_repo = AdministradorRepository(self.session)
            await admin_repo.create({
                "id_usuario": user_out.id_usuario,
                "cargo": data.cargo or "Administrador",
                "fecha_asignacion": date.today()
            })

        # Profesor (id_rol=1) y Administrador (id_rol=3) quedan INACTIVOS al
        # auto-registrarse: deben pasar por la bandeja de validación y ser activados
        # por un administrador activo antes de poder iniciar sesión. (El login rechaza
        # estado=False con "Usuario inactivo"; la bandeja lista los estado=False.)
        # Estudiante (2) y Padre (4) siguen activos por defecto.
        # Se compara por id_rol (estable) y no por nombre: en la BD los roles se
        # llaman 'docente'/'admin', no 'profesor'/'administrador'.
        if id_rol in (ROL_DOCENTE, ROL_ADMIN):
            user_model = await self.repo.get_by_id(user_out.id_usuario)
            if user_model:
                user_model.estado = False
                user_out.estado = False

        await self.session.commit()
        return user_out

    async def login(self, data: LoginRequest) -> TokenResponse:
        ahora = self.reloj()
        user = await self.repo.get_by_correo(data.correo)
        if user and user.bloqueado_hasta and user.bloqueado_hasta > ahora:
            # Aunque la contraseña sea correcta: el bloqueo corre hasta que venza.
            raise TooManyRequestsException(
                f"Demasiados intentos, espera {settings.LOGIN_BLOQUEO_MINUTOS} minutos"
            )
        if not user or not user.password or not verify_password(data.password, user.password):
            if user:
                await self._registrar_fallo(user.id_usuario, ahora)
            raise UnauthorizedException("Credenciales inválidas")
        if not user.estado:
            raise UnauthorizedException("Usuario inactivo")

        await self.repo.reiniciar_fallos(user.id_usuario)

        payload = {"sub": str(user.id_usuario), "idRol": user.id_rol, "rol": user.rol.nombre_rol}
        access_token = create_access_token(payload)
        refresh_token, jti = create_refresh_token(payload)
        expira = ahora + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.sesiones.crear(jti, user.id_usuario, expira)
        await self.sesiones.limpiar_vencidas()

        user.ultimo_acceso = ahora
        await self.session.flush()

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def _registrar_fallo(self, id_usuario: int, ahora) -> None:
        intentos = await self.repo.registrar_fallo(id_usuario)
        if intentos >= settings.LOGIN_MAX_INTENTOS:
            hasta = ahora + timedelta(minutes=settings.LOGIN_BLOQUEO_MINUTOS)
            await self.repo.bloquear(id_usuario, hasta)
            logger.warning("Usuario %s bloqueado hasta %s por intentos fallidos", id_usuario, hasta)
        # El fallo debe quedar guardado aunque la petición termine en 401.
        await self.session.commit()

    async def refresh(self, refresh_token: str) -> AccessTokenResponse:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            raise UnauthorizedException("Token inválido")
        if payload.get("type") != "refresh" or not payload.get("jti"):
            raise UnauthorizedException("Token inválido")

        # La sesión debe existir, no estar revocada ni vencida...
        if not await self.sesiones.obtener_activa(payload["jti"]):
            raise UnauthorizedException("Token expirado o revocado")
        # ...y la cuenta debe seguir activa.
        user = await self.repo.get_by_id(int(payload["sub"]))
        if not user or not user.estado:
            raise UnauthorizedException("Usuario inactivo")

        new_payload = {"sub": payload["sub"], "idRol": payload["idRol"], "rol": payload["rol"]}
        return AccessTokenResponse(access_token=create_access_token(new_payload))

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            return
        if payload.get("jti"):
            await self.sesiones.revocar(payload["jti"])

    async def forgot_password(self, correo: str) -> None:
        """Genera un token de reseteo y envía el enlace por correo.

        No revela si el correo existe (respuesta siempre neutra desde el endpoint).
        El token NUNCA se devuelve en la respuesta HTTP: sale solo por email (y, en
        desarrollo, se registra en el log para poder probar sin Resend configurado).
        """
        user = await self.repo.get_by_correo(correo.strip().lower())
        if not user or not user.estado:
            return

        sello = sello_password(user.password_actualizada)
        token = create_password_reset_token(user.id_usuario, sello)
        reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
        html = build_reset_email_html(user.primer_nombre or "", reset_url)
        sent = await send_email(user.correo, "Restablece tu contraseña - EyeSchool", html)

        if not sent and settings.ENVIRONMENT == "development":
            logger.warning("[DEV] Enlace de recuperación para %s: %s", correo, reset_url)

    async def reset_password(self, token: str, new_password: str) -> None:
        try:
            payload = decode_token(token)
        except JWTError:
            raise UnauthorizedException("El enlace de recuperación es inválido o expiró")

        if payload.get("type") != "reset":
            raise UnauthorizedException("Token inválido")

        user = await self.repo.get_by_id(int(payload["sub"]))
        if not user:
            raise UnauthorizedException("Usuario no encontrado")
        # Enlace de un solo uso: si la contraseña ya cambió, la marca no coincide.
        if payload.get("pwd_ts", 0) != sello_password(user.password_actualizada):
            raise UnauthorizedException("El enlace de recuperación ya fue usado")

        await self.repo.update(
            user, {"password": hash_password(new_password), "password_actualizada": self.reloj()}
        )
        await self.repo.reiniciar_fallos(user.id_usuario)
        await self.sesiones.revocar_todas(user.id_usuario)
        await self.session.commit()

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

        # Se lee un byte de más para saber si se pasó del máximo sin cargar archivos enormes.
        contenido = await file.read(AVATAR_MAX_BYTES + 1)
        if len(contenido) > AVATAR_MAX_BYTES:
            raise BusinessRuleException("La imagen no puede superar los 2 MB")

        # Ni el content-type ni el nombre los controla el servidor: se abre el contenido real.
        try:
            with Image.open(io.BytesIO(contenido)) as imagen:
                imagen.verify()
                formato = imagen.format
        except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
            raise BusinessRuleException("El archivo debe ser una imagen JPG, PNG o WEBP")
        if formato not in AVATAR_FORMATOS:
            raise BusinessRuleException("El archivo debe ser una imagen JPG, PNG o WEBP")

        filename = f"{uuid.uuid4()}.{AVATAR_FORMATOS[formato]}"
        await anyio.to_thread.run_sync(
            guardar_archivo, os.path.join(AVATAR_DIR, filename), contenido, AVATAR_DIR
        )

        url = f"/static/avatars/{filename}"
        await self.repo.update(user, {"foto_perfil": url})
        return url
