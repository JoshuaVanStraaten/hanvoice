"""Application settings.

Every environment variable the backend reads is declared here — nothing else
in the codebase touches ``os.environ``. Required settings (Supabase) fail at
startup with a clear pydantic error; optional AI/billing providers default to
empty strings and their features degrade with explicit 503s instead of
crashing the whole app.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"
    frontend_url: str = "http://localhost:5173"

    # Supabase (required — the app cannot function without its database)
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    # Azure Speech: pronunciation assessment + neural TTS (same key/region)
    azure_speech_key: str = ""
    azure_speech_region: str = ""
    azure_tts_voice: str = "ko-KR-SunHiNeural"

    # NVIDIA-hosted models (OpenAI-compatible chat endpoint; NVIDIA's speech
    # models are gRPC-only, so ASR/TTS live on Azure Speech instead)
    nvidia_api_key: str = ""
    nvidia_llm_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    nvidia_llm_model: str = "meta/llama-3.1-70b-instruct"
    nvidia_vision_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    # Handwriting judge. Benchmarked 2026-07-12 against canvas-like strokes:
    # nemotron-nano-vl-8b zeroed honest attempts (the churn bug), qwen3.5 and
    # nemotron-12b-v2-vl couldn't separate real writing from a scribble; the
    # 90B is the only one that passed honest jamo and failed the scribble.
    nvidia_vision_model: str = "meta/llama-3.2-90b-vision-instruct"

    # Sentry error monitoring (optional — no-op when empty)
    sentry_dsn: str = ""

    # Paddle Billing (optional — billing routes 503 when unconfigured).
    # The client token is public by design (it initializes Paddle.js in the
    # browser); the webhook secret is the only sensitive value here.
    paddle_env: str = "sandbox"  # "sandbox" | "production"
    paddle_client_token: str = ""
    paddle_webhook_secret: str = ""
    paddle_price_premium: str = ""
    paddle_price_founder: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
