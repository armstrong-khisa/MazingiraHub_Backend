from decimal import Decimal, InvalidOperation

from flask import abort
from extensions import ma
from models.donation import Donation


VALID_TYPES = ("one-time", "monthly")


class DonationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Donation
        load_instance = True
        include_fk = True
        exclude = ("donor", "organization", "project", "recurring_donation", "payment")


donation_schema = DonationSchema()


def serialize_donation(donation, include_relations=False):
	data = donation_schema.dump(donation)

	if include_relations:
		data["organization"] = {
			"id": donation.organization.id,
			"name": donation.organization.name,
		} if donation.organization else None
		data["project"] = {
			"id": donation.project.id,
			"title": donation.project.title,
		} if donation.project else None

	return data


def validate_create_donation(data: dict) -> dict:
	errors = []

	organization_id = data.get("organization_id")
	try:
		organization_id = int(organization_id)
		if organization_id <= 0:
			raise ValueError
	except (ValueError, TypeError):
		errors.append("'organization_id' must be a positive integer.")

	project_id = data.get("project_id")
	if project_id is not None:
		try:
			project_id = int(project_id)
			if project_id <= 0:
				raise ValueError
		except (ValueError, TypeError):
			errors.append("'project_id' must be a positive integer.")

	try:
		amount = Decimal(str(data.get("amount")))
		if amount <= 0:
			raise ValueError
		amount = amount.quantize(Decimal("0.01"))
	except (InvalidOperation, TypeError, ValueError):
		errors.append("'amount' must be a positive number.")

	currency = (data.get("currency") or "KES").strip().upper()
	if len(currency) > 10 or not currency:
		errors.append("'currency' must be between 1 and 10 characters.")

	donation_type = (data.get("donation_type") or "one-time").strip().lower()
	if donation_type not in VALID_TYPES:
		errors.append("'donation_type' must be one-time or monthly.")

	is_anonymous = data.get("is_anonymous", False)
	if not isinstance(is_anonymous, bool):
		errors.append("'is_anonymous' must be a boolean.")

	if errors:
		abort(400, description="; ".join(errors))

	return {
		"organization_id": organization_id,
		"project_id": project_id,
		"amount": amount,
		"currency": currency,
		"donation_type": donation_type,
		"is_anonymous": is_anonymous,
	}
