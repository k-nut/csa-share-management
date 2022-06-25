"""Add Share.name

Revision ID: 07468e9f0233
Revises: f92f33bd3b4a
Create Date: 2022-06-25 18:12:01.839117

"""

# revision identifiers, used by Alembic.
revision = "07468e9f0233"
down_revision = "f92f33bd3b4a"

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column("share", sa.Column("name", sa.Text(), default="", nullable=True))


def downgrade():
    op.drop_column("share", "name")
