"""Improve expected_today calculation if end_date is in the future

Revision ID: 236c477a1a2f
Revises: f9279763be97
Create Date: 2021-07-03 21:56:49.564486

"""

# revision identifiers, used by Alembic.
from migrations.utils import get_sql

revision = '236c477a1a2f'
down_revision = 'f9279763be97'

from alembic import op


def upgrade():
    connection = op.get_bind()

    connection.execute(get_sql('get_expected_today_2.sql'))


def downgrade():
    connection = op.get_bind()

    connection.execute(get_sql('get_expected_today_1.sql'))