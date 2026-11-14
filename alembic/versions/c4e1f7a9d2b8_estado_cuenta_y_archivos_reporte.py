"""estado_cuenta_y_archivos_reporte

N-31: `usuario.pendienteValidacion` distingue una cuenta autorregistrada que espera validación
de una que el administrador desactivó (las dos tienen `estado = false`).

N-23: `reporte_archivos` guarda el contenido de los archivos de reporte en la base. Antes iban al
disco del App Service, que se recrea en cada despliegue, y se perdían.

Es aditiva: el código anterior sigue funcionando con la base ya migrada (no lee la columna ni la
tabla), así que se puede migrar ANTES de desplegar sin cortar el servicio.

Revision ID: c4e1f7a9d2b8
Revises: b7d2e9a41c03
Create Date: 2026-11-13 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c4e1f7a9d2b8'
down_revision: Union[str, None] = 'b7d2e9a41c03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Roles que al autorregistrarse quedan inactivos hasta que un admin los valida (docente, admin).
ROLES_CON_VALIDACION = (1, 3)


def _pdf_de_ejemplo(nombre: str, tipo: str, inicio, fin) -> bytes:
    """PDF rotulado como ejemplo para los reportes del seed, que nunca tuvieron archivo.

    El seed los crea con `archivoGenerado = 'asistencia_junio_2026.pdf'` y similares: nombres que
    no existen en ningún lado (la API de subida siempre devuelve `/static/reportes/<uuid>.ext`),
    así que la descarga respondía 404. No se inventa un contenido que parezca real: el documento
    dice qué es.
    """
    from fpdf import FPDF

    def latin1(texto: str) -> str:
        return texto.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, latin1(nombre), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, latin1(f"Tipo: {tipo}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, latin1(f"Periodo: {inicio} a {fin}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.multi_cell(0, 7, latin1(
        "Documento de ejemplo de los datos de prueba (seed). Este reporte se cargó sin archivo; "
        "se generó este documento para que la descarga funcione. No contiene datos reales."
    ))
    return bytes(pdf.output())


def upgrade() -> None:
    # ------------------------------------------------------------------ N-31
    op.add_column('usuario', sa.Column('pendienteValidacion', sa.Boolean(), nullable=False,
                                       server_default=sa.text('false')), schema='public')
    # Cuentas que hoy esperan validación: docente o admin, inactivas y que nunca iniciaron sesión
    # (el login rechaza a los inactivos, así que una cuenta que ya entró alguna vez fue activada
    # y luego desactivada por un admin).
    op.execute(sa.text(
        'UPDATE public.usuario SET "pendienteValidacion" = true '
        'WHERE estado = false AND "ultimoAcceso" IS NULL AND "idRol" IN :roles'
    ).bindparams(sa.bindparam('roles', ROLES_CON_VALIDACION, expanding=True)))

    # ------------------------------------------------------------------ N-23
    op.create_table(
        'reporte_archivos',
        sa.Column('ruta', sa.Text(), primary_key=True),
        sa.Column('contenido', sa.LargeBinary(), nullable=False),
        sa.Column('tipo', sa.String(length=120), nullable=False),
        sa.Column('tamano', sa.Integer(), nullable=False),
        sa.Column('creado', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='public',
    )

    conexion = op.get_bind()
    sin_archivo = conexion.execute(sa.text(
        'SELECT "idReporte", "nombreReporte", "tipoReporte", "fechaInicio", "fechaFin" '
        'FROM public."Reportes" '
        'WHERE "archivoGenerado" IS NOT NULL AND "archivoGenerado" NOT LIKE \'/static/reportes/%\''
    )).fetchall()
    for id_reporte, nombre, tipo, inicio, fin in sin_archivo:
        ruta = f"/static/reportes/ejemplo-{id_reporte}.pdf"
        contenido = _pdf_de_ejemplo(nombre, tipo, inicio, fin)
        conexion.execute(sa.text(
            'INSERT INTO public.reporte_archivos (ruta, contenido, tipo, tamano) '
            'VALUES (:ruta, :contenido, \'application/pdf\', :tamano)'
        ), {"ruta": ruta, "contenido": contenido, "tamano": len(contenido)})
        conexion.execute(sa.text(
            'UPDATE public."Reportes" SET "archivoGenerado" = :ruta WHERE "idReporte" = :id'
        ), {"ruta": ruta, "id": id_reporte})


def downgrade() -> None:
    # Ojo: borra el contenido de los archivos subidos desde esta versión. Los reportes del seed
    # quedan apuntando a `/static/reportes/ejemplo-<id>.pdf`, que ya no existirá.
    op.drop_table('reporte_archivos', schema='public')
    op.drop_column('usuario', 'pendienteValidacion', schema='public')
