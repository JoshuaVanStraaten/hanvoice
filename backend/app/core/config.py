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
    nvidia_vision_model: str = "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"

    # Stripe (optional — billing routes 503 when unconfigured)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_premium: str = ""
    stripe_price_founder: str = ""

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
