from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.usuarios.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.core.exceptions import BusinessRuleException, ConflictException, NotFoundException
from app.core.reloj import Reloj, ahora_utc
from app.core.security import hash_password, verify_password
from app.infrastructure.repositories.sesion_repository import SesionRepository
from app.infrastructure.repositories.usuario_repository import RolRepository, UsuarioRepository


class UsuarioService:
    def __init__(self, session: AsyncSession, reloj: Reloj = ahora_utc):
        self.repo = UsuarioRepository(session)
        self.rol_repo = RolRepository(session)
        self.sesiones = SesionRepository(session)
        self.reloj = reloj

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        id_rol: int | None = None,
        estado: bool | None = None,
        search: str | None = None,
    ) -> list[UsuarioOut]:
        users = await self.repo.get_all_with_filters(skip=skip, limit=limit, id_rol=id_rol, estado=estado, search=search)
        return [UsuarioOut.model_validate(u) for u in users]

    async def get(self, id_usuario: int) -> UsuarioOut:
        user = await self.repo.get_by_id_with_rol(id_usuario)
        if not user:
            raise NotFoundException("Usuario no encontrado")
        return UsuarioOut.model_validate(user)

    async def create(self, data: UsuarioCreate) -> UsuarioOut:
        if data.correo and await self.repo.correo_exists(data.correo):
            raise ConflictException("El correo ya está registrado")
        if await self.repo.documento_exists(data.numero_documento, data.tipo_documento):
            raise ConflictException("El documento ya está registrado")

        raw = data.model_dump()
        if raw.get("password"):
            raw["password"] = hash_password(raw["password"])

        user = await self.repo.create(raw)
        return UsuarioOut.model_validate(await self.repo.get_by_id_with_rol(user.id_usuario))

    async def update(
        self, id_usuario: int, data: UsuarioUpdate, exigir_password_actual: bool = False
    ) -> UsuarioOut:
        """`exigir_password_actual`: el usuario edita su propia cuenta (no es un admin), así
        que cambiar la contraseña requiere confirmar la actual."""
        user = await self.repo.get_by_id_with_rol(id_usuario)
        if not user:
            raise NotFoundException("Usuario no encontrado")
        if data.correo and await self.repo.correo_exists(data.correo, exclude_id=id_usuario):
            raise ConflictException("El correo ya está en uso")

        raw = data.model_dump(exclude_none=True)
        raw.pop("password_actual", None)
        if raw.get("password"):
            if exigir_password_actual:
                if not data.password_actual:
                    raise BusinessRuleException("Debe indicar la contraseña actual para cambiarla")
                if not user.password or not verify_password(data.password_actual, user.password):
                    raise BusinessRuleException("La contraseña actual no es correcta")
            raw["password"] = hash_password(raw["password"])
            raw["password_actualizada"] = self.reloj()

        updated = await self.repo.update(user, raw)
        return UsuarioOut.model_validate(await self.repo.get_by_id_with_rol(updated.id_usuario))

    async def toggle_estado(self, id_usuario: int, estado: bool) -> UsuarioOut:
        user = await self.repo.get_by_id_with_rol(id_usuario)
        if not user:
            raise NotFoundException("Usuario no encontrado")
        updated = await self.repo.update(user, {"estado": estado})
        if not estado:
            # Una cuenta desactivada pierde sus sesiones de refresco de inmediato.
            await self.sesiones.revocar_todas(id_usuario)
        return UsuarioOut.model_validate(await self.repo.get_by_id_with_rol(updated.id_usuario))

    async def delete(self, id_usuario: int) -> None:
        user = await self.repo.get_by_id(id_usuario)
        if not user:
            raise NotFoundException("Usuario no encontrado")
        # Borrado en cascada: elimina filas de rol y registros asociados
        # (asistencia/notas/novedades/reportes/...) que apuntan al usuario por FK,
        # en una sola transacción, para no violar las restricciones de clave foránea.
        await self.repo.delete_cascade(id_usuario)

    async def list_roles(self) -> list:
        roles = await self.rol_repo.get_all()
        return roles
