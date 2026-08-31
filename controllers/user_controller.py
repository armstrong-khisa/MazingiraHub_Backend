from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.user import User
from schemas.user_schema import serialize_user, validate_profile_update


user_bp = Blueprint("users", __name__, url_prefix="/api/users")


def _get_current_user():
	user = db.session.get(User, int(get_jwt_identity()))
	if not user:
		abort(404, description="User not found.")
	return user


@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
	return jsonify({"user": serialize_user(_get_current_user())}), 200


@user_bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_current_user():
	user = _get_current_user()
	data = request.get_json(silent=True) or {}
	for field, value in validate_profile_update(data).items():
		setattr(user, field, value)
	db.session.commit()
	return jsonify({
		"message": "User profile updated successfully.",
		"user": serialize_user(user),
	}), 200
