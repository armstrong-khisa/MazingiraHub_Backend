from flask import abort
from extensions import ma
from models.user import User


VALID_ROLES = ("donor", "organization", "admin")
VALID_STATUSES = ("active", "inactive", "suspended")


class UserSchema(ma.SQLAlchemyAutoSchema):
	class Meta:
		model = User
		load_instance = True
		exclude = ("password_hash",)


user_schema = UserSchema()


def serialize_user(user):
	return user_schema.dump(user)


def validate_profile_update(data: dict) -> dict:
	errors = []
	cleaned = {}

	if "full_name" in data:
		full_name = (data["full_name"] or "").strip()
		if not full_name:
			errors.append("'full_name' cannot be empty.")
		elif len(full_name) > 150:
			errors.append("'full_name' must be 150 characters or fewer.")
		else:
			cleaned["full_name"] = full_name

	if "phone" in data:
		phone = (data["phone"] or "").strip() or None
		if phone and len(phone) > 30:
			errors.append("'phone' must be 30 characters or fewer.")
		else:
			cleaned["phone"] = phone

	if not cleaned and not errors:
		abort(400, description="No valid profile fields provided for update.")
	if errors:
		abort(400, description="; ".join(errors))
	return cleaned


def validate_admin_update(data: dict) -> dict:
	errors = []
	cleaned = {}

	if "role" in data:
		role = (data["role"] or "").strip().lower()
		if role not in VALID_ROLES:
			errors.append(f"'role' must be one of: {', '.join(VALID_ROLES)}.")
		else:
			cleaned["role"] = role

	if "status" in data:
		status = (data["status"] or "").strip().lower()
		if status not in VALID_STATUSES:
			errors.append(f"'status' must be one of: {', '.join(VALID_STATUSES)}.")
		else:
			cleaned["status"] = status

	if not cleaned and not errors:
		abort(400, description="No valid admin fields provided for update.")
	if errors:
		abort(400, description="; ".join(errors))
	return cleaned
