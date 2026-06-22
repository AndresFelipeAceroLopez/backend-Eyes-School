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
            
        promedio = await self.get_promedio(id_estudiante)
        
        from fpdf import FPDF
        import uuid
        import os
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, txt="Boletín de Notas", new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, txt=f"Estudiante ID: {id_estudiante}", new_x="LMARGIN", new_y="NEXT")
        promedio_str = f"{float(promedio):.2f}" if promedio else "N/A"
        pdf.cell(0, 10, txt=f"Promedio General: {promedio_str}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(80, 10, "Materia", border=1)
        pdf.cell(40, 10, "Periodo", border=1)
        pdf.cell(40, 10, "Nota", border=1)
        pdf.ln()
        
        pdf.set_font("Helvetica", size=12)
        for nota in notas:
            materia_nombre = nota.materia.nombre_materia if nota.materia else f"ID: {nota.id_materia}"
            # Some versions might not load periodo dynamically, so fallback to ID
            periodo_nombre = str(nota.id_periodo)
            valor_nota = f"{float(nota.nota):.2f}" if nota.nota else "N/A"
            pdf.cell(80, 10, str(materia_nombre), border=1)
            pdf.cell(40, 10, periodo_nombre, border=1)
            pdf.cell(40, 10, valor_nota, border=1)
            pdf.ln()
            
        os.makedirs("tmp", exist_ok=True)
        filepath = os.path.join("tmp", f"boletin_{id_estudiante}_{uuid.uuid4()}.pdf")
        pdf.output(filepath)
        
        return filepath
