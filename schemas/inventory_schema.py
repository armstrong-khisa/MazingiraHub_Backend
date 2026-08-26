from flask import abort


# ── Serializer ────────────────────────────────────────────────────────────────

def serialize_inventory_item(item, include_org=False):
    """Convert an InventoryItem ORM object to a plain dict."""
    data = {
        "id": item.id,
        "organization_id": item.organization_id,
        "name": item.name,
        "description": item.description,
        "quantity": item.quantity,
        "unit": item.unit,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }

    if include_org and item.organization:
        data["organization"] = {
            "id": item.organization.id,
            "name": item.organization.name,
        }

    return data


# ── Validators ────────────────────────────────────────────────────────────────

def validate_create_inventory_item(data: dict) -> dict:
    """
    Validate payload for creating an inventory item.
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

    # Optional: quantity (defaults to 0)
    quantity = data.get("quantity", 0)
    try:
        quantity = int(quantity)
        if quantity < 0:
            raise ValueError
    except (ValueError, TypeError):
        errors.append("'quantity' must be a non-negative integer.")

    # Optional: unit
    unit = (data.get("unit") or "").strip() or None
    if unit and len(unit) > 50:
        errors.append("'unit' must be 50 characters or fewer.")

    if errors:
        abort(400, description="; ".join(errors))

    return {
        "organization_id": org_id,
        "name": name,
        "description": (data.get("description") or "").strip() or None,
        "quantity": quantity,
        "unit": unit,
    }


def validate_update_inventory_item(data: dict) -> dict:
    """
    Validate payload for updating an inventory item.
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

    if "quantity" in data:
        try:
            qty = int(data["quantity"])
            if qty < 0:
                raise ValueError
            cleaned["quantity"] = qty
        except (ValueError, TypeError):
            errors.append("'quantity' must be a non-negative integer.")

    if "unit" in data:
        unit = (data["unit"] or "").strip() or None
        if unit and len(unit) > 50:
            errors.append("'unit' must be 50 characters or fewer.")
        else:
            cleaned["unit"] = unit

    if not cleaned and not errors:
        abort(400, description="No valid fields provided for update.")

    if errors:
        abort(400, description="; ".join(errors))

    return cleaned
