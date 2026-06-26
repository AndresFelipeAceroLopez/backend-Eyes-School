from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.notas.schemas import NotaCreate, NotaOut, NotaUpdate
from app.core.exceptions import ConflictException, NotFoundException
from app.infrastructure.repositories.notas_repository import NotaRepository


class NotaService:
    def __init__(self, session: AsyncSession):
        self.repo = NotaRepository(session)

    async def list(
        self,
        id_estudiante: int | None = None,
        id_materia: int | None = None,
        id_periodo: int | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[NotaOut]:
        items = await self.repo.get_with_filters(
            id_estudiante=id_estudiante, id_materia=id_materia, id_periodo=id_periodo, skip=skip, limit=limit
        )
        return [NotaOut.model_validate(n) for n in items]

    async def get(self, id_nota: int) -> NotaOut:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        return NotaOut.model_validate(item)

    async def create(self, data: NotaCreate) -> NotaOut:
        if await self.repo.exists(data.id_estudiante, data.id_materia, data.id_periodo):
            raise ConflictException("Ya existe una nota para este estudiante, materia y período")
        item = await self.repo.create(data.model_dump())
        return NotaOut.model_validate(item)

    async def update(self, id_nota: int, data: NotaUpdate) -> NotaOut:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        updated = await self.repo.update(item, data.model_dump(exclude_none=True))
        return NotaOut.model_validate(updated)

    async def delete(self, id_nota: int) -> None:
        item = await self.repo.get_by_id(id_nota)
        if not item:
            raise NotFoundException("Nota no encontrada")
        await self.repo.delete(item)

    async def get_promedio(self, id_estudiante: int) -> float | None:
        return await self.repo.get_promedio_estudiante(id_estudiante)

    async def generate_boletin_pdf(self, id_estudiante: int) -> str:
        notas = await self.repo.get_with_filters(id_estudiante=id_estudiante, limit=1000)
        if not notas:
            raise NotFoundException("No se encontraron notas para el estudiante")

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

        from fpdf import FPDF
        import uuid
        import os
        from datetime import date

        def L(value) -> str:
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

        os.makedirs("tmp", exist_ok=True)
        filepath = os.path.join("tmp", f"boletin_{id_estudiante}_{uuid.uuid4()}.pdf")
        pdf.output(filepath)

        return filepath
