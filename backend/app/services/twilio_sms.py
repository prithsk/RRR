"""
Thin Twilio SMS wrapper for the hauler bids flow.

Sends the templated quote-request SMS to each discovered hauler. Degrades
gracefully: when Twilio isn't configured, send_sms() returns False instead of
raising, so the bids flow can mark those haulers as un-textable.
"""

from __future__ import annotations

import logging
from typing import Optional, Sequence

from app.config import settings
from app.observability import capture_silent_failure

logger = logging.getLogger(__name__)

_client = None


def is_configured() -> bool:
    return bool(
        settings.twilio_account_sid
        and settings.twilio_auth_token
        and settings.twilio_from_number
    )


def get_client():
    global _client
    if _client is None:
        from twilio.rest import Client  # local import: optional dep

        _client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    return _client


def send_sms(
    to: str, body: str, media_url: Optional[Sequence[str]] = None
) -> Optional[str]:
    """Send one SMS/MMS. Pass media_url (public HTTPS image URLs) to attach the item
    photo as MMS. Returns the Twilio message SID, or None on failure."""
    if not is_configured():
        logger.warning("Twilio not configured — cannot text %s", to)
        capture_silent_failure(
            RuntimeError("Twilio not configured — hauler SMS silently skipped"),
            where="twilio.send_sms",
            reason="not_configured",
            to=to,
        )
        return None
    try:
        kwargs = {"to": to, "from_": settings.twilio_from_number, "body": body}
        if media_url:
            kwargs["media_url"] = list(media_url)
        msg = get_client().messages.create(**kwargs)
        return getattr(msg, "sid", None)
    except Exception as exc:  # noqa: BLE001 — landlines / invalid numbers fail here
        logger.warning("Twilio send to %s failed: %s", to, exc)
        capture_silent_failure(exc, where="twilio.send_sms", reason="send_failed", to=to)
        return None
