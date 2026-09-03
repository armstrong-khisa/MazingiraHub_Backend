from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import func, or_

from extensions import db
from models.donation import Donation
from models.organization import Organization
from models.organization_application import OrganizationApplication
from models.user import User
from schemas.user_schema import (
	serialize_user,
	validate_admin_update,
	validate_profile_update,
)
from schemas.donation_schema import serialize_donation
from schemas.organization_schema import OrganizationSchema
from schemas.organization_application_schema import OrganizationApplicationSchema


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
organization_schema = OrganizationSchema()
application_schema = OrganizationApplicationSchema()


def _application_data(application):
	data = application_schema.dump(application)
	data.update({
		"name": application.org_name,
		"email": application.applicant.email if application.applicant else None,
		"phone": application.applicant.phone if application.applicant else None,
		"appliedAt": application.created_at.isoformat(),
	})
	return data


def _organization_data(organization):
	data = organization_schema.dump(organization)
	data["status"] = "active" if organization.approved else "inactive"
	if organization.user:
		data.update({"email": organization.user.email, "phone": organization.user.phone})
	return data


def admin_required(function):
	@jwt_required()
	def wrapper(*args, **kwargs):
		if get_jwt().get("role") != "admin":
			abort(403, description="Administrator access is required.")
		return function(*args, **kwargs)
	wrapper.__name__ = function.__name__
	return wrapper


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
	users = User.query.order_by(User.created_at.desc()).all()
	return jsonify({
		"users": [serialize_user(user) for user in users],
		"count": len(users),
	}), 200


@admin_bp.route("/users/<int:user_id>", methods=["PATCH"])
@admin_required
def update_user(user_id):
	user = db.session.get(User, user_id)
	if not user:
		abort(404, description="User not found.")

	data = request.get_json(silent=True) or {}
	for field, value in validate_admin_update(data).items():
		setattr(user, field, value)
	db.session.commit()

	return jsonify({
		"message": "User updated successfully.",
		"user": serialize_user(user),
	}), 200


@admin_bp.route("/profile", methods=["GET"])
@admin_required
def get_admin_profile():
	user = db.session.get(User, int(get_jwt_identity()))
	return jsonify({"profile": serialize_user(user)}), 200


@admin_bp.route("/profile", methods=["PUT"])
@admin_required
def update_admin_profile():
	user = db.session.get(User, int(get_jwt_identity()))
	data = request.get_json(silent=True) or {}
	for field, value in validate_profile_update(data).items():
		setattr(user, field, value)
	db.session.commit()
	return jsonify({"profile": serialize_user(user)}), 200


@admin_bp.route("/applications", methods=["GET"])
@admin_required
def list_applications():
	page = max(request.args.get("page", 1, type=int), 1)
	per_page = min(max(request.args.get("limit", 10, type=int), 1), 100)
	query = OrganizationApplication.query
	status = request.args.get("status", "").strip().lower()
	if status and status != "all":
		query = query.filter_by(status=status)
	pagination = query.order_by(OrganizationApplication.created_at.desc()).paginate(
		page=page, per_page=per_page, error_out=False
	)
	return jsonify({
		"applications": [_application_data(item) for item in pagination.items],
		"totalPages": pagination.pages or 1,
		"totalItems": pagination.total,
	}), 200


@admin_bp.route("/applications/<int:application_id>", methods=["GET"])
@admin_required
def get_application(application_id):
	application = db.session.get(OrganizationApplication, application_id)
	if not application:
		abort(404, description="Organization application not found.")
	return jsonify({"application": _application_data(application)}), 200


def _review_application(application_id, status):
	application = db.session.get(OrganizationApplication, application_id)
	if not application:
		abort(404, description="Organization application not found.")
	if application.status != "pending":
		abort(400, description=f"Application is already {application.status}.")
	application.status = status
	application.reviewed_by = int(get_jwt_identity())
	if status == "approved":
		organization = Organization(
			name=application.org_name,
			description=application.description,
			approved_by=int(get_jwt_identity()),
			user_id=application.user_id,
			approved=True,
		)
		application.applicant.role = "organization"
		db.session.add(organization)
		db.session.commit()
		return jsonify({"application": _application_data(application), "organization": _organization_data(organization)}), 200
	db.session.commit()
	return jsonify({"application": _application_data(application)}), 200


@admin_bp.route("/applications/<int:application_id>/approve", methods=["PATCH"])
@admin_required
def approve_application(application_id):
	return _review_application(application_id, "approved")


@admin_bp.route("/applications/<int:application_id>/reject", methods=["PATCH"])
@admin_required
def reject_application(application_id):
	return _review_application(application_id, "rejected")


@admin_bp.route("/organizations", methods=["GET"])
@admin_required
def list_organizations():
	page = max(request.args.get("page", 1, type=int), 1)
	per_page = min(max(request.args.get("limit", 10, type=int), 1), 100)
	query = Organization.query
	status = request.args.get("status", "").strip().lower()
	search = request.args.get("search", "").strip()
	if status == "active":
		query = query.filter_by(approved=True)
	elif status == "inactive":
		query = query.filter_by(approved=False)
	if search:
		query = query.filter(Organization.name.ilike(f"%{search}%"))
	pagination = query.order_by(Organization.name.asc()).paginate(page=page, per_page=per_page, error_out=False)
	return jsonify({
		"organizations": [_organization_data(item) for item in pagination.items],
		"totalPages": pagination.pages or 1,
		"totalItems": pagination.total,
	}), 200


@admin_bp.route("/organizations/<int:organization_id>", methods=["GET"])
@admin_required
def get_admin_organization(organization_id):
	organization = db.session.get(Organization, organization_id)
	if not organization:
		abort(404, description="Organization not found.")
	return jsonify({"organization": _organization_data(organization)}), 200


@admin_bp.route("/organizations/<int:organization_id>/status", methods=["PATCH"])
@admin_required
def update_organization_status(organization_id):
	organization = db.session.get(Organization, organization_id)
	if not organization:
		abort(404, description="Organization not found.")
	status = (request.get_json(silent=True) or {}).get("status", "").lower()
	if status not in ("active", "inactive"):
		abort(400, description="Status must be active or inactive.")
	organization.approved = status == "active"
	db.session.commit()
	return jsonify({"organization": _organization_data(organization)}), 200


@admin_bp.route("/organizations/<int:organization_id>/deactivate", methods=["PATCH"])
@admin_required
def deactivate_organization(organization_id):
	return update_organization_status(organization_id)


@admin_bp.route("/organizations/<int:organization_id>/activate", methods=["PATCH"])
@admin_required
def activate_organization(organization_id):
	return update_organization_status(organization_id)


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def get_admin_stats():
	return jsonify({"stats": {
		"totalOrganizations": Organization.query.filter_by(approved=True).count(),
		"pendingApplications": OrganizationApplication.query.filter_by(status="pending").count(),
		"totalDonors": User.query.filter_by(role="donor", status="active").count(),
		"totalDonations": float(db.session.query(func.coalesce(func.sum(Donation.amount), 0)).filter(Donation.status == "paid").scalar() or 0),
		"approvedOrganizations": Organization.query.filter_by(approved=True).count(),
		"totalUsers": User.query.count(),
		"thisMonthDonations": 0,
	}}), 200


@admin_bp.route("/donations", methods=["GET"])
@admin_required
def list_admin_donations():
	page = max(request.args.get("page", 1, type=int), 1)
	per_page = min(max(request.args.get("limit", 10, type=int), 1), 100)
	query = Donation.query
	donation_type = request.args.get("type", "").strip()
	search = request.args.get("search", "").strip()
	if donation_type and donation_type != "all":
		query = query.filter(Donation.donation_type == donation_type)
	if search:
		query = query.join(User, Donation.donor_id == User.id).join(Organization).filter(
			or_(User.full_name.ilike(f"%{search}%"), Organization.name.ilike(f"%{search}%"))
		)
	sort = request.args.get("sort", "date")
	if sort == "amount-high":
		query = query.order_by(Donation.amount.desc())
	elif sort == "amount-low":
		query = query.order_by(Donation.amount.asc())
	else:
		query = query.order_by(Donation.created_at.desc())
	pagination = query.paginate(page=page, per_page=per_page, error_out=False)
	items = []
	for donation in pagination.items:
		item = serialize_donation(donation, include_relations=True)
		item["donor"] = {"name": donation.donor.full_name, "email": donation.donor.email} if donation.donor else None
		item["createdAt"] = donation.created_at.isoformat()
		item["type"] = donation.donation_type
		items.append(item)
	return jsonify({"donations": items, "totalPages": pagination.pages or 1, "totalItems": pagination.total}), 200


@admin_bp.route("/donations/<int:donation_id>", methods=["GET"])
@admin_required
def get_admin_donation(donation_id):
	donation = db.session.get(Donation, donation_id)
	if not donation:
		abort(404, description="Donation not found.")
	return jsonify({"donation": serialize_donation(donation, include_relations=True)}), 200


@admin_bp.route("/activity", methods=["GET"])
@admin_required
def get_admin_activity():
	return jsonify({"activity": []}), 200
