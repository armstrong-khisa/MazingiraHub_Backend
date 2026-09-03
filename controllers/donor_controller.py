from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import distinct, func

from extensions import db
from models.donation import Donation
from models.recurring_donation import RecurringDonation
from models.user import User
from schemas.user_schema import serialize_user, validate_profile_update


donor_bp = Blueprint("donor", __name__, url_prefix="/api/donor")


def _get_current_donor():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return None
    return user


@donor_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_donor_stats():
    donor_id = int(get_jwt_identity())
    donations = Donation.query.filter_by(donor_id=donor_id)
    successful_donations = donations.filter(Donation.status == "paid")

    total_donated = db.session.query(
        func.coalesce(func.sum(Donation.amount), 0)
    ).filter(
        Donation.donor_id == donor_id,
        Donation.status == "paid",
    ).scalar()

    donation_count = successful_donations.count()
    active_recurring = db.session.query(RecurringDonation).join(
        Donation
    ).filter(
        Donation.donor_id == donor_id,
        RecurringDonation.status == "active",
    ).count()
    organizations_supported = db.session.query(
        func.count(distinct(Donation.organization_id))
    ).filter(
        Donation.donor_id == donor_id,
        Donation.status == "paid",
    ).scalar()

    return jsonify({
        "stats": {
            "totalDonated": float(total_donated or 0),
            "donationCount": donation_count,
            "activeRecurring": active_recurring,
            "organizationsSupported": organizations_supported or 0,
        }
    }), 200


@donor_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_donor_profile():
    user = _get_current_donor()
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"profile": serialize_user(user)}), 200


@donor_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_donor_profile():
    user = _get_current_donor()
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json(silent=True) or {}
    for field, value in validate_profile_update(data).items():
        setattr(user, field, value)
    db.session.commit()
    return jsonify({"profile": serialize_user(user)}), 200
