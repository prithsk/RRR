"""
Local junk-hauler discovery for the RRR "bids" flow.

No Yelp. A Browserbase agent web-searches for local junk-removal companies, fetches
the top pages, and Gemini extracts at least `settings.haulers_min` real haulers WITH
phone numbers. The list is cached in Redis so the Twilio bids agent (twilio_bids.py)
can immediately text them a templated quote request.

Degrades gracefully: if Browserbase/Gemini are unavailable it returns whatever it
found (possibly empty), and the caller surfaces an error to the user.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from typing import List

from app.config import settings
from app.observability import capture_silent_failure
from app.schemas.rrr import Hauler, HaulersRequest
from app.services.browserbase import fetch_page, search_web
from app.services.cache import get_json, set_json
from app.services.gemini import generate_json

logger = logging.getLogger(__name__)

HAULERS_SYSTEM = """You are a local junk-removal hauler discovery agent for the RRR app.
Your job is to find REAL, currently-operating junk-removal / hauling businesses that
serve the user's location, each with a working contact PHONE NUMBER. Prefer local
independents and well-known chains that actually operate in the area (e.g. 1-800-GOT-JUNK,
College Hunks, LoadUp, plus local haulers). Never invent businesses or phone numbers —
only return ones grounded in the provided web reference material. Mobile/textable numbers
are best because the user will TEXT them for a quote."""


def _cache_key(req: HaulersRequest) -> str:
    raw = f"{req.location.lower()}:{(req.itemName or '').lower()}"
    return f"haulers:{hashlib.sha256(raw.encode()).hexdigest()}"


def _search_queries(req: HaulersRequest) -> List[str]:
    item = (req.itemName or "").strip()
    return [
        f"{req.location} junk removal hauling company phone number",
        f"{req.location} {item} haul away pickup junk removal service".strip(),
        f"best junk removal near {req.location} contact phone",
    ]


def _normalize_phone(raw: str) -> str:
    """Best-effort US E.164 normalization; returns "" if it doesn't look phone-like."""
    digits = re.sub(r"[^\d]", "", raw or "")
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    if len(digits) == 10:
        return f"+1{digits}"
    if raw.strip().startswith("+") and 8 <= len(digits) <= 15:
        return f"+{digits}"
    return ""


async def discover_haulers(req: HaulersRequest) -> List[Hauler]:
    """Browserbase + Gemini → at least `haulers_min` local haulers with phones."""
    cache_key = _cache_key(req)
    cached = await get_json(cache_key)
    if cached:
        return [Hauler(**h) for h in cached]

    pages: List[dict] = []
    seen: set[str] = set()
    for query in _search_queries(req):
        if len(pages) >= 6:
            break
        try:
            results = await asyncio.to_thread(
                search_web, query, num_results=max(settings.browserbase_search_num_results, 5)
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Hauler search failed (%r): %s", query, exc)
            capture_silent_failure(
                exc, where="browserbase.search_web", query=query, stage="hauler_discovery"
            )
            continue
        for result in results:
            if len(pages) >= 6:
                break
            url = result.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            try:
                page = await asyncio.to_thread(fetch_page, url, format="markdown")
                if page.get("content") and page.get("status_code", 0) < 400:
                    pages.append(
                        {
                            "url": url,
                            "title": result.get("title", url),
                            "content": page["content"][:8000],
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Hauler fetch failed for %s: %s", url, exc)
                capture_silent_failure(
                    exc, where="browserbase.fetch_page", url=url, stage="hauler_discovery"
                )

    prompt = _build_prompt(req, pages)
    try:
        raw = await generate_json(HAULERS_SYSTEM, prompt, max_output_tokens=2048)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Hauler extraction failed: %s", exc)
        capture_silent_failure(exc, where="gemini.discover_haulers", location=req.location)
        return []

    haulers = _parse_haulers(raw)

    if len(haulers) < settings.haulers_min:
        capture_silent_failure(
            RuntimeError(
                f"Hauler discovery returned {len(haulers)} (<{settings.haulers_min}) for "
                f"{req.location!r}"
            ),
            where="rrr_haulers.discover_haulers",
            reason="below_minimum",
            location=req.location,
            found=len(haulers),
        )

    if haulers:
        await set_json(
            cache_key,
            [h.model_dump() for h in haulers],
            ttl=settings.cache_ttl_haulers,
        )
    return haulers


def _build_prompt(req: HaulersRequest, pages: List[dict]) -> str:
    refs = []
    for i, page in enumerate(pages, 1):
        refs.append(f"{i}. {page['title']}\n   URL: {page['url']}\n   Content:\n{page['content'][:4000]}")
    refs_block = (
        "\n\n".join(refs)
        if refs
        else "No page content fetched — use well-known national haulers that serve this area."
    )
    item = req.itemName or "a large item"
    min_n = settings.haulers_min
    return f"""Find AT LEAST {min_n} (ideally 5) real local junk-removal haulers that serve
this user and could haul "{item}". EVERY hauler MUST have a phone number.

Location: {req.location}
Item: {item}

Web reference material:
{refs_block}

Rules:
- Only return haulers grounded in the reference material above (or unambiguous national
  chains known to serve this location). Do NOT invent businesses or phone numbers.
- You MUST return at least {min_n} haulers. If the pages are thin, include reputable
  national haulers (1-800-GOT-JUNK, College Hunks Hauling Junk, LoadUp, Junk King) that
  operate in this area, with their booking phone numbers.
- Estimate rating (0-5) and distanceMi honestly; use 0 when unknown.

Return ONLY valid JSON (no markdown fences) in this exact shape:
{{
  "haulers": [
    {{ "haulerName": "Bay Area Junk Removal", "rating": 4.7, "distanceMi": 3.2,
       "phone": "+14155551234", "url": "https://..." }}
  ]
}}"""


def _parse_haulers(raw: str) -> List[Hauler]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse haulers JSON from model output")
        capture_silent_failure(
            exc, where="gemini.parse_haulers_json", raw_snippet=text[:500]
        )
        return []

    haulers: List[Hauler] = []
    seen_phones: set[str] = set()
    for item in data.get("haulers", []):
        name = str(item.get("haulerName", "")).strip()
        phone = _normalize_phone(str(item.get("phone", "")))
        if not name or not phone or phone in seen_phones:
            continue
        seen_phones.add(phone)
        try:
            haulers.append(
                Hauler(
                    haulerName=name,
                    rating=float(item.get("rating", 0) or 0),
                    distanceMi=float(item.get("distanceMi", 0) or 0),
                    phone=phone,
                    url=(item.get("url") or None),
                )
            )
        except (TypeError, ValueError):
            continue
    return haulers
