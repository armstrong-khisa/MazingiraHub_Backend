from datetime import datetime, timezone

from extensions import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    organization_id = db.Column(
        db.Integer,
        db.ForeignKey("organizations.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    goal_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    amount_raised = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0.00
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=True
    )

    completed = db.Column(
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

    # Relationships
    organization = db.relationship(
        "Organization",
        back_populates="projects"
    )

    donations = db.relationship(
        "Donation",
        back_populates="project",
        lazy="dynamic"
    )

    def progress_percentage(self):
        """Return funding progress as a percentage (0–100)."""
        if not self.goal_amount or self.goal_amount == 0:
            return 0.0
        pct = (float(self.amount_raised) / float(self.goal_amount)) * 100
        return round(min(pct, 100.0), 2)

    def is_active(self):
        """A project is active if not completed and within its date range."""
        today = datetime.now(timezone.utc).date()
        if self.completed:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    def __repr__(self):
        return f"<Project {self.id}: {self.title}>"
