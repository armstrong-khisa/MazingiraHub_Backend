"""add image url to organization applications

Revision ID: a91f4e2c7b10
Revises: f1a844147b31
Create Date: 2026-09-04

"""
from alembic import op
import sqlalchemy as sa


revision = "a91f4e2c7b10"
down_revision = "f1a844147b31"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organization_applications",
        sa.Column("image_url", sa.String(length=500), nullable=True),
    )


def downgrade():
    op.drop_column("organization_applications", "image_url")