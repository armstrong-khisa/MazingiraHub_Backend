from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import distinct, func, or_

from extensions import db
from models.beneficiary import Beneficiary
from models.donation import Donation
from models.organization import Organization
from models.story import Story
from models.user import User


organization_dashboard_bp = Blueprint(
    "organization_dashboard", __name__, url_prefix="/api/organization"
)


def _current_organization():
    organization = Organization.query.filter_by(
        user_id=int(get_jwt_identity())
    ).first()
    if not organization:
        abort(404, description="Organization profile not found.")
    return organization


def _donation_data(donation):
    return {
        "id": donation.id,
        "amount": float(donation.amount),
        "currency": donation.currency,
        "type": donation.donation_type,
        "donation_type": donation.donation_type,
        "status": donation.status,
        "createdAt": donation.created_at.isoformat(),
        "created_at": donation.created_at.isoformat(),
        "donor": {
            "id": donation.donor.id,
            "name": donation.donor.full_name,
            "email": donation.donor.email,
        } if donation.donor else None,
        "organization": {
            "id": donation.organization.id,
            "name": donation.organization.name,
        },
    }


@organization_dashboard_bp.route("/donors", methods=["GET"])
@jwt_required()
def list_organization_donors():
    organization = _current_organization()
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("limit", 10, type=int), 1), 100)
    search = request.args.get("search", "").strip()

    donor_ids = db.session.query(Donation.donor_id).filter(
        Donation.organization_id == organization.id
    ).distinct().subquery()
    query = User.query.filter(User.id.in_(donor_ids))
    if search:
        query = query.filter(
            or_(User.full_name.ilike(f"%{search}%"), User.email.ilike(f"%{search}%"))
        )

    pagination = query.order_by(User.full_name.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    donors = []
    for donor in pagination.items:
        donor_donations = Donation.query.filter_by(
            organization_id=organization.id, donor_id=donor.id, status="success"
        )
        donors.append({
            "id": donor.id,
            "name": donor.full_name,
            "email": donor.email,
            "phone": donor.phone,
            "donationCount": donor_donations.count(),
            "totalDonated": float(db.session.query(func.coalesce(func.sum(Donation.amount), 0)).filter(
                Donation.organization_id == organization.id,
                Donation.donor_id == donor.id,
                Donation.status == "success",
            ).scalar() or 0),
        })

    return jsonify({
        "donors": donors,
        "totalPages": pagination.pages or 1,
        "totalItems": pagination.total,
    }), 200


@organization_dashboard_bp.route("/donors/<int:donor_id>", methods=["GET"])
@jwt_required()
def get_organization_donor(donor_id):
    organization = _current_organization()
    donor = User.query.join(Donation, Donation.donor_id == User.id).filter(
        Donation.organization_id == organization.id, User.id == donor_id
    ).first()
    if not donor:
        abort(404, description="Donor not found.")
    return jsonify({"donor": {
        "id": donor.id, "name": donor.full_name, "email": donor.email, "phone": donor.phone
    }}), 200


@organization_dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_organization_stats():
    organization = _current_organization()
    donations = Donation.query.filter_by(organization_id=organization.id)
    successful = donations.filter_by(status="success")
    return jsonify({"stats": {
        "totalDonations": float(db.session.query(func.coalesce(func.sum(Donation.amount), 0)).filter(
            Donation.organization_id == organization.id, Donation.status == "success"
        ).scalar() or 0),
        "donationCount": successful.count(),
        "activeDonors": db.session.query(func.count(distinct(Donation.donor_id))).filter(
            Donation.organization_id == organization.id, Donation.status == "success"
        ).scalar() or 0,
        "publishedStories": Story.query.filter_by(organization_id=organization.id, published=True).count(),
        "beneficiaries": Beneficiary.query.filter_by(organization_id=organization.id).count(),
    }}), 200


@organization_dashboard_bp.route("/donation-stats", methods=["GET"])
@jwt_required()
def get_organization_donation_stats():
    organization = _current_organization()
    donations = Donation.query.filter_by(organization_id=organization.id, status="success")
    amounts = [donation.amount for donation in donations.all()]
    return jsonify({"stats": {
        "averageDonation": float(sum(amounts) / len(amounts)) if amounts else 0,
        "largestDonation": float(max(amounts)) if amounts else 0,
        "thisMonth": 0,
        "recurringCount": Donation.query.filter_by(
            organization_id=organization.id, donation_type="monthly", status="success"
        ).count(),
    }}), 200


@organization_dashboard_bp.route("/donations", methods=["GET"])
@jwt_required()
def list_organization_donations():
    organization = _current_organization()
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("limit", 10, type=int), 1), 100)
    query = Donation.query.filter_by(organization_id=organization.id)
    donation_type = request.args.get("type", "").strip()
    if donation_type and donation_type != "all":
        query = query.filter(Donation.donation_type == donation_type)
    sort = request.args.get("sort", "date")
    if sort == "amount-high":
        query = query.order_by(Donation.amount.desc())
    elif sort == "amount-low":
        query = query.order_by(Donation.amount.asc())
    else:
        query = query.order_by(Donation.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "donations": [_donation_data(donation) for donation in pagination.items],
        "totalPages": pagination.pages or 1,
        "totalItems": pagination.total,
    }), 200


@organization_dashboard_bp.route("/donations/stats", methods=["GET"])
@jwt_required()
def get_organization_donations_stats():
    return get_organization_donation_stats()
