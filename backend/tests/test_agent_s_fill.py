"""End-to-end-ish verification of the Agent S fill pipeline WITHOUT any env keys.

The scrape -> decide -> fill -> verify logic in `agent_s._fill_page` is exercised
against a real *local* Chromium page (no Browserbase, no CDP) with the Gemini call
stubbed out, proving the structure works if real keys were present.

Requires: `pip install playwright pytest` + `playwright install chromium`.
Run from backend/: `python -m pytest tests/ -v`
"""

from __future__ import annotations

import asyncio
import contextlib

import pytest

from app.schemas.rrr import AgentFormProfile, AgentFormRequest
from app.services import agent_s

# A form covering every kind the hardened scraper handles.
FORM_HTML = """<!doctype html><html><body>
<form>
  <label for="name">Full name</label>
  <input id="name" name="name" type="text">
  <label for="email">Email</label>
  <input id="email" name="email" type="email">
  <label for="phone">Phone</label>
  <input id="phone" name="phone" type="tel">
  <textarea id="notes" name="notes" aria-label="Notes"></textarea>
  <label for="pickup">Pickup method</label>
  <select id="pickup" name="pickup">
    <option value="">Choose…</option>
    <option value="curb">Curbside</option>
    <option value="door">Doorstep</option>
  </select>
  <label><input type="radio" name="when" value="am"> Morning</label>
  <label><input type="radio" name="when" value="pm"> Afternoon</label>
  <label for="agree"><input id="agree" name="agree" type="checkbox"> I agree</label>
  <input type="hidden" name="csrf" value="xyz">
  <input type="submit" value="Submit">
</form></body></html>"""


def test_fill_page_fills_every_field_kind(tmp_path):
    form = tmp_path / "form.html"
    form.write_text(FORM_HTML, encoding="utf-8")

    req = AgentFormRequest(
        formUrl=form.as_uri(),
        profile=AgentFormProfile(
            name="Jane Doe", email="jane@example.com", phone="415-555-1212"
        ),
        itemName="Old sofa",
        itemDescription="Gently used 3-seater",
    )

    # Stub the LLM: keys must match what _scrape_fields emits.
    decided = {
        "#name": "Jane Doe",
        "#email": "jane@example.com",
        "#phone": "415-555-1212",
        "#notes": "Old sofa — gently used 3-seater",
        "#pickup": "Curbside",          # matched to option value "curb" by label
        "radio:when": "Afternoon",      # matched to radio value "pm" by label
        "#agree": "true",               # checkbox
    }

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            result = agent_s._fill_page(page, req, decide_fn=lambda fields, r: decided)

            assert page.input_value("#name") == "Jane Doe"
            assert page.input_value("#email") == "jane@example.com"
            assert page.input_value("#phone") == "415-555-1212"
            assert page.input_value("#notes") == "Old sofa — gently used 3-seater"
            assert page.input_value("#pickup") == "curb"
            assert page.is_checked('input[name="when"][value="pm"]')
            assert not page.is_checked('input[name="when"][value="am"]')
            assert page.is_checked("#agree")
        finally:
            browser.close()

    assert result["status"] == "ready"
    by_key = {r["key"]: r["ok"] for r in result["fields"]}
    assert all(by_key.values()), f"some fields failed: {by_key}"
    # hidden + submit must never be scraped as fillable
    assert "input[name=\"csrf\"]" not in by_key


def test_scrape_skips_non_fillable_and_groups_radios(tmp_path):
    form = tmp_path / "form.html"
    form.write_text(FORM_HTML, encoding="utf-8")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            page.goto(form.as_uri(), wait_until="domcontentloaded")
            fields = agent_s._scrape_fields(page, limit=40)
        finally:
            browser.close()

    kinds = [f["kind"] for f in fields]
    assert kinds.count("radio") == 1  # two radios collapse into one group
    radio = next(f for f in fields if f["kind"] == "radio")
    assert len(radio["options"]) == 2
    select = next(f for f in fields if f["kind"] == "select")
    assert {o["value"] for o in select["options"]} >= {"curb", "door"}
    keys = {f["key"] for f in fields}
    assert "#agree" in keys  # checkbox present
    # No hidden/submit leaked in.
    assert not any("csrf" in f["key"] for f in fields)


def test_start_form_fill_degrades_without_browserbase(monkeypatch):
    monkeypatch.setattr(agent_s.settings, "agent_s_enabled", True, raising=False)
    monkeypatch.setattr(agent_s.settings, "browserbase_api_key", "", raising=False)

    state = asyncio.run(agent_s.start_form_fill(AgentFormRequest(formUrl="https://example.com")))

    assert state.status == "error"
    assert "manually" in state.detail.lower()


def test_generate_json_sync_forces_clean_json(monkeypatch):
    from app.services import gemini

    captured = {}

    class _FakeResp:
        text = '{"#name": "Jane Doe"}'
        usage_metadata = None

    class _FakeModels:
        def generate_content(self, *, model, contents, config):
            captured["config"] = config
            return _FakeResp()

    class _FakeClient:
        models = _FakeModels()

    monkeypatch.setattr(gemini, "_get_client", lambda: _FakeClient())
    # Isolate from the OTEL/Phoenix tracer (not installed in the minimal test env).
    monkeypatch.setattr(gemini, "llm_span", lambda *a, **k: contextlib.nullcontext(None))
    monkeypatch.setattr(gemini, "set_llm_output", lambda *a, **k: None)

    out = gemini.generate_json_sync("system", "user")

    assert out == '{"#name": "Jane Doe"}'
    cfg = captured["config"]
    assert cfg.response_mime_type == "application/json"
    assert cfg.thinking_config.thinking_budget == 0
