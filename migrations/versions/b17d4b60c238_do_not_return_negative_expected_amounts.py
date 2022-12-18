"""Do not return negative expected amounts

Revision ID: b17d4b60c238
Revises: 3abef02994a2
Create Date: 2022-12-18 14:24:43.437925

"""
from migrations.utils import get_sql

# revision identifiers, used by Alembic.
revision = 'b17d4b60c238'
down_revision = '3abef02994a2'

from alembic import op


def upgrade():
    connection = op.get_bind()

    connection.execute(get_sql('get_expected_today_3.sql'))


def downgrade():
    connection = op.get_bind()

    connection.execute(get_sql('get_expected_today_2.sql'))