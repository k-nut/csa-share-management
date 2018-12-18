"""add member model

Revision ID: 503c0deffad6
Revises: ad3c46de6430
Create Date: 2018-12-05 20:26:05.489561

"""

# revision identifiers, used by Alembic.
revision = '503c0deffad6'
down_revision = 'ad3c46de6430'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('member',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('share_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['share_id'], ['share.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('member')
