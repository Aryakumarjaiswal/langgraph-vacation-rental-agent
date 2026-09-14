"""Twilio voice handoff when a guest asks for human support.

Functions in this module:
  - wants_human_support   : detect escalation phrases in guest text
  - handoff_message       : friendly chat reply after a dial attempt
  - place_voice_call      : Twilio REST outbound call to EXECUTIVE_PHONE
  - handoff_twiml         : XML spoken when support answers the phone
  - handoff_call_url      : webhook URL Twilio fetches for that TwiML
"""

from __future__ import annotations

import html
import os
import re
from urllib.parse import quote

import httpx
from dotenv import load_dotenv

load_dotenv()

EXECUTIVE_PHONE = (os.getenv("EXECUTIVE_PHONE") or "").strip()
TWILIO_ACCOUNT_SID = (os.getenv("TWILIO_ACCOUNT_SID") or "").strip()
TWILIO_AUTH_TOKEN = (os.getenv("TWILIO_AUTH_TOKEN") or "").strip()
TWILIO_FROM_NUMBER = (os.getenv("TWILIO_FROM_NUMBER") or "").strip()
API_BASE_URL = (os.getenv("API_BASE_URL") or "http://127.0.0.1:8000").strip().rstrip("/")

SUPPORT_PHRASES = (
    "customer support",
    "customer service",
    "talk to support",
    "talk to customer",
    "speak to support",
    "speak to a person",
    "speak to someone",
    "talk to someone",
    "talk to an executive",
    "talk to executive",
    "call executive",
    "call support",
    "call customer",
    "human agent",
    "real person",
    "live agent",
    "connect me",
    "transfer me",
    "transfer to",
)


def _phone_digits(phone: str) -> str:
    return re.sub(r"\D", "", phone or "")


def e164(phone: str = "") -> str:
    """Normalize to E.164 (+91 for 10-digit Indian numbers)."""
    digits = _phone_digits(phone or EXECUTIVE_PHONE)
    if not digits:
        return ""
    if not digits.startswith("91") and len(digits) == 10:
        digits = "91" + digits
    return f"+{digits}"


def twilio_configured() -> bool:
    return bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM_NUMBER)


def wants_human_support(text: str) -> bool:
    lowered = (text or "").lower()
    return any(phrase in lowered for phrase in SUPPORT_PHRASES)


def handoff_message(reason: str, dial: dict[str, str] | None = None) -> str:
    """Guest-facing reply based on whether Twilio placed the call."""
    dial = dial or {}
    status = dial.get("dial_status", "")
    if status == "dialed":
        return (
            "I'm connecting you with our support team now. "
            "They should receive a call shortly. Thanks for waiting."
        )
    if status == "failed":
        return (
            "I tried to reach our support team by phone just now, "
            "but the call could not be completed. Please try again in a moment, "
            "or ask me another question about your stay."
        )
    if status == "not_configured":
        return (
            "I've noted your request to speak with support. "
            "A teammate will follow up as soon as calling is available."
        )
    return (
        "I've noted your request to speak with our support team. "
        "Someone will help you shortly."
    )


def _spaced_digits(value: str) -> str:
    """Property IDs read digit-by-digit in Twilio TTS (930 -> '9 3 0')."""
    return " ".join(ch for ch in str(value) if ch.isdigit())


def handoff_twiml(property_id: str, reason: str) -> str:
    """TwiML played to support when they answer the outbound call."""
    prop = _spaced_digits(property_id) or "unknown"
    issue = html.escape((reason or "support request")[:300], quote=False)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">
    Hello, this is Stay Ops support.
    A guest at property {prop} needs assistance.
    Their reported issue is: {issue}.
    Thank you.
  </Say>
</Response>"""


def handoff_call_url(property_id: str, reason: str) -> str:
    """Public FastAPI URL Twilio requests when the call connects."""
    params = (
        f"property_id={quote(str(property_id or ''))}"
        f"&reason={quote(reason or 'support request')}"
    )
    return f"{API_BASE_URL}/twilio/handoff?{params}"


def _twilio_failure_detail(response: httpx.Response) -> str:
    body = (response.text or "")[:400]
    try:
        payload = response.json()
        return str(payload.get("message") or body)[:400]
    except Exception:
        return body


def place_voice_call(reason: str, property_id: str = "") -> dict[str, str]:
    """Ring EXECUTIVE_PHONE via Twilio; return dial_status + call SID or error."""
    to_number = e164()
    from_number = e164(TWILIO_FROM_NUMBER)
    if not to_number:
        return {"dial_status": "missing_phone", "dial_detail": ""}
    if not twilio_configured() or not from_number:
        return {"dial_status": "not_configured", "dial_detail": ""}

    twilio_api = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    try:
        response = httpx.post(
            twilio_api,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data={
                "To": to_number,
                "From": from_number,
                "Url": handoff_call_url(property_id, reason),
            },
            timeout=20,
        )
        if response.status_code >= 400:
            return {
                "dial_status": "failed",
                "dial_detail": _twilio_failure_detail(response),
            }
        sid = response.json().get("sid", "")
        return {"dial_status": "dialed", "dial_detail": sid}
    except Exception as exc:
        return {"dial_status": "failed", "dial_detail": str(exc)[:400]}
