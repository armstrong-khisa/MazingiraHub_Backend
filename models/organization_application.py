from datetime import datetime

from extensions import db


class OrganizationApplication(db.Model):
    __tablename__ = "organization_applications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    org_name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    registration_docs_url = db.Column(
        db.String(500),
        nullable=True
    )

    reviewed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    applicant = db.relationship(
        "User",
        foreign_keys=[user_id],
        backref="organization_applications"
    )

    reviewer = db.relationship(
        "User",
        foreign_keys=[reviewed_by]
    )

    def __repr__(self):
        return f"<OrganizationApplication {self.org_name}>"
