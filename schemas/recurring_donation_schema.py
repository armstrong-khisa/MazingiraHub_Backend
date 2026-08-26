from datetime import date

from flask import abort

VALID_FREQUENCIES = ("monthly", "quarterly", "yearly")
VALID_STATUSES = ("active", "cancelled", "paused")


# ── Serializer ────────────────────────────────────────────────────────────────

def serialize_recurring_donation(rd, include_donation=False):
    """Convert a RecurringDonation ORM object to a plain dict."""
    data = {
        "id": rd.id,
        "donation_id": rd.donation_id,
        "frequency": rd.frequency,
        "next_donation_date": (
            rd.next_donation_date.isoformat() if rd.next_donation_date else None
        ),
        "status": rd.status,
        "cancelled_at": rd.cancelled_at.isoformat() if rd.cancelled_at else None,
        "created_at": rd.created_at.isoformat(),
        "updated_at": rd.updated_at.isoformat(),
    }

    if include_donation and rd.donation:
        data["donation"] = {
            "id": rd.donation.id,
            "amount": float(rd.donation.amount),
            "currency": rd.donation.currency,
            "organization_id": rd.donation.organization_id,
            "donor_id": rd.donation.donor_id,
        }

    return data


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_date(value, field_name):
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        abort(400, description=f"'{field_name}' must be a valid date in YYYY-MM-DD format.")


# ── Validators ────────────────────────────────────────────────────────────────

def validate_create_recurring_donation(data: dict) -> dict:
    """
    Validate payload for creating a recurring donation schedule.
    Returns clean dict. Calls abort(400) on failure.
    """
    errors = []

    # Required: donation_id
    donation_id = data.get("donation_id")
    if donation_id is None:
        errors.append("'donation_id' is required.")
    else:
        try:
            donation_id = int(donation_id)
            if donation_id <= 0:
                raise ValueError
        except (ValueError, TypeError):
            errors.append("'donation_id' must be a positive integer.")

    # Required: frequency
    frequency = (data.get("frequency") or "").strip().lower()
    if not frequency:
        errors.append("'frequency' is required.")
    elif frequency not in VALID_FREQUENCIES:
        errors.append(f"'frequency' must be one of: {', '.join(VALID_FREQUENCIES)}.")

    # Required: next_donation_date
    next_date_raw = data.get("next_donation_date")
    if not next_date_raw:
        errors.append("'next_donation_date' is required.")
        next_date = None
    else:
        next_date = _parse_date(next_date_raw, "next_donation_date")
        if next_date and next_date < date.today():
            errors.append("'next_donation_date' must be today or in the future.")

    if errors:
        abort(400, description="; ".join(errors))

    return {
        "donation_id": donation_id,
        "frequency": frequency,
        "next_donation_date": next_date,
        "status": "active",
    }


def validate_update_recurring_donation(data: dict) -> dict:
    """
    Validate payload for updating a recurring donation.
    All fields optional. Calls abort(400) on failure.
    """
    errors = []
    cleaned = {}

    if "frequency" in data:
        frequency = (data["frequency"] or "").strip().lower()
        if frequency not in VALID_FREQUENCIES:
            errors.append(f"'frequency' must be one of: {', '.join(VALID_FREQUENCIES)}.")
        else:
            cleaned["frequency"] = frequency

    if "next_donation_date" in data:
        next_date = _parse_date(data["next_donation_date"], "next_donation_date")
        if next_date and next_date < date.today():
            errors.append("'next_donation_date' must be today or in the future.")
        else:
            cleaned["next_donation_date"] = next_date

    if "status" in data:
        status = (data["status"] or "").strip().lower()
        if status not in VALID_STATUSES:
            errors.append(f"'status' must be one of: {', '.join(VALID_STATUSES)}.")
        else:
            cleaned["status"] = status

    if not cleaned and not errors:
        abort(400, description="No valid fields provided for update.")

    if errors:
        abort(400, description="; ".join(errors))

    return cleaned
