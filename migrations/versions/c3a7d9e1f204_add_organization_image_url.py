"""Add image URLs to organizations.

Revision ID: c3a7d9e1f204
Revises: f1a844147b31
Create Date: 2026-08-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c3a7d9e1f204"
down_revision = "f1a844147b31"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organizations",
        sa.Column("image_url", sa.String(length=500), nullable=True),
    )


def downgrade():
    op.drop_column("organizations", "image_url")
