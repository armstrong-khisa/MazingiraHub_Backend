from flask import abort


# ── Serializer ────────────────────────────────────────────────────────────────

def serialize_beneficiary(beneficiary, include_org=False):
    """Convert a Beneficiary ORM object to a plain dict."""
    data = {
        "id": beneficiary.id,
        "organization_id": beneficiary.organization_id,
        "name": beneficiary.name,
        "description": beneficiary.description,
        "created_at": beneficiary.created_at.isoformat(),
        "updated_at": beneficiary.updated_at.isoformat(),
    }

    if include_org and beneficiary.organization:
        data["organization"] = {
            "id": beneficiary.organization.id,
            "name": beneficiary.organization.name,
        }

    return data


# ── Validators ────────────────────────────────────────────────────────────────

def validate_create_beneficiary(data: dict) -> dict:
    """
    Validate payload for creating a beneficiary.
    Returns clean dict. Calls abort(400) on failure.
    """
    errors = []

    # Required: organization_id
    org_id = data.get("organization_id")
    if org_id is None:
        errors.append("'organization_id' is required.")
    else:
        try:
            org_id = int(org_id)
            if org_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append("'organization_id' must be a positive integer.")

    # Required: name
    name = (data.get("name") or "").strip()
    if not name:
        errors.append("'name' is required.")
    elif len(name) > 200:
        errors.append("'name' must be 200 characters or fewer.")

    if errors:
        abort(400, description="; ".join(errors))

    return {
        "organization_id": org_id,
        "name": name,
        "description": (data.get("description") or "").strip() or None,
    }


def validate_update_beneficiary(data: dict) -> dict:
    """
    Validate payload for updating a beneficiary.
    All fields optional. Calls abort(400) on failure.
    """
    errors = []
    cleaned = {}

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            errors.append("'name' cannot be empty.")
        elif len(name) > 200:
            errors.append("'name' must be 200 characters or fewer.")
        else:
            cleaned["name"] = name

    if "description" in data:
        cleaned["description"] = (data["description"] or "").strip() or None

    if not cleaned and not errors:
        abort(400, description="No valid fields provided for update.")

    if errors:
        abort(400, description="; ".join(errors))

    return cleaned
