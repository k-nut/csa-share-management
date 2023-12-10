"""create members from share names

Revision ID: db09552d8be0
Revises: 503c0deffad6
Create Date: 2018-12-05 20:35:51.178462

"""
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'db09552d8be0'
down_revision = '503c0deffad6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    connection = op.get_bind()

    connection.execute(text("""
    INSERT INTO member(name, share_id)
    SELECT unnest(regexp_split_to_array(name, '\s*([,&]|und)\s*', 'i')), id FROM share;
    """))
    op.drop_column('share', 'name')
    op.drop_column('share', 'email')


def downgrade():
    op.add_column('share', sa.Column('email', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.add_column('share', sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True))
