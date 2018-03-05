"""fill_null_fields

Revision ID: ccbd861dc9ff
Revises: 3e031fc645ae
Create Date: 2018-03-05 15:35:18.770873

"""

# revision identifiers, used by Alembic.
revision = 'ccbd861dc9ff'
down_revision = '3e031fc645ae'

from alembic import op
import sqlalchemy as sa


def upgrade():
    conn = op.get_bind()
    conn.execute("UPDATE deposit set is_security = FALSE where is_security is NULL")
    conn.execute("UPDATE deposit set ignore = FALSE where ignore is NULL")


def downgrade():
    pass

