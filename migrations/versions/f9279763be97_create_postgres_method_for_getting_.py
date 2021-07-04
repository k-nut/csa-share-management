"""create postgres method for getting expected amount

Revision ID: f9279763be97
Revises: bad0fbb450c4
Create Date: 2021-01-17 11:08:10.649064

"""

# revision identifiers, used by Alembic.

revision = 'f9279763be97'
down_revision = 'bad0fbb450c4'

from alembic import op
from migrations.utils import get_sql


def upgrade():
    connection = op.get_bind()

    connection.execute(get_sql('get_expected_today_1.sql'))


def downgrade():
    connection = op.get_bind()

    connection.execute("""
    DROP FUNCTION get_expected_today(IN start_date date, IN end_date date, IN amount decimal, OUT amount_due decimal);
    """)
