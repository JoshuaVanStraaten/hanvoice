"""Shared fixtures.

Environment is stubbed *before* the app is imported so ``Settings`` resolves
without a real .env. Supabase URLs point at a fake host that respx intercepts.
"""

import os

os.environ.setdefault("SUPABASE_URL", "http://supabase.test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role-test-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-0123456789abcdef0123456789abcdef")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("AZURE_SPEECH_KEY", "azure-test-key")
os.environ.setdefault("AZURE_SPEECH_REGION", "koreacentral")
os.environ.setdefault("NVIDIA_API_KEY", "nvidia-test-key")
os.environ.setdefault("NVIDIA_LLM_URL", "http://nvidia.test/llm")
os.environ.setdefault("NVIDIA_VISION_URL", "http://nvidia.test/vision")

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services import tts_cache

SUPABASE_REST = "http://supabase.test/rest/v1"
SUPABASE_STORAGE = "http://supabase.test/storage/v1"


@pytest.fixture(autouse=True)
def _fresh_tts_cache():
    """TTS audio is cached process-wide; tests must not leak hits."""
    tts_cache.clear_cache()
    yield
    tts_cache.clear_cache()


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
