"""empty message

Revision ID: ad3c46de6430
Revises: 1aa290efdeaf
Create Date: 2018-12-04 18:42:50.120600

"""

# revision identifiers, used by Alembic.
revision = 'ad3c46de6430'
down_revision = '1aa290efdeaf'

from alembic import op


def upgrade():
    connection = op.get_bind()

    connection.execute("DROP FUNCTION if exists expected_today(int);")
    connection.execute("""
    CREATE OR REPLACE FUNCTION expected_today(the_id int) RETURNS DECIMAL AS
    $$
    SELECT sum(bets.expected)
    FROM (
           SELECT CAST(EXTRACT(MONTH FROM age(COALESCE(end_date - '1 month'::interval, CURRENT_DATE),
                                              start_date - '2 month'::INTERVAL + '27 days'::interval))
             + EXTRACT(YEAR FROM age(COALESCE(end_date - '1 month'::interval, CURRENT_DATE),
                                     start_date - '2 month'::INTERVAL + '27 days'::interval)) * 12
                    AS integer) * VALUE AS expected
           FROM bet
           WHERE bet.share_id = $1
         ) bets;
    $$
    LANGUAGE SQL;
    """)


def downgrade():
    pass
