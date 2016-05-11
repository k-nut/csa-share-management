"""add start date to share

Revision ID: c0de89fb178b
Revises: 362ad377bf0f
Create Date: 2016-05-11 17:11:01.539488

"""

# revision identifiers, used by Alembic.
revision = 'c0de89fb178b'
down_revision = '362ad377bf0f'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('share', sa.Column('start_date', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('share', 'start_date')
