"""
controllers/stats_controller.py
────────────────────────────────
Public stats endpoint consumed by the homepage.
No authentication required.

GET /api/stats
→ {
    "stats": {
      "totalOrganizations":   int,
      "totalDonations":       float,   (KES, successful donations only)
      "totalDonors":          int,     (unique donors)
      "approvedOrganizations": int
    },
    "cached_at": "ISO-8601 timestamp"
  }

Caching:
  Results are cached in-memory for CACHE_TTL_SECONDS (default 5 min).
  No extra dependency needed — stdlib time module only.
  On the first request after the TTL expires the DB is queried again.
"""

import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify
from sqlalchemy import func

from extensions import db
from models.donation import Donation
from models.organization import Organization
from models.user import User

stats_bp = Blueprint("stats", __name__, url_prefix="/api")

# ── Simple in-memory cache ────────────────────────────────────────────────────
CACHE_TTL_SECONDS = 300          # 5 minutes
_cache: dict = {
    "data": None,
    "expires_at": 0.0,
    "cached_at": None,
}


def _build_stats() -> dict:
    """
    Run all aggregate queries against the DB and return the stats dict.
    All queries use DB-level aggregation — no Python-side iteration.
    """

    # Total number of organizations (all)
    total_orgs = db.session.query(func.count(Organization.id)).scalar() or 0

    # Approved organizations
    approved_orgs = (
        db.session.query(func.count(Organization.id))
        .filter(Organization.approved == True)   # noqa: E712
        .scalar() or 0
    )

    # Total donations amount — only count donations with status='paid'
    total_donations = (
        db.session.query(func.coalesce(func.sum(Donation.amount), 0))
        .filter(Donation.status == "paid")
        .scalar()
    )
    total_donations = float(total_donations or 0)

    # Total unique donors — count distinct donor_id across all donations
    total_donors = (
        db.session.query(func.count(func.distinct(Donation.donor_id)))
        .scalar() or 0
    )

    return {
        "totalOrganizations": total_orgs,
        "totalDonations": total_donations,
        "totalDonors": total_donors,
        "approvedOrganizations": approved_orgs,
    }


# ── Route ─────────────────────────────────────────────────────────────────────

@stats_bp.route("/stats", methods=["GET"])
def get_stats():
    """
    Public homepage stats.
    No authentication required.
    Returns cached result for up to 5 minutes.
    """
    now = time.monotonic()

    # Serve from cache if still fresh
    if _cache["data"] is not None and now < _cache["expires_at"]:
        return jsonify({
            "stats": _cache["data"],
            "cached_at": _cache["cached_at"],
        }), 200

    # Cache miss — query DB
    stats_data = _build_stats()
    cached_at = datetime.now(timezone.utc).isoformat()

    # Update cache
    _cache["data"] = stats_data
    _cache["expires_at"] = now + CACHE_TTL_SECONDS
    _cache["cached_at"] = cached_at

    return jsonify({
        "stats": stats_data,
        "cached_at": cached_at,
    }), 200
