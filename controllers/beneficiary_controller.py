from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from extensions import db
from models.beneficiary import Beneficiary
from models.organization import Organization
from schemas.beneficiary_schema import (
    serialize_beneficiary,
    validate_create_beneficiary,
    validate_update_beneficiary,
)

beneficiary_bp = Blueprint("beneficiaries", __name__, url_prefix="/api/beneficiaries")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_beneficiary_or_404(beneficiary_id: int) -> Beneficiary:
    b = db.session.get(Beneficiary, beneficiary_id)
    if not b:
        abort(404, description=f"Beneficiary with id {beneficiary_id} not found.")
    return b


def _get_org_or_404(org_id: int) -> Organization:
    org = db.session.get(Organization, org_id)
    if not org:
        abort(404, description=f"Organization with id {org_id} not found.")
    return org


# ── POST /api/beneficiaries ───────────────────────────────────────────────────

@beneficiary_bp.route("", methods=["POST"])
@jwt_required()
def create_beneficiary():
    """
    Create a new beneficiary under an organization.

    Body (JSON):
        organization_id  int   required
        name             str   required
        description      str   optional
    """
    data = request.get_json(silent=True) or {}
    cleaned = validate_create_beneficiary(data)

    _get_org_or_404(cleaned["organization_id"])

    beneficiary = Beneficiary(**cleaned)
    db.session.add(beneficiary)
    db.session.commit()

    return jsonify({
        "message": "Beneficiary created successfully.",
        "beneficiary": serialize_beneficiary(beneficiary, include_org=True),
    }), 201


# ── GET /api/beneficiaries ────────────────────────────────────────────────────

@beneficiary_bp.route("", methods=["GET"])
def list_beneficiaries():
    """
    List all beneficiaries with optional filters and pagination.

    Query params:
        page      int   default 1
        per_page  int   default 10 (max 100)
        org_id    int   filter by organization
        search    str   search in name or description
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    org_id = request.args.get("org_id", type=int)
    search = request.args.get("search", "").strip()

    query = Beneficiary.query

    if org_id:
        query = query.filter(Beneficiary.organization_id == org_id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Beneficiary.name.ilike(like),
                Beneficiary.description.ilike(like),
            )
        )

    query = query.order_by(Beneficiary.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "beneficiaries": [
            serialize_beneficiary(b, include_org=True) for b in pagination.items
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


# ── GET /api/beneficiaries/<id> ───────────────────────────────────────────────

@beneficiary_bp.route("/<int:beneficiary_id>", methods=["GET"])
def get_beneficiary(beneficiary_id):
    """Return a single beneficiary by ID."""
    b = _get_beneficiary_or_404(beneficiary_id)
    return jsonify(serialize_beneficiary(b, include_org=True)), 200


# ── PATCH /api/beneficiaries/<id> ─────────────────────────────────────────────

@beneficiary_bp.route("/<int:beneficiary_id>", methods=["PATCH"])
@jwt_required()
def update_beneficiary(beneficiary_id):
    """
    Partially update a beneficiary.

    Updatable fields:
        name, description
    """
    b = _get_beneficiary_or_404(beneficiary_id)
    data = request.get_json(silent=True) or {}
    cleaned = validate_update_beneficiary(data)

    for field, value in cleaned.items():
        setattr(b, field, value)

    db.session.commit()

    return jsonify({
        "message": "Beneficiary updated successfully.",
        "beneficiary": serialize_beneficiary(b, include_org=True),
    }), 200


# ── DELETE /api/beneficiaries/<id> ────────────────────────────────────────────

@beneficiary_bp.route("/<int:beneficiary_id>", methods=["DELETE"])
@jwt_required()
def delete_beneficiary(beneficiary_id):
    """Delete a beneficiary. Returns 204 No Content."""
    b = _get_beneficiary_or_404(beneficiary_id)
    db.session.delete(b)
    db.session.commit()
    return "", 204


# ── GET /api/beneficiaries/organization/<org_id> ──────────────────────────────

@beneficiary_bp.route("/organization/<int:org_id>", methods=["GET"])
def list_beneficiaries_by_org(org_id):
    """
    List all beneficiaries for a specific organization (paginated).

    Query params:
        page      int  default 1
        per_page  int  default 10 (max 100)
    """
    _get_org_or_404(org_id)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)

    pagination = (
        Beneficiary.query
        .filter_by(organization_id=org_id)
        .order_by(Beneficiary.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "beneficiaries": [serialize_beneficiary(b) for b in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200
