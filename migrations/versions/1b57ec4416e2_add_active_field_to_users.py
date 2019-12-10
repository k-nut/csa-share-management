"""add active field to users

Revision ID: 1b57ec4416e2
Revises: db09552d8be0
Create Date: 2019-12-10 07:34:39.510991

"""

# revision identifiers, used by Alembic.
revision = '1b57ec4416e2'
down_revision = 'db09552d8be0'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('active', sa.Boolean(), nullable=False, default=False, server_default='t'))


def downgrade():
    op.drop_column('user', 'active')
