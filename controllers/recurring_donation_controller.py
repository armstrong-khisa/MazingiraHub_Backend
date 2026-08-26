from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from extensions import db
from models.donation import Donation
from models.recurring_donation import RecurringDonation
from schemas.recurring_donation_schema import (
    serialize_recurring_donation,
    validate_create_recurring_donation,
    validate_update_recurring_donation,
)

recurring_bp = Blueprint(
    "recurring_donations", __name__, url_prefix="/api/recurring-donations"
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_recurring_or_404(rd_id: int) -> RecurringDonation:
    rd = db.session.get(RecurringDonation, rd_id)
    if not rd:
        abort(404, description=f"Recurring donation with id {rd_id} not found.")
    return rd


def _get_donation_or_404(donation_id: int) -> Donation:
    d = db.session.get(Donation, donation_id)
    if not d:
        abort(404, description=f"Donation with id {donation_id} not found.")
    return d


# ── POST /api/recurring-donations ────────────────────────────────────────────

@recurring_bp.route("", methods=["POST"])
@jwt_required()
def create_recurring_donation():
    """
    Create a recurring donation schedule linked to an existing donation.
    A donation can only have one recurring schedule.

    Body (JSON):
        donation_id        int    required
        frequency          str    required  (monthly/quarterly/yearly)
        next_donation_date str    required  (YYYY-MM-DD, today or future)
    """
    data = request.get_json(silent=True) or {}
    cleaned = validate_create_recurring_donation(data)

    # Ensure the base donation exists
    _get_donation_or_404(cleaned["donation_id"])

    # Prevent duplicate recurring schedules for the same donation
    existing = RecurringDonation.query.filter_by(
        donation_id=cleaned["donation_id"]
    ).first()
    if existing:
        abort(409, description=(
            f"Donation {cleaned['donation_id']} already has a recurring schedule "
            f"(id: {existing.id})."
        ))

    rd = RecurringDonation(**cleaned)
    db.session.add(rd)
    db.session.commit()

    return jsonify({
        "message": "Recurring donation created successfully.",
        "recurring_donation": serialize_recurring_donation(rd, include_donation=True),
    }), 201


# ── GET /api/recurring-donations ─────────────────────────────────────────────

@recurring_bp.route("", methods=["GET"])
@jwt_required()
def list_recurring_donations():
    """
    List all recurring donations with optional filters and pagination.

    Query params:
        page       int   default 1
        per_page   int   default 10 (max 100)
        status     str   filter by status (active/cancelled/paused)
        frequency  str   filter by frequency (monthly/quarterly/yearly)
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    status = request.args.get("status", "").strip().lower()
    frequency = request.args.get("frequency", "").strip().lower()

    query = RecurringDonation.query

    if status:
        query = query.filter(RecurringDonation.status == status)

    if frequency:
        query = query.filter(RecurringDonation.frequency == frequency)

    query = query.order_by(RecurringDonation.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "recurring_donations": [
            serialize_recurring_donation(rd, include_donation=True)
            for rd in pagination.items
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


# ── GET /api/recurring-donations/<id> ────────────────────────────────────────

@recurring_bp.route("/<int:rd_id>", methods=["GET"])
@jwt_required()
def get_recurring_donation(rd_id):
    """Return a single recurring donation by ID."""
    rd = _get_recurring_or_404(rd_id)
    return jsonify(serialize_recurring_donation(rd, include_donation=True)), 200


# ── PATCH /api/recurring-donations/<id> ──────────────────────────────────────

@recurring_bp.route("/<int:rd_id>", methods=["PATCH"])
@jwt_required()
def update_recurring_donation(rd_id):
    """
    Partially update a recurring donation schedule.

    Updatable fields:
        frequency, next_donation_date, status
    """
    rd = _get_recurring_or_404(rd_id)
    data = request.get_json(silent=True) or {}
    cleaned = validate_update_recurring_donation(data)

    for field, value in cleaned.items():
        setattr(rd, field, value)

    db.session.commit()

    return jsonify({
        "message": "Recurring donation updated successfully.",
        "recurring_donation": serialize_recurring_donation(rd, include_donation=True),
    }), 200


# ── DELETE /api/recurring-donations/<id> ─────────────────────────────────────

@recurring_bp.route("/<int:rd_id>", methods=["DELETE"])
@jwt_required()
def delete_recurring_donation(rd_id):
    """Delete a recurring donation schedule. Returns 204 No Content."""
    rd = _get_recurring_or_404(rd_id)
    db.session.delete(rd)
    db.session.commit()
    return "", 204


# ── PATCH /api/recurring-donations/<id>/cancel ───────────────────────────────

@recurring_bp.route("/<int:rd_id>/cancel", methods=["PATCH"])
@jwt_required()
def cancel_recurring_donation(rd_id):
    """
    Cancel a recurring donation.
    Sets status to 'cancelled' and records the cancellation timestamp.
    """
    rd = _get_recurring_or_404(rd_id)

    if rd.status == "cancelled":
        abort(400, description="This recurring donation is already cancelled.")

    rd.status = "cancelled"
    rd.cancelled_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        "message": "Recurring donation cancelled.",
        "recurring_donation": serialize_recurring_donation(rd, include_donation=True),
    }), 200


# ── PATCH /api/recurring-donations/<id>/pause ────────────────────────────────

@recurring_bp.route("/<int:rd_id>/pause", methods=["PATCH"])
@jwt_required()
def pause_recurring_donation(rd_id):
    """Pause an active recurring donation."""
    rd = _get_recurring_or_404(rd_id)

    if rd.status != "active":
        abort(400, description=f"Only active recurring donations can be paused (current: {rd.status}).")

    rd.status = "paused"
    db.session.commit()

    return jsonify({
        "message": "Recurring donation paused.",
        "recurring_donation": serialize_recurring_donation(rd, include_donation=True),
    }), 200


# ── PATCH /api/recurring-donations/<id>/resume ───────────────────────────────

@recurring_bp.route("/<int:rd_id>/resume", methods=["PATCH"])
@jwt_required()
def resume_recurring_donation(rd_id):
    """Resume a paused recurring donation."""
    rd = _get_recurring_or_404(rd_id)

    if rd.status != "paused":
        abort(400, description=f"Only paused recurring donations can be resumed (current: {rd.status}).")

    rd.status = "active"
    db.session.commit()

    return jsonify({
        "message": "Recurring donation resumed.",
        "recurring_donation": serialize_recurring_donation(rd, include_donation=True),
    }), 200


# ── GET /api/recurring-donations/donation/<donation_id> ──────────────────────

@recurring_bp.route("/donation/<int:donation_id>", methods=["GET"])
@jwt_required()
def get_by_donation(donation_id):
    """Get the recurring schedule for a specific donation."""
    _get_donation_or_404(donation_id)

    rd = RecurringDonation.query.filter_by(donation_id=donation_id).first()
    if not rd:
        abort(404, description=f"No recurring schedule found for donation {donation_id}.")

    return jsonify(serialize_recurring_donation(rd, include_donation=True)), 200
