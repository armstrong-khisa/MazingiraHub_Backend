from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.donation import Donation
from models.organization import Organization
from models.project import Project
from schemas.donation_schema import serialize_donation, validate_create_donation


donation_bp = Blueprint("donations", __name__, url_prefix="/api/donations")


def _get_donation_or_404(donation_id):
	donation = db.session.get(Donation, donation_id)
	if not donation:
		abort(404, description=f"Donation with id {donation_id} not found.")
	return donation


@donation_bp.route("", methods=["POST"])
@jwt_required()
def create_donation():
	data = request.get_json(silent=True) or {}
	cleaned = validate_create_donation(data)

	organization = db.session.get(Organization, cleaned["organization_id"])
	if not organization:
		abort(404, description="Organization not found.")

	if cleaned["project_id"] is not None:
		project = db.session.get(Project, cleaned["project_id"])
		if not project or project.organization_id != organization.id:
			abort(404, description="Project not found for this organization.")

	donation = Donation(
		donor_id=int(get_jwt_identity()),
		status="pending",
		**cleaned,
	)
	db.session.add(donation)
	db.session.commit()

	return jsonify({
		"message": "Donation created successfully.",
		"donation": serialize_donation(donation, include_relations=True),
	}), 201


@donation_bp.route("", methods=["GET"])
@jwt_required()
def list_donations():
	donor_id = int(get_jwt_identity())
	status = request.args.get("status", "").strip().lower()
	if status and status not in {"pending", "paid", "cancelled"}:
		abort(400, description="Status must be pending, paid, or cancelled.")

	query = Donation.query.filter_by(donor_id=donor_id)
	if status:
		query = query.filter(Donation.status == status)
	donations = (
		query
		.order_by(Donation.created_at.desc())
		.all()
	)
	return jsonify({
		"donations": [serialize_donation(d, include_relations=True) for d in donations],
		"count": len(donations),
	}), 200


@donation_bp.route("/<int:donation_id>", methods=["GET"])
@jwt_required()
def get_donation(donation_id):
	donation = _get_donation_or_404(donation_id)
	if donation.donor_id != int(get_jwt_identity()):
		abort(403, description="You do not have permission to view this donation.")
	return jsonify(serialize_donation(donation, include_relations=True)), 200
