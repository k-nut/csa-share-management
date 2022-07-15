"""Mark fields non-nullable

Revision ID: 3abef02994a2
Revises: f92f33bd3b4a
Create Date: 2022-07-13 16:34:39.599007

"""

# revision identifiers, used by Alembic.
revision = '3abef02994a2'
down_revision = 'f92f33bd3b4a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('deposit', 'is_security',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    op.alter_column('deposit', 'ignore',
               existing_type=sa.BOOLEAN(),
               nullable=False)


def downgrade():
    op.alter_column('deposit', 'ignore',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('deposit', 'is_security',
               existing_type=sa.BOOLEAN(),
               nullable=True)
