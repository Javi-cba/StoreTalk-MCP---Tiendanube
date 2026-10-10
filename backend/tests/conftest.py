import base64
import os

# Tests must not depend on the developer's .env; set safe defaults before importing src.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("ENCRYPTION_KEY", base64.b64encode(b"0" * 32).decode())
os.environ.setdefault("API_KEY_PEPPER", "test-pepper")
os.environ.setdefault("TIENDANUBE_CLIENT_ID", "123")
os.environ.setdefault("TIENDANUBE_CLIENT_SECRET", "test-secret")
os.environ.setdefault("TIENDANUBE_USER_AGENT", "StoreTalk tests (test@example.com)")
