from datetime import datetime, timezone

from extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

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

    # M-Pesa CheckoutRequestID or provider transaction ID
    provider_payment_id = db.Column(
        db.String(100),
        nullable=True,
        unique=True
    )

    # ERD: payment_method (stripe/paypal/mpesa)
    payment_method = db.Column(
        db.String(30),
        nullable=False,
        default="mpesa"
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

    # Status values: pending, paid, cancelled
    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    # Raw callback payload stored for audit/debugging
    raw_callback = db.Column(
        db.Text,
        nullable=True
    )

    # Set when status becomes paid.
    paid_at = db.Column(
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

    # DONATION 1 → 0..1 PAYMENT
    donation = db.relationship(
        "Donation",
        back_populates="payment"
    )

    def __repr__(self):
        return f"<Payment {self.id}: {self.status} / {self.amount} {self.currency}>"
