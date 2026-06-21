"""
Agent S form-filling over a Browserbase cloud browser.

Flow:
  1. Create a Browserbase session and grab its CDP connect URL + live-view URL.
  2. Return the live-view URL immediately so the phone embeds it in a WebView and
     the user watches the browser in real time.
  3. In the background, the form agent (Gemini 2.5 Flash) connects Playwright to
     that same remote session over CDP, reads the form fields, decides values from
     the user's profile, and fills them in — STOPPING before the final submit so
     the user reviews and submits themselves in the WebView.

The agent is intentionally conservative: it only fills inputs, never clicks submit.
If Browserbase/Playwright are unavailable, status flips to "error" and the frontend
falls back to opening the form URL directly in the same WebView.

This is the "Agent S" hook: when the Simular `gui-agents` package and a desktop
runtime are available it can drive the live view instead; the Gemini+Playwright
loop below is the reliable cloud-only driver that shares the exact same contract.

The page-driving logic lives in `_fill_page(page, req, ...)`, which is decoupled from
the Browserbase CDP connection and the session store so it can run against any
Playwright page (e.g. a local browser in tests) with a stubbed decision function.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from typing import Callable, Dict, List, Optional

from app.config import settings
from app.schemas.rrr import AgentFormRequest, AgentFormSession
from app.services.browserbase import (
    create_session,
    release_session,
    session_connect_url,
    session_live_view_url,
)

logger = logging.getLogger(__name__)

# In-memory session store (single-process; fine for the hackathon/demo).
_sessions: Dict[str, AgentFormSession] = {}

# Release a Browserbase session after this long so abandoned live views don't keep
# burning session minutes. The user normally submits well within this window.
_SESSION_TTL_SECONDS = 900

FILL_SYSTEM = """You are Agent S, a careful web-form-filling agent for the RRR app.
You are given the fields of a disposal/pickup scheduling form and the user's profile.
Map the profile to fields by meaning: name → full-name fields; email → email fields;
phone → phone/tel fields; address → street-address fields; zip → postal-code fields.
Use the item name/description for any "what are you disposing"/notes fields.
Never guess sensitive data you don't have. Leave a field blank ("") if you are unsure.
For select/radio fields return EXACTLY one of the listed option labels. For checkbox
fields return "true" or "false". You NEVER submit the form — a human reviews and submits."""


def get_form_status(session_id: str) -> Optional[AgentFormSession]:
    return _sessions.get(session_id)


async def start_form_fill(req: AgentFormRequest) -> AgentFormSession:
    session_id = uuid.uuid4().hex

    if not settings.agent_s_enabled or not settings.browserbase_api_key:
        state = AgentFormSession(
            sessionId=session_id,
            liveViewUrl="",
            status="error",
            detail="Agent S/Browserbase not configured — open the form manually.",
        )
        _sessions[session_id] = state
        return state

    try:
        bb_session = await asyncio.to_thread(create_session)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Browserbase session create failed: %s", exc)
        state = AgentFormSession(
            sessionId=session_id, liveViewUrl="", status="error", detail=str(exc)
        )
        _sessions[session_id] = state
        return state

    bb_id = getattr(bb_session, "id", None)
    connect_url = session_connect_url(bb_session)
    live_url = await asyncio.to_thread(session_live_view_url, bb_id) if bb_id else None

    state = AgentFormSession(
        sessionId=session_id,
        liveViewUrl=live_url or "",
        status="filling",
        detail="Agent S is opening the form…",
    )
    _sessions[session_id] = state

    # Kick off the fill in the background; the live view streams immediately.
    asyncio.create_task(_run_fill(session_id, connect_url, req))
    # Defer cleanup so an abandoned session doesn't linger (the user submits in the
    # live view, so we can't close it right away — release after a TTL instead).
    if bb_id:
        asyncio.create_task(_release_after(bb_id, _SESSION_TTL_SECONDS))
    return state


async def _release_after(bb_id: str, delay: float) -> None:
    try:
        await asyncio.sleep(delay)
        await asyncio.to_thread(release_session, bb_id)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.debug("Deferred session release failed for %s: %s", bb_id, exc)


async def _run_fill(session_id: str, connect_url: Optional[str], req: AgentFormRequest) -> None:
    if not connect_url:
        _update(session_id, "error", "No CDP endpoint for the browser session.")
        return
    try:
        await asyncio.to_thread(_fill_sync, session_id, connect_url, req)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Agent S fill failed for %s: %s", session_id, exc)
        _update(session_id, "error", f"Could not auto-fill: {exc}")


def _update(session_id: str, status: str, detail: str) -> None:
    state = _sessions.get(session_id)
    if state:
        state.status = status  # type: ignore[assignment]
        state.detail = detail


def _fill_sync(session_id: str, connect_url: str, req: AgentFormRequest) -> None:
    """Connect Playwright to the Browserbase session over CDP, then drive the page.

    Only the connection lives here; the scrape→decide→fill→verify pipeline is in
    `_fill_page` so it can be tested against a local browser without Browserbase.
    """
    from playwright.sync_api import sync_playwright  # local import: optional dep

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(connect_url)
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.pages[0] if context.pages else context.new_page()

        result = _fill_page(
            page, req, progress=lambda msg: _update(session_id, "filling", msg)
        )
        _update(session_id, result["status"], result["detail"])
        # Leave the page open in the live view for the user; do NOT submit.


# --- Core page logic (decoupled from Browserbase + the session store) -------------

DecideFn = Callable[[List[dict], AgentFormRequest], Dict[str, str]]


def _fill_page(
    page,
    req: AgentFormRequest,
    *,
    decide_fn: Optional[DecideFn] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> dict:
    """Navigate to the form, read its fields, decide values, fill + verify them.

    Returns {status, detail, fields:[{key, ok, detail}]}. `decide_fn` is injectable
    so tests can supply a fixed value map instead of calling Gemini. Never submits.
    """
    decide = decide_fn or _decide_values_blocking

    def _progress(msg: str) -> None:
        if progress:
            progress(msg)

    page.goto(req.formUrl, wait_until="domcontentloaded", timeout=45000)
    _progress("Reading the form fields…")

    fields = _scrape_fields(page, limit=settings.agent_s_max_steps or 40)
    if not fields:
        return {"status": "ready", "detail": "Form loaded — review and submit.", "fields": []}

    values = decide(fields, req)
    _progress("Filling in your details…")

    results: List[dict] = []
    for field in fields:
        results.append(_apply_field(page, field, values.get(field["key"], "")))

    filled = sum(1 for r in results if r["ok"])
    logger.info("Agent S filled %d/%d fields", filled, len(results))
    return {
        "status": "ready",
        "detail": "Prefilled — review the fields and submit.",
        "fields": results,
    }


def _apply_field(page, field: dict, value: str) -> dict:
    """Fill a single field according to its kind, verifying the result."""
    kind = field["kind"]
    key = field["key"]
    try:
        if kind == "checkbox":
            return _apply_checkbox(page, field, _truthy(value))
        if not value:
            return {"key": key, "ok": False, "detail": "no value"}
        if kind == "select":
            return _apply_select(page, field, value)
        if kind == "radio":
            return _apply_radio(page, field, value)
        return _apply_text(page, field, value)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Field fill skipped (%s): %s", key, exc)
        return {"key": key, "ok": False, "detail": str(exc)}


def _apply_text(page, field: dict, value: str) -> dict:
    el = page.query_selector(field["selector"])
    if not el:
        return {"key": field["key"], "ok": False, "detail": "not found"}
    el.fill(value)
    if _norm(el.input_value()) != _norm(value):
        # Some controlled inputs ignore fill(); fall back to click + type.
        try:
            el.click()
            el.fill("")
            el.type(value)
        except Exception:  # noqa: BLE001
            pass
    ok = _norm(el.input_value()) == _norm(value)
    return {"key": field["key"], "ok": ok, "detail": "" if ok else "value mismatch"}


def _apply_select(page, field: dict, value: str) -> dict:
    el = page.query_selector(field["selector"])
    if not el:
        return {"key": field["key"], "ok": False, "detail": "not found"}
    match = _match_option(field.get("options", []), value)
    try:
        if match:
            try:
                el.select_option(value=match["value"])
            except Exception:  # noqa: BLE001
                el.select_option(label=match["label"])
        else:
            el.select_option(label=value)
    except Exception as exc:  # noqa: BLE001
        return {"key": field["key"], "ok": False, "detail": str(exc)}
    ok = bool(el.input_value()) and (not match or el.input_value() == match["value"])
    return {"key": field["key"], "ok": ok, "detail": "" if ok else "no matching option"}


def _apply_radio(page, field: dict, value: str) -> dict:
    match = _match_option(field.get("options", []), value)
    if not match:
        return {"key": field["key"], "ok": False, "detail": "no matching option"}
    el = page.query_selector(match["selector"])
    if not el:
        return {"key": field["key"], "ok": False, "detail": "option not found"}
    el.check()
    ok = el.is_checked()
    return {"key": field["key"], "ok": ok, "detail": "" if ok else "could not select"}


def _apply_checkbox(page, field: dict, want: bool) -> dict:
    el = page.query_selector(field["selector"])
    if not el:
        return {"key": field["key"], "ok": False, "detail": "not found"}
    if want:
        el.check()
    else:
        el.uncheck()
    ok = el.is_checked() == want
    return {"key": field["key"], "ok": ok, "detail": "" if ok else "could not toggle"}


# --- Scraping --------------------------------------------------------------------

# Best-effort human label for an element: aria-label, associated <label>, wrapping
# <label>, placeholder, then name. Used for every field kind.
_LABEL_JS = """
e => {
  if (e.getAttribute && e.getAttribute('aria-label')) return e.getAttribute('aria-label');
  if (e.id) { const l = document.querySelector('label[for="' + e.id + '"]'); if (l) return l.innerText; }
  const wrap = e.closest ? e.closest('label') : null;
  if (wrap) return wrap.innerText;
  if (e.placeholder) return e.placeholder;
  return e.name || '';
}
"""

_SKIP_INPUT_TYPES = ("hidden", "submit", "button", "image", "reset", "file", "password")


def _scrape_fields(page, *, limit: int = 40) -> List[dict]:
    """Extract fillable fields with stable selectors, grouping radios and reading
    select/radio option lists so the LLM can pick a valid choice."""
    handles = page.query_selector_all("input, textarea, select")
    fields: List[dict] = []
    radio_groups: Dict[str, dict] = {}

    for i, el in enumerate(handles):
        try:
            tag = (el.evaluate("e => e.tagName") or "").lower()
            input_type = (el.get_attribute("type") or "text").lower()
            if tag == "input" and input_type in _SKIP_INPUT_TYPES:
                continue

            name = el.get_attribute("name") or ""
            el_id = el.get_attribute("id") or ""
            label = (el.evaluate(_LABEL_JS) or "")[:120].strip()

            if tag == "select":
                selector = _stable_selector(el, tag, name, el_id, i)
                fields.append(
                    {
                        "key": selector,
                        "selector": selector,
                        "kind": "select",
                        "label": label,
                        "options": _read_options(el),
                    }
                )
            elif tag == "input" and input_type == "radio":
                value = el.get_attribute("value") or ""
                opt_selector = _radio_selector(el, name, value, el_id, i)
                group_key = name or f"_anon{i}"
                grp = radio_groups.get(group_key)
                if not grp:
                    grp = {
                        "key": f"radio:{name or el_id or i}",
                        "kind": "radio",
                        "name": name,
                        "label": name or label,
                        "options": [],
                    }
                    radio_groups[group_key] = grp
                    fields.append(grp)
                grp["options"].append(
                    {"selector": opt_selector, "value": value, "label": label or value}
                )
            elif tag == "input" and input_type == "checkbox":
                selector = _stable_selector(el, tag, name, el_id, i)
                fields.append(
                    {"key": selector, "selector": selector, "kind": "checkbox", "label": label}
                )
            else:
                selector = _stable_selector(el, tag, name, el_id, i)
                fields.append(
                    {
                        "key": selector,
                        "selector": selector,
                        "kind": "text",
                        "label": label,
                        "type": input_type,
                    }
                )
        except Exception:  # noqa: BLE001
            continue
        if len(fields) >= limit:
            break
    return fields


def _read_options(select_el) -> List[dict]:
    options: List[dict] = []
    for o in select_el.query_selector_all("option"):
        value = o.get_attribute("value")
        text = (o.inner_text() or "").strip()
        if value is None:
            value = text
        if not (value or text):
            continue
        options.append({"value": value, "label": text or value})
    return options


def _stable_selector(el, tag: str, name: str, el_id: str, i: int) -> str:
    if el_id:
        return f"#{_css_escape(el_id)}"
    if name:
        return f'{tag}[name="{name}"]'
    el.evaluate(f"e => e.setAttribute('data-rrr-idx', '{i}')")
    return f'[data-rrr-idx="{i}"]'


def _radio_selector(el, name: str, value: str, el_id: str, i: int) -> str:
    if el_id:
        return f"#{_css_escape(el_id)}"
    if name and value:
        return f'input[name="{name}"][value="{value}"]'
    el.evaluate(f"e => e.setAttribute('data-rrr-idx', '{i}')")
    return f'[data-rrr-idx="{i}"]'


def _css_escape(value: str) -> str:
    return re.sub(r'([^a-zA-Z0-9_-])', r"\\\1", value)


# --- Matching helpers ------------------------------------------------------------


def _norm(value: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _truthy(value: Optional[str]) -> bool:
    return _norm(value) in ("true", "yes", "1", "on", "checked", "y")


def _match_option(options: List[dict], value: str) -> Optional[dict]:
    """Match an LLM-chosen value to a real option by value/label, tolerating
    case/whitespace drift, then falling back to a substring match."""
    nv = _norm(value)
    if not nv:
        return None
    for o in options:
        if _norm(o.get("value")) == nv or _norm(o.get("label")) == nv:
            return o
    for o in options:
        lab = _norm(o.get("label"))
        if lab and (nv in lab or lab in nv):
            return o
    return None


# --- LLM decision ----------------------------------------------------------------


def _decide_values_blocking(fields: List[dict], req: AgentFormRequest) -> Dict[str, str]:
    """Ask Gemini (sync, JSON-forced) to map the profile → field values."""
    from app.services.gemini import generate_json_sync

    # NOTE: the frontend currently sends only email/address/zip (onboarding collects
    # address/zip/location, auth provides email); name/phone are accepted here but
    # not yet collected client-side, so those fields stay blank until that lands.
    profile = req.profile.model_dump()
    field_lines = "\n".join(_field_brief(f) for f in fields)
    prompt = f"""User profile: {json.dumps(profile)}
Item being disposed: {req.itemName} — {req.itemDescription}

Form fields (use the exact key shown as the JSON key):
{field_lines}

Return ONLY a JSON object mapping key -> value:
- text fields: the value from the profile/item, or "" if unknown or sensitive.
- select/radio fields: EXACTLY one of the listed option labels, or "" if none fit.
- checkbox fields: "true" or "false".
Example: {{ "#name": "Jane Doe", "radio:pickup": "Curbside", "#agree": "true" }}"""

    raw = generate_json_sync(FILL_SYSTEM, prompt, max_output_tokens=2048)
    data = _parse_json_object(raw)
    return {str(k): str(v) for k, v in data.items() if v is not None}


def _field_brief(f: dict) -> str:
    kind = f["kind"]
    if kind in ("select", "radio"):
        opts = ", ".join(o["label"] for o in f.get("options", [])[:25])
        return f'- key "{f["key"]}" ({kind}) label="{f["label"]}" options=[{opts}]'
    if kind == "checkbox":
        return f'- key "{f["key"]}" (checkbox) label="{f["label"]}" — answer "true" or "false"'
    return f'- key "{f["key"]}" (text/{f.get("type", "text")}) label="{f["label"]}"'


def _parse_json_object(raw: str) -> dict:
    text = (raw or "").strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        pass
    # Safety net if JSON mode ever returns fenced/wrapped text.
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        data = json.loads(text[start : end + 1])
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}
