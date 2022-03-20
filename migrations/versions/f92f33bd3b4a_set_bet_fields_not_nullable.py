"""Set Bet fields not nullable

Revision ID: f92f33bd3b4a
Revises: 236c477a1a2f
Create Date: 2022-03-20 09:21:10.506038

"""

# revision identifiers, used by Alembic.
revision = 'f92f33bd3b4a'
down_revision = '236c477a1a2f'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column('bet', 'value',
               existing_type=sa.NUMERIC(),
               nullable=False)
    op.alter_column('bet', 'start_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=False)
    op.alter_column('bet', 'share_id',
               existing_type=sa.INTEGER(),
               nullable=False)


def downgrade():
    op.alter_column('bet', 'share_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('bet', 'start_date',
               existing_type=postgresql.TIMESTAMP(),
               nullable=True)
    op.alter_column('bet', 'value',
               existing_type=sa.NUMERIC(),
               nullable=True)
