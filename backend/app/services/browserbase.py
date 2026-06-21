from __future__ import annotations

import logging
import re
from typing import List, Optional

from browserbase import Browserbase

from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Browserbase] = None
# Lazily-created persistent context id, used when none is configured in .env.
_context_id: Optional[str] = None


def get_client() -> Browserbase:
    global _client
    if _client is None:
        if not settings.browserbase_api_key:
            raise ValueError("BROWSERBASE_API_KEY is not set")
        _client = Browserbase(api_key=settings.browserbase_api_key)
    return _client


def search_web(query: str, *, num_results: int = 3) -> List[dict]:
    """Browserbase web search — returns list of {title, url}."""
    client = get_client()
    response = client.search.web(query=query, num_results=num_results)
    return [
        {"title": r.title, "url": r.url}
        for r in (response.results or [])
    ]


def fetch_page(
    url: str,
    *,
    allow_redirects: bool = True,
    format: str = "markdown",
) -> dict:
    """Lightweight page retrieval via Browserbase Fetch API."""
    client = get_client()
    response = client.fetch_api.create(
        url=url,
        allow_redirects=allow_redirects,
        format=format,
    )
    return {
        "url": url,
        "status_code": response.status_code,
        "content": response.content or "",
        "headers": dict(response.headers) if response.headers else {},
    }


def _persistent_context_id() -> Optional[str]:
    """Return a Browserbase context id to persist logins across sessions.

    Prefers the configured BROWSERBASE_CONTEXT_ID; otherwise creates one once per
    process and logs it so it can be pinned in .env for true durability.
    """
    global _context_id
    if settings.browserbase_context_id:
        return settings.browserbase_context_id
    if _context_id:
        return _context_id
    try:
        ctx = get_client().contexts.create(project_id=settings.browserbase_project_id)
        _context_id = getattr(ctx, "id", None)
        if _context_id:
            logger.info(
                "Created Browserbase context %s — set BROWSERBASE_CONTEXT_ID=%s in .env "
                "to keep the Yelp/Google login across restarts.",
                _context_id,
                _context_id,
            )
        return _context_id
    except Exception as exc:  # noqa: BLE001 — context persistence is best-effort
        logger.warning("Could not create a persistent Browserbase context: %s", exc)
        return None


def create_session(
    *,
    persist_login: bool = False,
    stealth: bool = False,
    viewport: Optional[tuple[int, int]] = None,
):
    """Create a full Browserbase session for JS-heavy pages or PDFs.

    persist_login → attach a persistent context so a one-time Google/Yelp sign-in is
    reused on later sessions. stealth → enable bot-evasion + captcha solving (and
    proxies if configured) so Google's "browser may not be secure" block is avoided.
    viewport → (width, height) of the remote browser; pass a portrait size for flows
    streamed into the phone WebView so the page fits without horizontal scrolling.
    """
    client = get_client()
    kwargs: dict = {}
    if settings.browserbase_project_id:
        kwargs["project_id"] = settings.browserbase_project_id

    browser_settings: dict = {}
    if persist_login:
        cid = _persistent_context_id()
        if cid:
            browser_settings["context"] = {"id": cid, "persist": True}
    if stealth and settings.browserbase_advanced_stealth:
        browser_settings["advanced_stealth"] = True
    if stealth:
        browser_settings["solve_captchas"] = True
    if viewport:
        browser_settings["viewport"] = {"width": viewport[0], "height": viewport[1]}

    if browser_settings:
        kwargs["browser_settings"] = browser_settings
    if stealth and settings.browserbase_proxies:
        kwargs["proxies"] = True

    return client.sessions.create(**kwargs)


def session_connect_url(session) -> Optional[str]:
    """CDP endpoint Playwright connects to (connect_over_cdp)."""
    return getattr(session, "connect_url", None) or getattr(session, "connectUrl", None)


def release_session(session_id: str) -> None:
    """Request that Browserbase release a running session, so it doesn't linger and
    burn session minutes after the user is done. Best-effort: ignores errors and
    works across SDK shapes (sessions.update REQUEST_RELEASE)."""
    if not session_id:
        return
    client = get_client()
    try:
        client.sessions.update(
            session_id,
            project_id=settings.browserbase_project_id or None,
            status="REQUEST_RELEASE",
        )
    except Exception as exc:  # noqa: BLE001 — release is best-effort cleanup
        logger.debug("Browserbase session release skipped (%s): %s", session_id, exc)


def session_live_view_url(session_id: str) -> Optional[str]:
    """Embeddable fullscreen live-view URL for the running session."""
    client = get_client()
    try:
        debug = client.sessions.debug(session_id)
    except Exception:  # noqa: BLE001
        return None
    return (
        getattr(debug, "debugger_fullscreen_url", None)
        or getattr(debug, "debuggerFullscreenUrl", None)
        or getattr(debug, "debugger_url", None)
    )
