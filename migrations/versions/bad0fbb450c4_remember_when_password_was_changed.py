"""remember when password was changed

Revision ID: bad0fbb450c4
Revises: 1b57ec4416e2
Create Date: 2020-02-02 12:21:11.553055

"""

# revision identifiers, used by Alembic.
revision = 'bad0fbb450c4'
down_revision = '1b57ec4416e2'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user', sa.Column('password_changed_at', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('user', 'password_changed_at')
