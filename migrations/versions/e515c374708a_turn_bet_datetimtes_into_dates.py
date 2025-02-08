"""Turn Bet datetimtes into dates

Revision ID: e515c374708a
Revises: d7e58ce0ffec
Create Date: 2025-02-08 06:51:00.347086

"""

# revision identifiers, used by Alembic.
revision = 'e515c374708a'
down_revision = 'd7e58ce0ffec'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    with op.batch_alter_table('bet', schema=None) as batch_op:
        batch_op.alter_column('start_date',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.Date(),
               existing_nullable=False)
        batch_op.alter_column('end_date',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.Date(),
               existing_nullable=True)


def downgrade():
    with op.batch_alter_table('bet', schema=None) as batch_op:
        batch_op.alter_column('end_date',
               existing_type=sa.Date(),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=True)
        batch_op.alter_column('start_date',
               existing_type=sa.Date(),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False)
