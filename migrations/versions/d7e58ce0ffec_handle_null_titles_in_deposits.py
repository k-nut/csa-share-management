"""Handle `null` titles in deposits

Revision ID: d7e58ce0ffec
Revises: b17d4b60c238
Create Date: 2024-03-13 07:29:11.561112

"""
from solawi.models import Deposit

# revision identifiers, used by Alembic.
revision = 'd7e58ce0ffec'
down_revision = 'b17d4b60c238'

from alembic import op


def upgrade():
    op.drop_constraint("_all_fields", "deposit")
    op.create_index("_all_fields_without_null_title",
                    "deposit",
                    [
                        "timestamp",
                        "amount",
                        "title",
                        "person_id"],
                    unique=True,
                    postgresql_where=(Deposit.title.isnot(None)),
                    )
    op.create_index("_all_fields_with_null_title",
                    "deposit",
                    [
                        "timestamp",
                        "amount",
                        "person_id"],
                    unique=True,
                    postgresql_where=(Deposit.title.is_(None)),
                    )

    def downgrade():
        op.drop_index("_all_fields_without_null_title")
        op.drop_index("_all_fields_with_null_title")
