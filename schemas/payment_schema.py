import re

from flask import abort


# ── Serializer ────────────────────────────────────────────────────────────────

def serialize_payment(payment, include_donation=False):
    """Convert a Payment ORM object to a plain dict."""
    data = {
        "id": payment.id,
        "donation_id": payment.donation_id,
        "provider_payment_id": payment.provider_payment_id,
        "payment_method": payment.payment_method,
        "amount": float(payment.amount),
        "currency": payment.currency,
        "status": payment.status,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "created_at": payment.created_at.isoformat(),
        "updated_at": payment.updated_at.isoformat(),
    }

    if include_donation and payment.donation:
        data["donation"] = {
            "id": payment.donation.id,
            "amount": float(payment.donation.amount),
            "currency": payment.donation.currency,
            "organization_id": payment.donation.organization_id,
            "donor_id": payment.donation.donor_id,
        }

    return data


# ── Validators ────────────────────────────────────────────────────────────────

_PHONE_RE = re.compile(r"^2547\d{8}$")


def validate_stk_push_request(data: dict) -> dict:
    """
    Validate the STK push initiation payload.
    Returns clean dict. Calls abort(400) on failure.

    Expected fields:
        donation_id   int    required
        phone_number  str    required  (format: 2547XXXXXXXX)
    """
    errors = []

    # donation_id
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

    # phone_number — must be 2547XXXXXXXX (12 digits, starts with 2547)
    phone = (data.get("phone_number") or "").strip()
    if not phone:
        errors.append("'phone_number' is required.")
    elif not _PHONE_RE.match(phone):
        errors.append(
            "'phone_number' must be in format 2547XXXXXXXX "
            "(e.g. 254712345678)."
        )

    if errors:
        abort(400, description="; ".join(errors))

    return {
        "donation_id": donation_id,
        "phone_number": phone,
    }
