from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from extensions import db
from models.inventory import InventoryItem
from models.organization import Organization
from schemas.inventory_schema import (
    serialize_inventory_item,
    validate_create_inventory_item,
    validate_update_inventory_item,
)

inventory_bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_item_or_404(item_id: int) -> InventoryItem:
    item = db.session.get(InventoryItem, item_id)
    if not item:
        abort(404, description=f"Inventory item with id {item_id} not found.")
    return item


def _get_org_or_404(org_id: int) -> Organization:
    org = db.session.get(Organization, org_id)
    if not org:
        abort(404, description=f"Organization with id {org_id} not found.")
    return org


# ── POST /api/inventory ───────────────────────────────────────────────────────

@inventory_bp.route("", methods=["POST"])
@jwt_required()
def create_inventory_item():
    """
    Create a new inventory item for an organization.

    Body (JSON):
        organization_id  int    required
        name             str    required
        description      str    optional
        quantity         int    optional  (default 0, must be >= 0)
        unit             str    optional  e.g. "kg", "litres", "pieces"
    """
    data = request.get_json(silent=True) or {}
    cleaned = validate_create_inventory_item(data)

    _get_org_or_404(cleaned["organization_id"])

    item = InventoryItem(**cleaned)
    db.session.add(item)
    db.session.commit()

    return jsonify({
        "message": "Inventory item created successfully.",
        "inventory_item": serialize_inventory_item(item, include_org=True),
    }), 201


# ── GET /api/inventory ────────────────────────────────────────────────────────

@inventory_bp.route("", methods=["GET"])
def list_inventory_items():
    """
    List all inventory items with optional filters and pagination.

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

    query = InventoryItem.query

    if org_id:
        query = query.filter(InventoryItem.organization_id == org_id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                InventoryItem.name.ilike(like),
                InventoryItem.description.ilike(like),
            )
        )

    query = query.order_by(InventoryItem.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "inventory_items": [
            serialize_inventory_item(i, include_org=True) for i in pagination.items
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


# ── GET /api/inventory/<id> ───────────────────────────────────────────────────

@inventory_bp.route("/<int:item_id>", methods=["GET"])
def get_inventory_item(item_id):
    """Return a single inventory item by ID."""
    item = _get_item_or_404(item_id)
    return jsonify(serialize_inventory_item(item, include_org=True)), 200


# ── PATCH /api/inventory/<id> ─────────────────────────────────────────────────

@inventory_bp.route("/<int:item_id>", methods=["PATCH"])
@jwt_required()
def update_inventory_item(item_id):
    """
    Partially update an inventory item.

    Updatable fields:
        name, description, quantity, unit
    """
    item = _get_item_or_404(item_id)
    data = request.get_json(silent=True) or {}
    cleaned = validate_update_inventory_item(data)

    for field, value in cleaned.items():
        setattr(item, field, value)

    db.session.commit()

    return jsonify({
        "message": "Inventory item updated successfully.",
        "inventory_item": serialize_inventory_item(item, include_org=True),
    }), 200


# ── DELETE /api/inventory/<id> ────────────────────────────────────────────────

@inventory_bp.route("/<int:item_id>", methods=["DELETE"])
@jwt_required()
def delete_inventory_item(item_id):
    """Delete an inventory item. Returns 204 No Content."""
    item = _get_item_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return "", 204


# ── PATCH /api/inventory/<id>/adjust ─────────────────────────────────────────

@inventory_bp.route("/<int:item_id>/adjust", methods=["PATCH"])
@jwt_required()
def adjust_quantity(item_id):
    """
    Adjust inventory quantity by a delta (positive to add, negative to subtract).
    Prevents quantity from going below 0.

    Body (JSON):
        delta  int  required  (e.g. 10 to add, -5 to remove)
    """
    item = _get_item_or_404(item_id)
    data = request.get_json(silent=True) or {}

    delta = data.get("delta")
    if delta is None:
        abort(400, description="'delta' is required.")
    try:
        delta = int(delta)
    except (ValueError, TypeError):
        abort(400, description="'delta' must be an integer.")

    new_quantity = item.quantity + delta
    if new_quantity < 0:
        abort(400, description=(
            f"Adjustment would result in negative quantity "
            f"(current: {item.quantity}, delta: {delta})."
        ))

    item.quantity = new_quantity
    db.session.commit()

    return jsonify({
        "message": "Quantity adjusted successfully.",
        "inventory_item": serialize_inventory_item(item, include_org=True),
    }), 200


# ── GET /api/inventory/organization/<org_id> ──────────────────────────────────

@inventory_bp.route("/organization/<int:org_id>", methods=["GET"])
def list_inventory_by_org(org_id):
    """
    List all inventory items for a specific organization (paginated).

    Query params:
        page      int  default 1
        per_page  int  default 10 (max 100)
    """
    _get_org_or_404(org_id)

    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)

    pagination = (
        InventoryItem.query
        .filter_by(organization_id=org_id)
        .order_by(InventoryItem.name.asc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return jsonify({
        "inventory_items": [serialize_inventory_item(i) for i in pagination.items],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200
