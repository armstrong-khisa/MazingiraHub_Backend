from datetime import datetime, timezone

from extensions import db


class Donation(db.Model):
    __tablename__ = "donations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id"),
        nullable=False
    )

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

    # Relationships
    project = db.relationship(
        "Project",
        back_populates="donations"
    )

    def __repr__(self):
        return f"<Donation {self.id}: {self.amount} {self.currency}>"
