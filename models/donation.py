from datetime import datetime, timezone

from extensions import db


class Donation(db.Model):
    __tablename__ = "donations"

    # ── Columns (matches ERD exactly) ─────────────────────────────────────────

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # FK → USERS.id
    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    # FK → ORGANIZATIONS.id
    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id"),
        nullable=False
    )

    # FK → PROJECTS.id  (nullable — donation can be org-level, not project-level)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=True
    )

    amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    currency = db.Column(
        db.String(10),
        nullable=False,
        default="KES"
    )

    # ERD: donation_type (one-time/monthly)
    donation_type = db.Column(
        db.String(20),
        nullable=False,
        default="one-time"
    )

    is_anonymous = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    payment_ref = db.Column(
        db.String(100),
        nullable=True
    )

    # ERD: status (pending/success/failed)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    payment_method = db.Column(
        db.String(30),
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

    # DONOR (User) → 0..* DONATIONS
    donor = db.relationship(
        "User",
        foreign_keys=[donor_id],
        backref=db.backref("donations", lazy="dynamic")
    )

    # ORGANIZATION 1 → 0..* DONATIONS
    organization = db.relationship(
        "Organization",
        back_populates="donations"
    )

    # PROJECT 1 → 0..* DONATIONS  (optional)
    project = db.relationship(
        "Project",
        back_populates="donations"
    )

    # DONATION 1 → 0..1 RECURRING_DONATION
    recurring_donation = db.relationship(
        "RecurringDonation",
        back_populates="donation",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # DONATION 1 → 0..1 PAYMENT
    payment = db.relationship(
        "Payment",
        back_populates="donation",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Donation {self.id}: {self.amount} {self.currency}>"
