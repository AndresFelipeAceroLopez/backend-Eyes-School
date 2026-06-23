from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.usuarios.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import hash_password
from app.infrastructure.repositories.usuario_repository import RolRepository, UsuarioRepository


class UsuarioService:
    def __init__(self, session: AsyncSession):
        self.repo = UsuarioRepository(session)
        self.rol_repo = RolRepository(session)

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

    async def update(self, id_usuario: int, data: UsuarioUpdate) -> UsuarioOut:
        user = await self.repo.get_by_id_with_rol(id_usuario)
        if not user:
            raise NotFoundException("Usuario no encontrado")
        if data.correo and await self.repo.correo_exists(data.correo, exclude_id=id_usuario):
            raise ConflictException("El correo ya está en uso")

        updated = await self.repo.update(user, data.model_dump(exclude_none=True))
        return UsuarioOut.model_validate(await self.repo.get_by_id_with_rol(updated.id_usuario))

    async def toggle_estado(self, id_usuario: int, estado: bool) -> UsuarioOut:
        user = await self.repo.get_by_id_with_rol(id_usuario)
        if not user:
            raise NotFoundException("Usuario no encontrado")
        updated = await self.repo.update(user, {"estado": estado})
        return UsuarioOut.model_validate(await self.repo.get_by_id_with_rol(updated.id_usuario))

    async def delete(self, id_usuario: int) -> None:
        user = await self.repo.get_by_id(id_usuario)
        if not user:
            raise NotFoundException("Usuario no encontrado")
        await self.repo.delete(user)

    async def list_roles(self) -> list:
        roles = await self.rol_repo.get_all()
        return roles
