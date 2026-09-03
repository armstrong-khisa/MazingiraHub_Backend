"""Align payment and donation status values.

Revision ID: c7b3e9a1d2f4
Revises: f1a844147b31
Create Date: 2026-09-04
"""

from alembic import op
import sqlalchemy as sa


revision = "c7b3e9a1d2f4"
down_revision = "542a4e8aa723"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE donations SET status = 'paid' WHERE status = 'success'")
    )
    connection.execute(
        sa.text("UPDATE donations SET status = 'cancelled' WHERE status = 'failed'")
    )
    connection.execute(
        sa.text("UPDATE payments SET status = 'paid' WHERE status = 'success'")
    )
    connection.execute(
        sa.text("UPDATE payments SET status = 'cancelled' WHERE status = 'failed'")
    )


def downgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE donations SET status = 'success' WHERE status = 'paid'")
    )
    connection.execute(
        sa.text("UPDATE donations SET status = 'failed' WHERE status = 'cancelled'")
    )
    connection.execute(
        sa.text("UPDATE payments SET status = 'success' WHERE status = 'paid'")
    )
    connection.execute(
        sa.text("UPDATE payments SET status = 'failed' WHERE status = 'cancelled'")
    )