"""Add ignore field to deposit

Revision ID: 362ad377bf0f
Revises: 1e4efa50f006
Create Date: 2016-05-11 14:29:24.764207

"""

# revision identifiers, used by Alembic.
revision = '362ad377bf0f'
down_revision = '1e4efa50f006'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('deposit', sa.Column('ignore', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('deposit', 'ignore')
