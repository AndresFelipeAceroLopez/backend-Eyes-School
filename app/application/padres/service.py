from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.padres.schemas import HijoOut, PadreOut
from app.core.exceptions import ForbiddenException, NotFoundException
from app.infrastructure.repositories.actores_repository import PadreRepository


def _nombre(usuario) -> str | None:
    if usuario is None:
        return None
    return f"{usuario.primer_nombre} {usuario.primer_apellido}"


class PadreService:
    def __init__(self, session: AsyncSession):
        self.repo = PadreRepository(session)

    async def hijos(self, id_usuario: int) -> list[HijoOut]:
        """Todos los estudiantes vinculados al acudiente (lista vacía si no tiene ninguno)."""
        vinculos = await self.repo.list_by_usuario(id_usuario)
        hijos = []
        for v in vinculos:
            est = v.estudiante
            usuario = est.usuario if est is not None else None
            hijos.append(
                HijoOut(
                    id_estudiante=v.id_estudiante,
                    nombre_estudiante=_nombre(usuario),
                    documento_estudiante=usuario.numero_documento if usuario else None,
                    parentesco=v.parentesco,
                    id_curso_actual=est.id_curso_actual if est is not None else None,
                )
            )
        return hijos

    async def mi_vinculo(self, id_usuario: int, id_estudiante: int | None = None) -> PadreOut:
        """Vínculo con un hijo: el indicado (si es suyo) o, por compatibilidad, el primero."""
        vinculos = await self.repo.list_by_usuario(id_usuario)
        if not vinculos:
            raise NotFoundException("Perfil padre no encontrado")
        if id_estudiante is None:
            vinculo = vinculos[0]
        else:
            vinculo = next((v for v in vinculos if v.id_estudiante == id_estudiante), None)
            if vinculo is None:
                raise ForbiddenException("Solo puede consultar la información del estudiante asociado")
        out = PadreOut.model_validate(vinculo)
        est = vinculo.estudiante
        usuario = est.usuario if est is not None else None
        out.nombre_estudiante = _nombre(usuario)
        out.documento_estudiante = usuario.numero_documento if usuario else None
        return out
