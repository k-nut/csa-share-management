"""extract bets

Revision ID: 56a234140efd
Revises: ccbd861dc9ff
Create Date: 2018-03-16 09:42:49.721830

"""

# revision identifiers, used by Alembic.
revision = '56a234140efd'
down_revision = 'ccbd861dc9ff'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('bet',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Numeric(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('end_date', sa.DateTime(), nullable=True),
    sa.Column('share_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['share_id'], ['share.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    connection = op.get_bind()

    connection.execute("""
    INSERT INTO bet(start_date, end_date, value, share_id)
    SELECT start_date, '2017-12-31'::date, bet_value, id
    FROM share
    RETURNING id
    """)

    op.drop_column('share', 'bet_value')
    op.drop_column('share', 'start_date')


def downgrade():
    op.add_column('share', sa.Column('start_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True))
    op.add_column('share', sa.Column('bet_value', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.drop_table('bet')
