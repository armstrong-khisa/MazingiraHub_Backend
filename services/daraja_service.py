"""
services/daraja_service.py
──────────────────────────
All Safaricom Daraja API logic lives here.
The controller stays clean — it just calls these functions.

Environment variables required (set in .env):
    MPESA_CONSUMER_KEY
    MPESA_CONSUMER_SECRET
    MPESA_SHORTCODE
    MPESA_PASSKEY
    MPESA_ENVIRONMENT   sandbox | production
    MPESA_CALLBACK_URL  your ngrok HTTPS URL + /api/payments/mpesa/callback
"""

import base64
import os
from datetime import datetime, timezone

import requests


# ── Base URLs ─────────────────────────────────────────────────────────────────

_SANDBOX_BASE = "https://sandbox.safaricom.co.ke"
_PRODUCTION_BASE = "https://api.safaricom.co.ke"


def _base_url() -> str:
    env = os.getenv("MPESA_ENVIRONMENT", "sandbox").lower()
    return _PRODUCTION_BASE if env == "production" else _SANDBOX_BASE


# ── OAuth token ───────────────────────────────────────────────────────────────

def get_access_token() -> str:
    """
    Fetch a short-lived OAuth2 access token from Daraja.
    Raises RuntimeError if the request fails.
    """
    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")

    if not consumer_key or not consumer_secret:
        raise RuntimeError(
            "MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be set in .env"
        )

    url = f"{_base_url()}/oauth/v1/generate?grant_type=client_credentials"

    response = requests.get(
        url,
        auth=(consumer_key, consumer_secret),
        timeout=15,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Daraja token request failed: {response.status_code} {response.text}"
        )

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in Daraja response: {data}")

    return token


# ── Password ──────────────────────────────────────────────────────────────────

def _generate_password(shortcode: str, passkey: str, timestamp: str) -> str:
    """
    Base64-encode(shortcode + passkey + timestamp).
    This is the STK push password Safaricom expects.
    """
    raw = f"{shortcode}{passkey}{timestamp}"
    return base64.b64encode(raw.encode()).decode()


# ── STK Push ──────────────────────────────────────────────────────────────────

def stk_push(phone_number: str, amount: int, account_ref: str, description: str) -> dict:
    """
    Initiate an M-Pesa STK Push (Lipa Na M-Pesa Online).

    Args:
        phone_number  Kenyan number in 2547XXXXXXXX format
        amount        Integer amount in KES (M-Pesa does not accept decimals)
        account_ref   Short reference shown on the M-Pesa prompt (≤12 chars)
        description   Transaction description shown to user (≤13 chars)

    Returns:
        Daraja API response dict containing:
            MerchantRequestID, CheckoutRequestID,
            ResponseCode, ResponseDescription, CustomerMessage

    Raises:
        RuntimeError on network or API errors.
    """
    shortcode = os.getenv("MPESA_SHORTCODE", "174379")
    passkey = os.getenv("MPESA_PASSKEY")
    callback_url = os.getenv("MPESA_CALLBACK_URL")

    if not passkey:
        raise RuntimeError("MPESA_PASSKEY must be set in .env")
    if not callback_url:
        raise RuntimeError("MPESA_CALLBACK_URL must be set in .env")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    password = _generate_password(shortcode, passkey, timestamp)

    token = get_access_token()

    url = f"{_base_url()}/mpesa/stkpush/v1/processrequest"

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),          # must be integer
        "PartyA": phone_number,          # payer's number
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": account_ref[:12],
        "TransactionDesc": description[:13],
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"STK push failed: {response.status_code} {response.text}"
        )

    return response.json()


# ── STK Push Query (check payment status) ────────────────────────────────────

def query_stk_status(checkout_request_id: str) -> dict:
    """
    Query the status of an STK push request.

    Args:
        checkout_request_id  The CheckoutRequestID returned by stk_push()

    Returns:
        Daraja API response dict.
    """
    shortcode = os.getenv("MPESA_SHORTCODE", "174379")
    passkey = os.getenv("MPESA_PASSKEY")

    if not passkey:
        raise RuntimeError("MPESA_PASSKEY must be set in .env")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    password = _generate_password(shortcode, passkey, timestamp)

    token = get_access_token()

    url = f"{_base_url()}/mpesa/stkpushquery/v1/query"

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"STK query failed: {response.status_code} {response.text}"
        )

    return response.json()


# ── Callback parser ───────────────────────────────────────────────────────────

def parse_callback(callback_data: dict) -> dict:
    """
    Parse the raw M-Pesa STK Push callback payload into a clean dict.

    Returns a dict with keys:
        success           bool
        checkout_request_id  str
        result_code       int
        result_desc       str
        mpesa_receipt     str or None   (M-Pesa transaction ID)
        amount            float or None
        phone_number      str or None
        transaction_date  str or None
    """
    body = callback_data.get("Body", {})
    stk_callback = body.get("stkCallback", {})

    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc", "")
    checkout_request_id = stk_callback.get("CheckoutRequestID", "")
    success = str(result_code) == "0"

    mpesa_receipt = None
    amount = None
    phone_number = None
    transaction_date = None

    if success:
        items = (
            stk_callback
            .get("CallbackMetadata", {})
            .get("Item", [])
        )
        # Build a quick lookup dict from the Item list
        meta = {item["Name"]: item.get("Value") for item in items}
        mpesa_receipt = meta.get("MpesaReceiptNumber")
        amount = meta.get("Amount")
        phone_number = str(meta.get("PhoneNumber", ""))
        transaction_date = str(meta.get("TransactionDate", ""))

    return {
        "success": success,
        "checkout_request_id": checkout_request_id,
        "result_code": result_code,
        "result_desc": result_desc,
        "mpesa_receipt": mpesa_receipt,
        "amount": amount,
        "phone_number": phone_number,
        "transaction_date": transaction_date,
    }
