"""add added_by to Deposit

Revision ID: 1aa290efdeaf
Revises: 3d3dfb1686e8
Create Date: 2018-05-06 16:25:08.182128

"""

# revision identifiers, used by Alembic.
revision = '1aa290efdeaf'
down_revision = '3d3dfb1686e8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('deposit', sa.Column('added_by', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'deposit', 'user', ['added_by'], ['id'])


def downgrade():
    op.drop_constraint(None, 'deposit', type_='foreignkey')
    op.drop_column('deposit', 'added_by')
