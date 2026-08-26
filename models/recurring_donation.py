from datetime import datetime, timezone

from extensions import db


class RecurringDonation(db.Model):
    __tablename__ = "recurring_donations"

    # ── Columns (matches ERD exactly) ─────────────────────────────────────────

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # FK → DONATIONS.id
    donation_id = db.Column(
        db.Integer,
        db.ForeignKey("donations.id"),
        nullable=False
    )

    # ERD: frequency (monthly/quarterly/yearly)
    frequency = db.Column(
        db.String(20),
        nullable=False,
        default="monthly"
    )

    next_donation_date = db.Column(
        db.Date,
        nullable=False
    )

    # ERD: status (active/cancelled/paused)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="active"
    )

    # ERD: cancelled_at (nullable)
    cancelled_at = db.Column(
        db.DateTime,
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

    # DONATION 1 → 0..1 RECURRING_DONATION
    donation = db.relationship(
        "Donation",
        back_populates="recurring_donation"
    )

    def __repr__(self):
        return f"<RecurringDonation {self.id}: {self.frequency} / {self.status}>"
