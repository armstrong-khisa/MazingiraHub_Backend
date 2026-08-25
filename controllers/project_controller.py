from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.organization import Organization
from models.project import Project
from schemas.project_schema import (
    serialize_project,
    validate_create_project,
    validate_update_project,
)

project_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


# ── Helper ────────────────────────────────────────────────────────────────────

def _get_project_or_404(project_id: int) -> Project:
    project = db.session.get(Project, project_id)
    if not project:
        abort(404, description=f"Project with id {project_id} not found.")
    return project


def _get_org_or_404(org_id: int) -> Organization:
    org = db.session.get(Organization, org_id)
    if not org:
        abort(404, description=f"Organization with id {org_id} not found.")
    return org


# ── POST /api/projects ────────────────────────────────────────────────────────

@project_bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    """
    Create a new project under an organization.
    Only the org owner or an admin should call this — 
    authorization is checked via JWT identity.

    Body (JSON):
        organization_id  int      required
        title            str      required
        description      str      optional
        goal_amount      decimal  required  (> 0)
        start_date       str      required  (YYYY-MM-DD)
        end_date         str      optional  (YYYY-MM-DD, must be > start_date)
    """
    data = request.get_json(silent=True) or {}
    cleaned = validate_create_project(data)

    # Ensure the organization exists
    _get_org_or_404(cleaned["organization_id"])

    project = Project(**cleaned)
    db.session.add(project)
    db.session.commit()

    return jsonify({
        "message": "Project created successfully.",
        "project": serialize_project(project, include_org=True),
    }), 201


# ── GET /api/projects ─────────────────────────────────────────────────────────

@project_bp.route("", methods=["GET"])
def list_projects():
    """
    List all projects with optional filters and pagination.

    Query params:
        page          int   default 1
        per_page      int   default 10  (max 100)
        org_id        int   filter by organization
        completed     bool  filter by completion status  (true/false)
        search        str   search in title or description
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    org_id = request.args.get("org_id", type=int)
    completed_param = request.args.get("completed")
    search = request.args.get("search", "").strip()

    query = Project.query

    # Filter by organization
    if org_id:
        query = query.filter(Project.organization_id == org_id)

    # Filter by completed status
    if completed_param is not None:
        if completed_param.lower() == "true":
            query = query.filter(Project.completed == True)
        elif completed_param.lower() == "false":
            query = query.filter(Project.completed == False)

    # Search by title or description
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Project.title.ilike(like_pattern),
                Project.description.ilike(like_pattern),
            )
        )

    # Order newest first
    query = query.order_by(Project.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "projects": [serialize_project(p, include_org=True) for p in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200


# ── GET /api/projects/<id> ────────────────────────────────────────────────────

@project_bp.route("/<int:project_id>", methods=["GET"])
def get_project(project_id):
    """Return a single project by ID."""
    project = _get_project_or_404(project_id)
    return jsonify(serialize_project(project, include_org=True)), 200


# ── PATCH /api/projects/<id> ──────────────────────────────────────────────────

@project_bp.route("/<int:project_id>", methods=["PATCH"])
@jwt_required()
def update_project(project_id):
    """
    Partially update a project.
    Only fields included in the body are changed.

    Updatable fields:
        title, description, goal_amount,
        start_date, end_date, completed
    """
    project = _get_project_or_404(project_id)
    data = request.get_json(silent=True) or {}
    cleaned = validate_update_project(data)

    for field, value in cleaned.items():
        setattr(project, field, value)

    db.session.commit()

    return jsonify({
        "message": "Project updated successfully.",
        "project": serialize_project(project, include_org=True),
    }), 200


# ── DELETE /api/projects/<id> ─────────────────────────────────────────────────

@project_bp.route("/<int:project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    """
    Delete a project.
    Returns 204 No Content on success.
    """
    project = _get_project_or_404(project_id)

    db.session.delete(project)
    db.session.commit()

    return "", 204


# ── GET /api/projects/organization/<org_id> ───────────────────────────────────

@project_bp.route("/organization/<int:org_id>", methods=["GET"])
def list_projects_by_org(org_id):
    """
    List all projects for a specific organization (paginated).

    Query params:
        page      int  default 1
        per_page  int  default 10 (max 100)
    """
    _get_org_or_404(org_id)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)

    pagination = (
        Project.query
        .filter_by(organization_id=org_id)
        .order_by(Project.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "projects": [serialize_project(p) for p in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200
