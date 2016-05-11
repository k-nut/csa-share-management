"""initial migration

Revision ID: 1e4efa50f006
Revises: None
Create Date: 2016-05-11 14:25:58.881051

"""

# revision identifiers, used by Alembic.
revision = '1e4efa50f006'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('share',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('bet_value', sa.Float(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('person',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('share_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['share_id'], ['share.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('deposit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Float(), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('is_security', sa.Boolean(), nullable=True),
    sa.Column('title', sa.Text(), nullable=True),
    sa.Column('person_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['person_id'], ['person.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('timestamp', 'amount', 'title', 'person_id', name='_all_fields')
    )


def downgrade():
    op.drop_table('deposit')
    op.drop_table('person')
    op.drop_table('share')
