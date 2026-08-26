from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from extensions import db
from models.organization import Organization
from models.story import Story, StoryMedia
from schemas.story_schema import (
    serialize_story,
    serialize_story_media,
    validate_add_media,
    validate_create_story,
    validate_update_story,
)

story_bp = Blueprint("stories", __name__, url_prefix="/api/stories")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_story_or_404(story_id: int) -> Story:
    story = db.session.get(Story, story_id)
    if not story:
        abort(404, description=f"Story with id {story_id} not found.")
    return story


def _get_org_or_404(org_id: int) -> Organization:
    org = db.session.get(Organization, org_id)
    if not org:
        abort(404, description=f"Organization with id {org_id} not found.")
    return org


def _get_media_or_404(media_id: int) -> StoryMedia:
    media = db.session.get(StoryMedia, media_id)
    if not media:
        abort(404, description=f"Story media with id {media_id} not found.")
    return media


# ── POST /api/stories ─────────────────────────────────────────────────────────

@story_bp.route("", methods=["POST"])
@jwt_required()
def create_story():
    """
    Create a new story for an organization.
    Optionally attach media URLs in the same request.

    Body (JSON):
        organization_id  int    required
        title            str    required
        content          str    required
        featured         bool   optional  (default false)
        published        bool   optional  (default false)
        media_urls       list   optional  list of URL strings
    """
    data = request.get_json(silent=True) or {}
    cleaned = validate_create_story(data)

    _get_org_or_404(cleaned["organization_id"])

    media_urls = cleaned.pop("media_urls", [])

    story = Story(**cleaned)
    db.session.add(story)
    db.session.flush()   # get story.id before adding media

    for url in media_urls:
        db.session.add(StoryMedia(story_id=story.id, media_url=url))

    db.session.commit()

    return jsonify({
        "message": "Story created successfully.",
        "story": serialize_story(story, include_org=True, include_media=True),
    }), 201


# ── GET /api/stories ──────────────────────────────────────────────────────────

@story_bp.route("", methods=["GET"])
def list_stories():
    """
    List stories with optional filters and pagination.
    By default only published stories are returned for public access.

    Query params:
        page       int   default 1
        per_page   int   default 10 (max 100)
        org_id     int   filter by organization
        featured   bool  filter featured stories  (true/false)
        published  bool  filter by published status (default: true)
        search     str   search in title or content
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    org_id = request.args.get("org_id", type=int)
    featured_param = request.args.get("featured")
    published_param = request.args.get("published", "true")
    search = request.args.get("search", "").strip()

    query = Story.query

    # Default: show published only; allow ?published=false for internal use
    if published_param.lower() == "true":
        query = query.filter(Story.published == True)
    elif published_param.lower() == "false":
        query = query.filter(Story.published == False)

    if org_id:
        query = query.filter(Story.organization_id == org_id)

    if featured_param is not None:
        if featured_param.lower() == "true":
            query = query.filter(Story.featured == True)
        elif featured_param.lower() == "false":
            query = query.filter(Story.featured == False)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Story.title.ilike(like),
                Story.content.ilike(like),
            )
        )

    query = query.order_by(Story.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "stories": [
            serialize_story(s, include_org=True, include_media=True)
            for s in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200


# ── GET /api/stories/<id> ─────────────────────────────────────────────────────

@story_bp.route("/<int:story_id>", methods=["GET"])
def get_story(story_id):
    """Return a single story by ID, including all media."""
    story = _get_story_or_404(story_id)
    return jsonify(serialize_story(story, include_org=True, include_media=True)), 200


# ── PATCH /api/stories/<id> ───────────────────────────────────────────────────

@story_bp.route("/<int:story_id>", methods=["PATCH"])
@jwt_required()
def update_story(story_id):
    """
    Partially update a story.

    Updatable fields:
        title, content, featured, published
    """
    story = _get_story_or_404(story_id)
    data = request.get_json(silent=True) or {}
    cleaned = validate_update_story(data)

    for field, value in cleaned.items():
        setattr(story, field, value)

    db.session.commit()

    return jsonify({
        "message": "Story updated successfully.",
        "story": serialize_story(story, include_org=True, include_media=True),
    }), 200


# ── DELETE /api/stories/<id> ──────────────────────────────────────────────────

@story_bp.route("/<int:story_id>", methods=["DELETE"])
@jwt_required()
def delete_story(story_id):
    """Delete a story and all its media. Returns 204 No Content."""
    story = _get_story_or_404(story_id)
    db.session.delete(story)
    db.session.commit()
    return "", 204


# ── GET /api/stories/organization/<org_id> ────────────────────────────────────

@story_bp.route("/organization/<int:org_id>", methods=["GET"])
def list_stories_by_org(org_id):
    """
    List all published stories for a specific organization (paginated).

    Query params:
        page      int  default 1
        per_page  int  default 10 (max 100)
        featured  bool filter featured only (true/false)
    """
    _get_org_or_404(org_id)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    featured_param = request.args.get("featured")

    query = (
        Story.query
        .filter_by(organization_id=org_id, published=True)
    )

    if featured_param is not None:
        if featured_param.lower() == "true":
            query = query.filter(Story.featured == True)

    pagination = (
        query
        .order_by(Story.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "stories": [
            serialize_story(s, include_media=True) for s in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200


# ── POST /api/stories/<id>/media ──────────────────────────────────────────────

@story_bp.route("/<int:story_id>/media", methods=["POST"])
@jwt_required()
def add_story_media(story_id):
    """
    Add media URLs to an existing story.

    Body (JSON):
        media_urls  list  required  list of URL strings
    """
    story = _get_story_or_404(story_id)
    data = request.get_json(silent=True) or {}
    urls = validate_add_media(data)

    new_media = []
    for url in urls:
        m = StoryMedia(story_id=story.id, media_url=url)
        db.session.add(m)
        new_media.append(m)

    db.session.commit()

    return jsonify({
        "message": f"{len(new_media)} media item(s) added.",
        "media": [serialize_story_media(m) for m in new_media],
    }), 201


# ── DELETE /api/stories/<id>/media/<media_id> ─────────────────────────────────

@story_bp.route("/<int:story_id>/media/<int:media_id>", methods=["DELETE"])
@jwt_required()
def delete_story_media(story_id, media_id):
    """Remove a specific media item from a story. Returns 204 No Content."""
    story = _get_story_or_404(story_id)
    media = _get_media_or_404(media_id)

    if media.story_id != story.id:
        abort(404, description=f"Media {media_id} does not belong to story {story_id}.")

    db.session.delete(media)
    db.session.commit()
    return "", 204
