from pathlib import Path

from pydantic_settings import BaseSettings

_ENV_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    app_name: str = "RecycleRegulations"
    debug: bool = False

    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    browserbase_api_key: str = ""
    browserbase_project_id: str = ""
    # Persistent context: a signed-in Yelp/Google login is reused across sessions so
    # the brittle Google OAuth only has to succeed once. Leave blank to auto-create
    # one on first run (the id is logged — paste it here to make it durable).
    browserbase_context_id: str = ""
    # Bot-evasion for Google sign-in (reduces the "this browser may not be secure"
    # block). advanced_stealth requires the Browserbase Scale plan.
    browserbase_advanced_stealth: bool = False
    browserbase_proxies: bool = False

    # Twilio SMS — multi-hauler "bids" blast. Haulers are discovered by the
    # Browserbase agent (no Yelp), then texted a templated quote request; their
    # replies hit the inbound webhook and stream back as quotes.
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""  # E.164 SMS-capable Twilio number, e.g. +14155551234
    twilio_validate_signature: bool = False  # verify X-Twilio-Signature on the webhook
    # Minimum local junk haulers the discovery agent must surface for the bids flow.
    haulers_min: int = 3
    # Public HTTPS base URL the backend is reachable at (e.g. your ngrok URL). Used to
    # build the MMS media URL Twilio fetches the item photo from. Leave blank to send
    # plain SMS (no image).
    public_base_url: str = ""
    # TEST ONLY: route every hauler text to this one number instead of the real
    # haulers. Lets you demo the full bid loop on a Twilio trial (which can only
    # text *verified* numbers). Leave blank in real use.
    bids_test_phone: str = ""
    cache_ttl_haulers: int = 43200  # 12 hours
    cache_ttl_bids: int = 3600  # 1 hour — a live bidding session

    geoip_url: str = "http://ip-api.com/json"
    geo_max_match_km: float = 150.0  # closest-campus match only within this radius
    rag_top_k: int = 5

    # Redis cache-aside
    redis_enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_ip: int = 604800  # 7 days
    cache_ttl_municipal_rules: int = 86400  # 24 hours
    cache_ttl_disposal_options: int = 43200  # 12 hours
    cache_ttl_triage: int = 86400  # 24 hours
    cache_ttl_card_detail: int = 43200  # 12 hours
    cache_ttl_location_rag: int = 0  # 0 ⇒ no expiry (persistent RAG)

    # Agent S (Simular) form-filling over a Browserbase cloud session
    agent_s_max_steps: int = 25
    agent_s_enabled: bool = True

    # Vector search
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 3072
    vector_distance_threshold: float = 0.35

    # Browserbase research
    browserbase_search_num_results: int = 3

    # RRR mobile app integration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    allowed_origins: str = ""
    auth_required: bool = False

    # Sentry error monitoring — captures silent failures behind graceful fallbacks
    sentry_dsn: str = ""
    sentry_environment: str = "local"
    sentry_traces_sample_rate: float = 1.0

    # Arize Phoenix (OSS) observability
    phoenix_enabled: bool = True
    phoenix_collector_endpoint: str = ""
    phoenix_api_key: str = ""
    phoenix_project: str = "rrr-backend"

    # Prompt A/B switch for the eval before/after loop: "baseline" | "v2"
    prompt_variant: str = "baseline"

    @property
    def cors_origins(self) -> list[str]:
        if not self.allowed_origins.strip():
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    class Config:
        env_file = (_ENV_DIR / ".env", _ENV_DIR.parent / ".env")
        extra = "ignore"


settings = Settings()
