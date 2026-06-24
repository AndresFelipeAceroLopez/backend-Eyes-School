"""add_foto_perfil_usuario

Revision ID: a1b2c3d4e5f6
Revises: 7c1badcb31be
Create Date: 2026-06-22 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '7c1badcb31be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'usuario',
        sa.Column('fotoPerfil', sa.String(length=255), nullable=True),
        schema='public',
    )


def downgrade() -> None:
    op.drop_column('usuario', 'fotoPerfil', schema='public')
