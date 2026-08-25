from datetime import date

from flask import abort


# ── Serializer ────────────────────────────────────────────────────────────────

def serialize_project(project, include_org=False):
    """Convert a Project ORM object to a plain dict for JSON responses."""
    data = {
        "id": project.id,
        "organization_id": project.organization_id,
        "title": project.title,
        "description": project.description,
        "goal_amount": float(project.goal_amount),
        "amount_raised": float(project.amount_raised),
        "progress_percentage": project.progress_percentage(),
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "end_date": project.end_date.isoformat() if project.end_date else None,
        "completed": project.completed,
        "is_active": project.is_active(),
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }

    if include_org and project.organization:
        data["organization"] = {
            "id": project.organization.id,
            "name": project.organization.name,
        }

    return data


# ── Validators ────────────────────────────────────────────────────────────────

def _parse_date(value, field_name):
    """Parse a date string (YYYY-MM-DD). Aborts 400 on bad format."""
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        abort(400, description=f"'{field_name}' must be a valid date in YYYY-MM-DD format.")


def validate_create_project(data: dict) -> dict:
    """
    Validate payload for creating a project.
    Returns a clean dict of validated fields.
    Calls abort(400) on any validation failure.
    """
    errors = []

    # Required: title
    title = (data.get("title") or "").strip()
    if not title:
        errors.append("'title' is required.")
    elif len(title) > 200:
        errors.append("'title' must be 200 characters or fewer.")

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

    # Required: goal_amount
    goal_amount = data.get("goal_amount")
    if goal_amount is None:
        errors.append("'goal_amount' is required.")
    else:
        try:
            goal_amount = float(goal_amount)
            if goal_amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append("'goal_amount' must be a positive number.")

    # Required: start_date
    start_date_raw = data.get("start_date")
    if not start_date_raw:
        errors.append("'start_date' is required.")
        start_date = None
    else:
        start_date = _parse_date(start_date_raw, "start_date")

    # Optional: end_date
    end_date_raw = data.get("end_date")
    end_date = _parse_date(end_date_raw, "end_date") if end_date_raw else None

    # end_date must be after start_date
    if start_date and end_date and end_date <= start_date:
        errors.append("'end_date' must be after 'start_date'.")

    if errors:
        abort(400, description="; ".join(errors))

    return {
        "organization_id": org_id,
        "title": title,
        "description": (data.get("description") or "").strip() or None,
        "goal_amount": round(goal_amount, 2),
        "start_date": start_date,
        "end_date": end_date,
    }


def validate_update_project(data: dict) -> dict:
    """
    Validate payload for updating a project.
    All fields are optional — only provided fields are validated and returned.
    Calls abort(400) on any validation failure.
    """
    errors = []
    cleaned = {}

    if "title" in data:
        title = (data["title"] or "").strip()
        if not title:
            errors.append("'title' cannot be empty.")
        elif len(title) > 200:
            errors.append("'title' must be 200 characters or fewer.")
        else:
            cleaned["title"] = title

    if "description" in data:
        cleaned["description"] = (data["description"] or "").strip() or None

    if "goal_amount" in data:
        try:
            goal_amount = float(data["goal_amount"])
            if goal_amount <= 0:
                raise ValueError
            cleaned["goal_amount"] = round(goal_amount, 2)
        except (ValueError, TypeError):
            errors.append("'goal_amount' must be a positive number.")

    if "start_date" in data:
        cleaned["start_date"] = _parse_date(data["start_date"], "start_date")

    if "end_date" in data:
        val = data["end_date"]
        cleaned["end_date"] = _parse_date(val, "end_date") if val else None

    if "completed" in data:
        if not isinstance(data["completed"], bool):
            errors.append("'completed' must be a boolean (true/false).")
        else:
            cleaned["completed"] = data["completed"]

    # Cross-field: end_date must be after start_date
    s = cleaned.get("start_date")
    e = cleaned.get("end_date")
    if s and e and e <= s:
        errors.append("'end_date' must be after 'start_date'.")

    if not cleaned and not errors:
        abort(400, description="No valid fields provided for update.")

    if errors:
        abort(400, description="; ".join(errors))

    return cleaned
