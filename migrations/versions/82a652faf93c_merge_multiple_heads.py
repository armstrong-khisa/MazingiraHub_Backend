"""merge multiple heads

Revision ID: 82a652faf93c
Revises: a91f4e2c7b10, c7b3e9a1d2f4
Create Date: 2026-09-04 10:16:34.823669

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82a652faf93c'
down_revision = ('a91f4e2c7b10', 'c7b3e9a1d2f4')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
