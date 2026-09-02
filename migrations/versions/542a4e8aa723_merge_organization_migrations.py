"""Merge organization migrations

Revision ID: 542a4e8aa723
Revises: b4c6d8e0f123, c3a7d9e1f204
Create Date: 2026-09-02 08:21:37.767872

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '542a4e8aa723'
down_revision = ('b4c6d8e0f123', 'c3a7d9e1f204')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
