from datetime import datetime, timezone

from extensions import db


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    # ── Columns (matches ERD exactly) ─────────────────────────────────────────

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # FK → ORGANIZATIONS.id
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id"),
        nullable=False
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    unit = db.Column(
        db.String(50),
        nullable=True    # e.g. "kg", "litres", "pieces"
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────

    # ORGANIZATION 1 → 0..* INVENTORY_ITEMS
    organization = db.relationship(
        "Organization",
        back_populates="inventory_items"
    )

    def __repr__(self):
        return f"<InventoryItem {self.id}: {self.name} x{self.quantity}>"
