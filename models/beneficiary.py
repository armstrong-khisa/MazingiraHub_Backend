from datetime import datetime, timezone

from extensions import db


class Beneficiary(db.Model):
    __tablename__ = "beneficiaries"

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

    # ORGANIZATION 1 → 0..* BENEFICIARIES
    organization = db.relationship(
        "Organization",
        back_populates="beneficiaries"
    )

    def __repr__(self):
        return f"<Beneficiary {self.id}: {self.name}>"
