"""Link organization profiles to their authenticated users."""
from alembic import op
import sqlalchemy as sa


revision = "b4c6d8e0f123"
down_revision = "f1a844147b31"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_unique_constraint("uq_organizations_user_id", ["user_id"])
        batch_op.create_foreign_key("fk_organizations_user_id", "users", ["user_id"], ["id"])


def downgrade():
    with op.batch_alter_table("organizations") as batch_op:
        batch_op.drop_constraint("fk_organizations_user_id", type_="foreignkey")
        batch_op.drop_constraint("uq_organizations_user_id", type_="unique")
        batch_op.drop_column("user_id")