from __future__ import annotations

import anyio

# fpdf se importa al arrancar, no en la primera petición: su importación en frío (fonttools,
# Pillow) tarda ~1,2 s y la pagaba el primer boletín después de cada despliegue (CP-INT-051).
from fpdf import FPDF
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.notas.schemas import NotaCreate, NotaOut, NotaUpdate
from app.core.dependencies import CurrentUser
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.infrastructure.repositories.academico_repository import AsignacionRepository
from app.infrastructure.repositories.actores_repository import (
    EstudianteRepository,
    ProfesorRepository,
)
from app.infrastructure.repositories.notas_repository import NotaRepository

MENSAJE_BOLETIN_SIN_NOTAS = "No hay datos disponibles para generar el boletín."


class NotaService:
    def __init__(self, session: AsyncSession):
        self.repo = NotaRepository(session)
        self.profesor_repo = ProfesorRepository(session)
        self.estudiante_repo = EstudianteRepository(session)
        self.asignacion_repo = AsignacionRepository(session)

    async def _id_profesor(self, actor: CurrentUser) -> int:
        profesor = await self.profesor_repo.get_by_usuario(actor.id_usuario)
        if not profesor:
            raise ForbiddenException("Perfil docente no encontrado")
        return profesor.id_profesor

    async def _exigir_asignacion(self, actor: CurrentUser, id_estudiante: int, id_materia: int) -> None:
        """Un docente solo califica las materias que dicta en el curso del estudiante."""
        if actor.nombre_rol != "docente":
            return
        id_profesor = await self._id_profesor(actor)
        estudiante = await self.estudiante_repo.get_by_id(id_estudiante)
        if not estudiante:
            raise NotFoundException("Estudiante no encontrado")
        if estudiante.id_curso_actual is None or not await self.asignacion_repo.docente_dicta(
            id_profesor, id_materia, estudiante.id_curso_actual
        ):
            raise ForbiddenException("No tiene asignada esta materia en el curso del estudiante")

    async def list(
        self,
        id_estudiante: int | None = None,
        id_materia: int | None = None,
        id_periodo: int | None = None,
        skip: int = 0,
        limit: int = 100,
        actor: CurrentUser | None = None,
    ) -> list[NotaOut]:
        # El docente solo lee las notas de los cursos que dicta.
        id_profesor = None
        if actor is not None and actor.nombre_rol == "docente":
            id_profesor = await self._id_profesor(actor)
        items = await self.repo.get_with_filters(
            id_estudiante=id_estudiante, id_materia=id_materia, id_periodo=id_periodo,
            skip=skip, limit=limit, id_profesor=id_profesor,
        )
        return [NotaOut.model_validate(n) for n in items]

    async def get(self, id_nota: int, actor: CurrentUser | None = None) -> NotaOut:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        if actor is not None and actor.nombre_rol == "docente":
            await self._exigir_asignacion(actor, item.id_estudiante, item.id_materia)
        return NotaOut.model_validate(item)

    async def create(self, data: NotaCreate, actor: CurrentUser) -> NotaOut:
        """`registrado_por` sale del token, nunca del cuerpo de la petición."""
        await self._exigir_asignacion(actor, data.id_estudiante, data.id_materia)
        if await self.repo.exists(data.id_estudiante, data.id_materia, data.id_periodo):
            raise ConflictException("Ya existe una nota para este estudiante, materia y período")
        item = await self.repo.create({**data.model_dump(), "registrado_por": actor.id_usuario})
        return NotaOut.model_validate(item)

    async def update(self, id_nota: int, data: NotaUpdate, actor: CurrentUser) -> NotaOut:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        await self._exigir_asignacion(actor, item.id_estudiante, item.id_materia)
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return NotaOut.model_validate(updated)

    async def delete(self, id_nota: int, actor: CurrentUser) -> None:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        await self._exigir_asignacion(actor, item.id_estudiante, item.id_materia)
        await self.repo.delete(item)

    async def get_promedio(self, id_estudiante: int) -> float | None:
        return await self.repo.get_promedio_estudiante(id_estudiante)

    async def generate_boletin_pdf(self, id_estudiante: int) -> bytes:
        """Boletín en PDF, generado en memoria: no deja archivos en el servidor."""
        notas = await self.repo.get_with_filters(id_estudiante=id_estudiante, limit=1000)
        if not notas:
            raise NotFoundException(MENSAJE_BOLETIN_SIN_NOTAS)

        estudiante = await self.repo.get_estudiante_con_usuario(id_estudiante)
        nombre = "N/A"
        codigo = str(id_estudiante)
        if estudiante:
            codigo = estudiante.codigo_estudiante or codigo
            u = estudiante.usuario
            if u:
                nombre = " ".join(
                    p for p in (u.primer_nombre, u.segundo_nombre, u.primer_apellido, u.segundo_apellido) if p
                ) or nombre

        promedio = await self.get_promedio(id_estudiante)

        # Armar el PDF es CPU: en un hilo, para no congelar las demás peticiones (como bcrypt).
        def construir() -> bytes:
            from datetime import date

            def L(value) -> str:  # noqa: N802 (atajo usado en todo el PDF)
                # Las fuentes core de fpdf usan latin-1; reemplaza caracteres fuera de ese rango.
                return str(value).encode("latin-1", "replace").decode("latin-1")

            pdf = FPDF()
            pdf.add_page()

            # Encabezado
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 10, L("Boletín de Notas"), new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, L("EyeSchool"), new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(4)

            # Datos del estudiante
            pdf.cell(0, 7, L(f"Estudiante: {nombre}"), new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, L(f"Código: {codigo}"), new_x="LMARGIN", new_y="NEXT")
            pdf.cell(0, 7, L(f"Fecha de emisión: {date.today().strftime('%d/%m/%Y')}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

            # Agrupa las notas por periodo académico
            por_periodo: dict[int, list] = {}
            for nota in notas:
                por_periodo.setdefault(nota.id_periodo, []).append(nota)

            for periodo in sorted(por_periodo):
                items = por_periodo[periodo]

                pdf.set_font("Helvetica", "B", 13)
                pdf.cell(0, 9, L(f"Periodo {periodo}"), new_x="LMARGIN", new_y="NEXT")

                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(120, 8, L("Materia"), border=1)
                pdf.cell(30, 8, L("Nota"), border=1, align="C")
                pdf.ln()

                pdf.set_font("Helvetica", "", 11)
                suma = 0.0
                for nota in items:
                    materia_nombre = nota.materia.nombre_materia if nota.materia else f"ID {nota.id_materia}"
                    valor = float(nota.nota)
                    suma += valor
                    pdf.cell(120, 8, L(materia_nombre), border=1)
                    pdf.cell(30, 8, f"{valor:.2f}", border=1, align="C")
                    pdf.ln()

                prom_periodo = suma / len(items) if items else 0.0
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(120, 8, L("Promedio del periodo"), border=1)
                pdf.cell(30, 8, f"{prom_periodo:.2f}", border=1, align="C")
                pdf.ln()
                pdf.ln(4)

            # Promedio general
            pdf.set_font("Helvetica", "B", 12)
            promedio_str = f"{float(promedio):.2f}" if promedio is not None else "N/A"
            pdf.cell(0, 9, L(f"Promedio general: {promedio_str}"), new_x="LMARGIN", new_y="NEXT")

            return bytes(pdf.output())

        return await anyio.to_thread.run_sync(construir)
