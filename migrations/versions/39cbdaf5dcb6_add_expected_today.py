"""create expected_today function

Revision ID: 39cbdaf5dcb6
Revises: 56a234140efd
Create Date: 2018-03-17 10:48:07.552895

"""

# revision identifiers, used by Alembic.
revision = '39cbdaf5dcb6'
down_revision = '56a234140efd'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    connection = op.get_bind()

    connection.execute("DROP FUNCTION if exists expected_today(int);")
    connection.execute("""
    CREATE OR REPLACE FUNCTION expected_today (the_id int) RETURNS FLOAT AS $$
SELECT sum(bets.expected) FROM (
  SELECT 
   EXTRACT('months' FROM age(COALESCE(end_date - '1 month'::interval, CURRENT_DATE), start_date-'2 month'::INTERVAL + '27 days'::interval)) * VALUE AS   expected
  FROM bet
   WHERE bet.share_id=$1
) bets; 
$$
LANGUAGE SQL;
    """)


def downgrade():
    pass
