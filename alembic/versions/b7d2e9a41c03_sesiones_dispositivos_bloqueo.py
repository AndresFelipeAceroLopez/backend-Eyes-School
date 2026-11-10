"""sesiones_dispositivos_bloqueo

Sesiones de refresco en PostgreSQL (BE-17, reemplaza a Redis), enlace de recuperación de
un solo uso (BE-13), bloqueo de inicio de sesión (BE-16), dispositivos para push (BE-18)
y correo único sin distinguir mayúsculas (BE-12).

Revision ID: b7d2e9a41c03
Revises: a1b2c3d4e5f6
Create Date: 2026-11-02 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b7d2e9a41c03'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # BE-12: el índice único falla si hay dos correos que solo difieren en mayúsculas.
    # Antes hay que correr `python -m scripts.normalizar_correos` (reporta y, con
    # --aplicar, pasa los correos a minúsculas).
    choques = op.get_bind().execute(sa.text(
        'SELECT lower(correo) FROM public.usuario WHERE correo IS NOT NULL '
        'GROUP BY lower(correo) HAVING count(*) > 1'
    )).fetchall()
    if choques:
        raise RuntimeError(
            f"Hay {len(choques)} correos repetidos al pasar a minúsculas. "
            "Corra scripts/normalizar_correos.py y resuélvalos antes de migrar."
        )

    op.add_column('usuario', sa.Column('passwordActualizada', sa.DateTime(), nullable=True),
                  schema='public')
    op.add_column('usuario', sa.Column('intentosFallidos', sa.Integer(), nullable=False,
                                       server_default='0'), schema='public')
    op.add_column('usuario', sa.Column('bloqueadoHasta', sa.DateTime(), nullable=True),
                  schema='public')
    op.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_usuario_correo_lower '
               'ON public.usuario (lower(correo)) WHERE correo IS NOT NULL')

    op.create_table(
        'sesiones_refresco',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('jti', sa.String(64), nullable=False, unique=True),
        sa.Column('idUsuario', sa.Integer(),
                  sa.ForeignKey('public.usuario.idUsuario', ondelete='CASCADE'), nullable=False),
        sa.Column('emitido', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('expira', sa.DateTime(), nullable=False),
        sa.Column('revocado', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        schema='public',
    )
    op.create_index('ix_sesiones_refresco_idUsuario', 'sesiones_refresco', ['idUsuario'],
                    schema='public')

    op.create_table(
        'dispositivos',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('idUsuario', sa.Integer(),
                  sa.ForeignKey('public.usuario.idUsuario', ondelete='CASCADE'), nullable=False),
        sa.Column('tokenFcm', sa.String(512), nullable=False, unique=True),
        sa.Column('plataforma', sa.String(20), nullable=False),
        sa.Column('actualizado', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        schema='public',
    )
    op.create_index('ix_dispositivos_idUsuario', 'dispositivos', ['idUsuario'], schema='public')


def downgrade() -> None:
    op.drop_index('ix_dispositivos_idUsuario', table_name='dispositivos', schema='public')
    op.drop_table('dispositivos', schema='public')
    op.drop_index('ix_sesiones_refresco_idUsuario', table_name='sesiones_refresco',
                  schema='public')
    op.drop_table('sesiones_refresco', schema='public')
    op.execute('DROP INDEX IF EXISTS public.uq_usuario_correo_lower')
    op.drop_column('usuario', 'bloqueadoHasta', schema='public')
    op.drop_column('usuario', 'intentosFallidos', schema='public')
    op.drop_column('usuario', 'passwordActualizada', schema='public')
