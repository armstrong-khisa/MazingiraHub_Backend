from datetime import datetime, timezone

from extensions import db


class Organization(db.Model):
    __tablename__ = "organizations"

    # ── Columns (matches ERD exactly) ─────────────────────────────────────────

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    mission = db.Column(
        db.Text,
        nullable=True
    )

    location = db.Column(
        db.String(200),
        nullable=True
    )

    # FK → USERS.id  (admin who approved this org)
    approved_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    approved = db.Column(
        db.Boolean,
        nullable=False,
        default=False
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

    # The admin user who approved this org
    approver = db.relationship(
        "User",
        foreign_keys=[approved_by],
        backref=db.backref("approved_organizations", lazy="dynamic")
    )

    # ORGANIZATION 1 → 0..* PROJECTS
    projects = db.relationship(
        "Project",
        back_populates="organization",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # ORGANIZATION 1 → 0..* DONATIONS
    donations = db.relationship(
        "Donation",
        back_populates="organization",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<Organization {self.id}: {self.name}>"
