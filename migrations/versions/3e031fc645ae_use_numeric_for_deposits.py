"""use_numeric_for_deposits

Revision ID: 3e031fc645ae
Revises: 446bd5b15bf2
Create Date: 2017-11-17 08:15:22.572528

"""

# revision identifiers, used by Alembic.
revision = '3e031fc645ae'
down_revision = '446bd5b15bf2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column(
        table_name='deposit',
        column_name='amount',
        nullable=False,
        type_=sa.types.NUMERIC(scale=2, precision=10)
    )


def downgrade():
    op.alter_column(
        table_name='deposit',
        column_name='amount',
        nullable=False,
        type_=sa.types.FLOAT()
    )