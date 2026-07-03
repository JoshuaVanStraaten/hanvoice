"""Shared fixtures.

Environment is stubbed *before* the app is imported so ``Settings`` resolves
without a real .env. Supabase URLs point at a fake host that respx intercepts.
"""

import os

os.environ.setdefault("SUPABASE_URL", "http://supabase.test")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role-test-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-0123456789abcdef0123456789abcdef")
os.environ.setdefault("APP_ENV", "test")

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

SUPABASE_REST = "http://supabase.test/rest/v1"
SUPABASE_STORAGE = "http://supabase.test/storage/v1"


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
