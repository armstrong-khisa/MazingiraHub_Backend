from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from extensions import db
from models.user import User
from schemas.user_schema import (
	serialize_user,
	validate_admin_update,
)


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


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
