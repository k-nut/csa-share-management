"""empty message

Revision ID: 3d3dfb1686e8
Revises: 39cbdaf5dcb6
Create Date: 2018-04-22 10:40:29.272517

"""

# revision identifiers, used by Alembic.
revision = '3d3dfb1686e8'
down_revision = '39cbdaf5dcb6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    connection = op.get_bind()

    connection.execute("DROP FUNCTION if exists expected_today(int);")
    connection.execute("""
CREATE OR REPLACE FUNCTION expected_today (the_id int) RETURNS DECIMAL AS $$
SELECT sum(bets.expected) FROM (
  SELECT
   CAST(
     EXTRACT('months'
       FROM age(COALESCE(end_date - '1 month'::interval, CURRENT_DATE),
                start_date-'2 month'::INTERVAL + '27 days'::interval)
    ) AS integer) * VALUE AS expected
  FROM bet
   WHERE bet.share_id=$1
) bets;
$$
LANGUAGE SQL;
""")


def downgrade():
    pass
