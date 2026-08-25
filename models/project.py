from datetime import datetime, timezone

from extensions import db


class Project(db.Model):
    __tablename__ = "projects"

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

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    # ERD: goal_amount (decimal)
    goal_amount = db.Column(
        db.Numeric(12, 2),
        nullable=False
    )

    # ERD: amount_raised (decimal)  — starts at 0, updated when donations succeed
    amount_raised = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0.00
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    # ERD: end_date (nullable)
    end_date = db.Column(
        db.Date,
        nullable=True
    )

    # ERD: completed (boolean)
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

    # ── Relationships ──────────────────────────────────────────────────────────

    # ORGANIZATION 1 → 0..* PROJECTS  (many side)
    organization = db.relationship(
        "Organization",
        back_populates="projects"
    )

    # PROJECT 1 → 0..* DONATIONS
    donations = db.relationship(
        "Donation",
        back_populates="project",
        lazy="dynamic"
    )

    # ── Computed helpers ───────────────────────────────────────────────────────

    def progress_percentage(self):
        """Funding progress as a float between 0.0 and 100.0."""
        if not self.goal_amount or float(self.goal_amount) == 0:
            return 0.0
        pct = (float(self.amount_raised) / float(self.goal_amount)) * 100
        return round(min(pct, 100.0), 2)

    def is_active(self):
        """
        True when:
          - not marked completed, AND
          - today is on or after start_date, AND
          - end_date is either null or still in the future
        """
        today = datetime.now(timezone.utc).date()
        if self.completed:
            return False
        if today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    def __repr__(self):
        return f"<Project {self.id}: {self.title}>"
