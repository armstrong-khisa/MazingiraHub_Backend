"""
controllers/payment_controller.py
──────────────────────────────────
Handles:
  - STK Push initiation  (POST /api/payments/mpesa/stk-push)
  - M-Pesa callback      (POST /api/payments/mpesa/callback)   ← public, called by Safaricom
  - STK status query     (GET  /api/payments/mpesa/query/<checkout_id>)
  - List payments        (GET  /api/payments)
  - Get one payment      (GET  /api/payments/<id>)
"""

import json
import logging
from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import jwt_required

from extensions import db
from models.donation import Donation
from models.payment import Payment
from schemas.payment_schema import serialize_payment, validate_stk_push_request
from services.daraja_service import parse_callback, query_stk_status, stk_push

logger = logging.getLogger(__name__)

payment_bp = Blueprint("payments", __name__, url_prefix="/api/payments")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_payment_or_404(payment_id: int) -> Payment:
    p = db.session.get(Payment, payment_id)
    if not p:
        abort(404, description=f"Payment with id {payment_id} not found.")
    return p


def _get_donation_or_404(donation_id: int) -> Donation:
    d = db.session.get(Donation, donation_id)
    if not d:
        abort(404, description=f"Donation with id {donation_id} not found.")
    return d


# ── POST /api/payments/mpesa/stk-push ────────────────────────────────────────

@payment_bp.route("/mpesa/stk-push", methods=["POST"])
@jwt_required()
def initiate_stk_push():
    """
    Initiate an M-Pesa STK Push for a donation.

    Body (JSON):
        donation_id   int   required  — must be an existing pending donation
        phone_number  str   required  — format: 2547XXXXXXXX

    Flow:
        1. Validate input
        2. Load donation (must be pending)
        3. Call Daraja STK Push API
        4. Create a Payment record with status=pending
        5. Return the CheckoutRequestID so the client can poll status

    The donor receives an M-Pesa PIN prompt on their phone.
    Safaricom calls our callback URL when they confirm or cancel.
    """
    data = request.get_json(silent=True) or {}
    cleaned = validate_stk_push_request(data)

    donation = _get_donation_or_404(cleaned["donation_id"])

    # Only initiate payment for pending donations
    if donation.status != "pending":
        abort(400, description=(
            f"Donation {donation.id} is already '{donation.status}'. "
            "Only pending donations can be paid."
        ))

    # Prevent duplicate pending payments
    existing = Payment.query.filter_by(
        donation_id=donation.id, status="pending"
    ).first()
    if existing:
        abort(409, description=(
            f"A pending payment already exists for donation {donation.id} "
            f"(payment id: {existing.id}, "
            f"checkout: {existing.provider_payment_id})."
        ))

    try:
        result = stk_push(
            phone_number=cleaned["phone_number"],
            amount=int(float(donation.amount)),
            account_ref=f"DON{donation.id}",
            description="MazingiraHub",
        )
    except RuntimeError as e:
        logger.error("STK push error: %s", e)
        abort(502, description=f"M-Pesa request failed: {str(e)}")

    # ResponseCode "0" means the request was accepted by Safaricom
    if result.get("ResponseCode") != "0":
        abort(502, description=(
            f"M-Pesa rejected the request: {result.get('ResponseDescription')}"
        ))

    checkout_request_id = result.get("CheckoutRequestID")

    # Create a payment record
    payment = Payment(
        donation_id=donation.id,
        provider_payment_id=checkout_request_id,
        payment_method="mpesa",
        amount=donation.amount,
        currency=donation.currency,
        status="pending",
    )
    db.session.add(payment)
    db.session.commit()

    return jsonify({
        "message": "STK Push sent. Ask the donor to check their phone.",
        "checkout_request_id": checkout_request_id,
        "merchant_request_id": result.get("MerchantRequestID"),
        "customer_message": result.get("CustomerMessage"),
        "payment": serialize_payment(payment),
    }), 200


# ── POST /api/payments/mpesa/callback ─────────────────────────────────────────

@payment_bp.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    """
    M-Pesa STK Push callback — called directly by Safaricom.
    This endpoint must be PUBLIC (no JWT) and reachable via ngrok.

    Safaricom always expects HTTP 200 with {"ResultCode": 0}.
    Any other response triggers retries.

    Flow:
        1. Parse callback payload
        2. Find the Payment by CheckoutRequestID
        3. Update Payment status (paid/cancelled)
        4. Update Donation status to match
        5. If paid, update project.amount_raised
    """
    callback_data = request.get_json(silent=True) or {}
    logger.info("M-Pesa callback received: %s", json.dumps(callback_data))

    parsed = parse_callback(callback_data)
    checkout_id = parsed.get("checkout_request_id")

    if not checkout_id:
        # Malformed callback — still return 200 so Safaricom stops retrying
        logger.warning("Callback missing CheckoutRequestID")
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200

    payment = Payment.query.filter_by(provider_payment_id=checkout_id).first()

    if not payment:
        logger.warning("Payment not found for checkout_id: %s", checkout_id)
        return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200

    # Store the raw callback for auditing
    payment.raw_callback = json.dumps(callback_data)

    if parsed["success"]:
        was_paid = payment.status == "paid"
        payment.status = "paid"
        payment.paid_at = datetime.now(timezone.utc)

        # Update donation status
        payment.donation.status = "paid"
        payment.donation.payment_ref = parsed.get("mpesa_receipt")
        payment.donation.payment_method = "mpesa"

        # Update project.amount_raised if the donation is linked to a project
        project = payment.donation.project
        if project and not was_paid:
            project.amount_raised = (
                float(project.amount_raised) + float(payment.amount)
            )
            # Auto-complete project if goal is reached
            if float(project.amount_raised) >= float(project.goal_amount):
                project.completed = True

    else:
        payment.status = "cancelled"
        payment.donation.status = "cancelled"
        logger.info(
            "STK push failed for checkout %s: %s",
            checkout_id,
            parsed["result_desc"],
        )

    db.session.commit()

    # Always return 200 to Safaricom
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


# ── GET /api/payments/mpesa/query/<checkout_id> ───────────────────────────────

@payment_bp.route("/mpesa/query/<string:checkout_id>", methods=["GET"])
@jwt_required()
def query_payment_status(checkout_id):
    """
    Query the live status of an STK push from Daraja.
    Use this to poll after initiating a push if the callback hasn't arrived.
    """
    try:
        result = query_stk_status(checkout_id)
    except RuntimeError as e:
        abort(502, description=str(e))

    # Reconcile the local record while polling so callback timing cannot leave
    # the frontend showing a different status from donation history.
    payment = Payment.query.filter_by(provider_payment_id=checkout_id).first()
    result_code = result.get("ResultCode", result.get("ResponseCode"))
    if payment and result_code is not None:
        result_code = str(result_code)
        if result_code == "0":
            was_paid = payment.status == "paid"
            payment.status = "paid"
            payment.paid_at = payment.paid_at or datetime.now(timezone.utc)
            payment.donation.status = "paid"
            if payment.donation.project and not was_paid:
                project = payment.donation.project
                project.amount_raised = float(project.amount_raised) + float(payment.amount)
                if float(project.amount_raised) >= float(project.goal_amount):
                    project.completed = True
        elif result_code != "1037":
            payment.status = "cancelled"
            payment.donation.status = "cancelled"
        db.session.commit()

    return jsonify({
        "daraja_response": result,
        "local_payment": serialize_payment(payment) if payment else None,
    }), 200


# ── GET /api/payments ─────────────────────────────────────────────────────────

@payment_bp.route("", methods=["GET"])
@jwt_required()
def list_payments():
    """
    List all payments with optional filters and pagination.

    Query params:
        page       int   default 1
        per_page   int   default 10 (max 100)
        status     str   filter by status (pending/paid/cancelled)
        method     str   filter by payment_method (mpesa/stripe/paypal)
    """
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    status = request.args.get("status", "").strip()
    method = request.args.get("method", "").strip()

    query = Payment.query

    if status:
        query = query.filter(Payment.status == status)
    if method:
        query = query.filter(Payment.payment_method == method)

    query = query.order_by(Payment.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "payments": [
            serialize_payment(p, include_donation=True) for p in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": pagination.pages,
            "total_items": pagination.total,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200


# ── GET /api/payments/<id> ────────────────────────────────────────────────────

@payment_bp.route("/<int:payment_id>", methods=["GET"])
@jwt_required()
def get_payment(payment_id):
    """Return a single payment by ID."""
    p = _get_payment_or_404(payment_id)
    return jsonify(serialize_payment(p, include_donation=True)), 200


# ── GET /api/payments/donation/<donation_id> ──────────────────────────────────

@payment_bp.route("/donation/<int:donation_id>", methods=["GET"])
@jwt_required()
def get_payment_by_donation(donation_id):
    """Get the payment record for a specific donation."""
    _get_donation_or_404(donation_id)

    payment = Payment.query.filter_by(donation_id=donation_id).first()
    if not payment:
        abort(404, description=f"No payment found for donation {donation_id}.")

    return jsonify(serialize_payment(payment, include_donation=True)), 200
