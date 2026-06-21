"""
Twilio multi-hauler "bids" orchestration.

start_bids: the Browserbase agent discovers >= haulers_min local haulers, then the
backend texts them ALL a templated quote request in parallel. The session (with one
HaulerQuote per hauler) is stored in Redis.

handle_inbound_sms: each hauler reply hits the Twilio webhook; we map the sender's
number back to its session + quote, parse a price out of the text, and flip the quote
to "replied". The frontend polls get_bids() and streams quotes into the HaulerRow list
as they arrive.

Redis is the source of truth so the inbound webhook and the polling GET stay consistent
even across multiple workers.
"""

from __future__ import annotations

import asyncio
import logging
import re
import uuid
from typing import Optional

from app.config import settings
from app.schemas.rrr import BidSession, Hauler, HaulerQuote, HaulersRequest, StartBidsRequest
from app.services.cache import get_json, set_json
from app.services.rrr_haulers import _normalize_phone, discover_haulers
from app.services.twilio_sms import is_configured, send_sms

logger = logging.getLogger(__name__)


def _session_key(session_id: str) -> str:
    return f"bids:{session_id}"


def _phone_key(phone: str) -> str:
    return f"bids_phone:{phone}"


def _media_key(media_id: str) -> str:
    return f"bids_media:{media_id}"


async def get_media(media_id: str) -> Optional[dict]:
    """Return {"b64": ..., "ct": ...} for a stored item photo, or None."""
    return await get_json(_media_key(media_id))


def _template(req: StartBidsRequest, hauler: Hauler, has_image: bool) -> str:
    item = req.itemDescription or req.itemName or "a large item"
    photo = " (photo attached)" if has_image else ""
    return (
        f"Hi {hauler.haulerName}, I'd like a quote to haul away {item} in {req.location}{photo}. "
        f"Roughly what would you charge? Please reply with a price. Thanks! (sent via RRR)"
    )


async def _save(session: BidSession) -> None:
    await set_json(_session_key(session.sessionId), session.model_dump(), ttl=settings.cache_ttl_bids)


async def get_bids(session_id: str) -> Optional[BidSession]:
    data = await get_json(_session_key(session_id))
    return BidSession(**data) if data else None


async def start_bids(req: StartBidsRequest) -> BidSession:
    session_id = uuid.uuid4().hex

    haulers = await discover_haulers(
        HaulersRequest(location=req.location, itemName=req.itemName)
    )
    haulers = haulers[: max(1, req.maxHaulers)]

    if not haulers:
        return BidSession(
            sessionId=session_id,
            status="error",
            detail="Couldn't find local haulers to contact. Try again or call one directly.",
            quotes=[],
        )

    quotes = [
        HaulerQuote(
            haulerName=h.haulerName,
            rating=h.rating,
            distanceMi=h.distanceMi,
            phone=h.phone,
            status="pending",
        )
        for h in haulers
    ]
    session = BidSession(
        sessionId=session_id,
        status="collecting",
        detail="Texting haulers for quotes…",
        quotes=quotes,
    )
    await _save(session)

    if not is_configured():
        for q in session.quotes:
            q.status = "no_sms"
        session.status = "done"
        session.detail = (
            "Texting isn't set up (no Twilio number) — tap Call to reach a hauler directly."
        )
        await _save(session)
        return session

    # Stash the item photo and build the public MMS media URL Twilio will fetch.
    media_url = None
    has_image = False
    if req.imageBase64 and settings.public_base_url:
        await set_json(
            _media_key(session_id),
            {"b64": req.imageBase64, "ct": req.imageContentType or "image/jpeg"},
            ttl=settings.cache_ttl_bids,
        )
        base = settings.public_base_url.rstrip("/")
        media_url = [f"{base}/api/haulers/media/{session_id}"]
        has_image = True
    elif req.imageBase64 and not settings.public_base_url:
        logger.warning("Item image present but PUBLIC_BASE_URL unset — sending SMS without photo")

    # On a trial account, route every text to one verified number for testing.
    test_phone = _normalize_phone(settings.bids_test_phone) if settings.bids_test_phone else ""

    # Register reverse phone → session lookups (keyed by the number actually texted),
    # then blast all texts in parallel.
    await asyncio.gather(
        *(
            set_json(
                _phone_key(test_phone or q.phone),
                {"sessionId": session_id},
                ttl=settings.cache_ttl_bids,
            )
            for q in session.quotes
        )
    )
    results = await asyncio.gather(
        *(
            asyncio.to_thread(
                send_sms, test_phone or h.phone, _template(req, h, has_image), media_url
            )
            for h in haulers
        )
    )
    sent = 0
    for quote, sid in zip(session.quotes, results):
        if sid:
            sent += 1
        else:
            quote.status = "no_sms"  # landline / invalid — user can still tap Call

    session.detail = (
        f"Texted {sent} hauler(s). Waiting for quotes to come in…"
        if sent
        else "Couldn't text the haulers — tap Call to reach one directly."
    )
    await _save(session)
    return session


_PRICE_RE = re.compile(r"\$?\s*(\d{2,5})(?:\.\d{1,2})?\b")


def _parse_price(body: str) -> Optional[float]:
    """Pull the first plausible dollar amount out of a free-text reply."""
    # Prefer an explicit $-prefixed amount; fall back to the first 2-5 digit number.
    dollar = re.search(r"\$\s*(\d{2,5})(?:\.\d{1,2})?", body)
    match = dollar or _PRICE_RE.search(body)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


async def handle_inbound_sms(from_number: str, body: str) -> bool:
    """Twilio inbound webhook → attach the reply to its pending hauler quote."""
    phone = _normalize_phone(from_number) or from_number
    ref = await get_json(_phone_key(phone))
    if not ref:
        logger.info("Inbound SMS from unknown number %s — ignored", phone)
        return False

    session = await get_bids(ref.get("sessionId", ""))
    if not session:
        return False

    # Match the hauler by their real number; in test mode (all texts routed to one
    # verified phone) the reply won't match a hauler number, so fill the first
    # still-pending quote instead.
    target = next((q for q in session.quotes if q.phone == phone), None)
    if target is None:
        target = next((q for q in session.quotes if q.status == "pending"), None)

    matched = target is not None
    if target is not None:
        target.reply = body.strip()[:280]
        target.priceUsd = _parse_price(body)
        target.status = "replied"

    if matched:
        if all(q.status != "pending" for q in session.quotes):
            session.status = "done"
            session.detail = "All haulers responded."
        else:
            replied = sum(1 for q in session.quotes if q.status == "replied")
            session.detail = f"{replied} quote(s) in so far…"
        await _save(session)
    return matched
