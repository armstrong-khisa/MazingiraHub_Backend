from datetime import datetime, timezone

from extensions import db


class Story(db.Model):
    __tablename__ = "stories"

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
        db.String(250),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    published = db.Column(
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

    # ORGANIZATION 1 → 0..* STORIES
    organization = db.relationship(
        "Organization",
        back_populates="stories"
    )

    # STORY 1 → 0..* STORY_MEDIA
    media = db.relationship(
        "StoryMedia",
        back_populates="story",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Story {self.id}: {self.title}>"


class StoryMedia(db.Model):
    __tablename__ = "story_media"

    # ── Columns (matches ERD exactly) ─────────────────────────────────────────

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # FK → STORIES.id
    story_id = db.Column(
        db.Integer,
        db.ForeignKey("stories.id"),
        nullable=False
    )

    media_url = db.Column(
        db.String(500),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────

    # STORY 1 → 0..* STORY_MEDIA  (many side)
    story = db.relationship(
        "Story",
        back_populates="media"
    )

    def __repr__(self):
        return f"<StoryMedia {self.id}: {self.media_url}>"
