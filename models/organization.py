from datetime import datetime

from extensions import db


class Organization(db.Model):
    __tablename__ = "organizations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(150),
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
        db.String(255),
        nullable=True
    )

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
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    approver = db.relationship(
        "User",
        foreign_keys=[approved_by]
    )

    def __repr__(self):
        return f"<Organization {self.name}>"
