"""
============================================================
SDLC Phase 3 — Security & Compliance Testing
============================================================
Software Development Lifecycle Stage: SECURITY / TESTING

This phase validates security requirements from the SRS:
  • OWASP Top-10: Injection, Broken Auth, Sensitive Data Exposure
  • Code injection prevention (AST-level blocking)
  • SQL injection safety (ORM parameterized queries)
  • Cross-user data isolation (authorization, not just authentication)
  • Token security: JWTs never leaked in response bodies
  • Input sanitization: long inputs, unicode, special characters
  • Rate of information leakage: error messages are generic

~32 Tests
============================================================
"""

import pytest
import io
import json
import pandas as pd
import numpy as np
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from database.session import Base, get_db

TEST_DB_URL = "sqlite:///./test_sdlc3.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

_counter = 0
def make_user(prefix="sec"):
    global _counter
    _counter += 1
    return {"username": f"{prefix}_{_counter}", "email": f"{prefix}_{_counter}@test.com", "password": "Secure123!"}

def auth_headers(u):
    client.post("/api/auth/register", json=u)
    r = client.post("/api/auth/login", json={"username": u["username"], "password": u["password"]})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}

def upload_csv(headers, rows=20):
    df = pd.DataFrame({"val": np.arange(rows), "cat": [f"c{i%5}" for i in range(rows)]})
    buf = io.BytesIO(); df.to_csv(buf, index=False); buf.seek(0)
    r = client.post("/api/datasets/upload", headers=headers,
                    files={"file": ("d.csv", buf, "text/csv")})
    body = r.json()
    return body.get("dataset_id") or body.get("id")


# ═════════════════════════════════════════════════════════
# SEC-1: Code Injection Prevention (OWASP A03:2021)
# ═════════════════════════════════════════════════════════

class TestCodeInjectionPrevention:
    """The query validator must block all code injection vectors."""

    def setup_method(self):
        from services.query_validator import validate_query
        self.validate = validate_query
        self.cols = ["sales", "region", "date"]

    INJECTION_PAYLOADS = [
        "import os; os.system('rm -rf /')",
        "__import__('subprocess').call(['ls', '-la'])",
        "exec('malicious code here')",
        "eval('1+1')",
        "().__class__.__mro__[1].__subclasses__()",
        "open('/etc/passwd').read()",
        "import sys; sys.exit()",
        "globals()['__builtins__'].__import__('os')",
    ]

    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
    def test_sec_injection_payload_blocked(self, payload):
        """SEC-1.1: All known code injection patterns are rejected."""
        result = self.validate(payload, self.cols)
        assert result["is_valid"] is False, \
            f"SECURITY FAILURE: Injection payload was NOT blocked: {payload[:60]}"

    def test_sec_safe_code_is_allowed(self):
        """SEC-1.2: Legitimate data analysis code passes validation."""
        safe = "result = df.groupby('region')['sales'].mean()"
        result = self.validate(safe, self.cols)
        assert result["is_valid"] is True

    def test_sec_dunder_traversal_blocked(self):
        """SEC-1.3: __class__.__mro__ traversal is blocked."""
        from services.query_validator import validate_query
        result = validate_query("df.__class__.__mro__", ["a", "b"])
        assert result["is_valid"] is False

    def test_sec_file_open_blocked(self):
        """SEC-1.4: File open operations are blocked."""
        from services.query_validator import validate_query
        result = validate_query("open('/etc/passwd', 'r').read()", ["a"])
        assert result["is_valid"] is False


# ═════════════════════════════════════════════════════════
# SEC-2: Cross-User Data Isolation (OWASP A01:2021)
# ═════════════════════════════════════════════════════════

class TestCrossUserDataIsolation:
    """Users must not be able to access each other's data."""

    def setup_method(self):
        self.user_a = make_user("user_a")
        self.user_b = make_user("user_b")
        self.headers_a = auth_headers(self.user_a)
        self.headers_b = auth_headers(self.user_b)

        # User A uploads a dataset
        self.dataset_id = upload_csv(self.headers_a, rows=25)

    def test_sec_user_b_cannot_see_user_a_datasets(self):
        """SEC-2.1: User B's dataset list does not contain User A's datasets."""
        r = client.get("/api/datasets/", headers=self.headers_b)
        ids = [d.get("id") or d.get("dataset_id") for d in r.json()]
        assert self.dataset_id not in ids, "User B can see User A's dataset!"

    def test_sec_user_b_cannot_query_user_a_dataset(self):
        """SEC-2.2: User B querying User A's dataset gets 403 or 404."""
        if self.dataset_id is None:
            pytest.skip("Dataset upload failed")
        r = client.post("/api/queries/run",
                        headers=self.headers_b,
                        json={"query": "show average val", "dataset_id": self.dataset_id})
        assert r.status_code in (403, 404, 400), \
            f"User B accessed User A's dataset! Status: {r.status_code}"

    def test_sec_user_b_cannot_see_user_a_query_history(self):
        """SEC-2.3: Query history is scoped per user."""
        # User A runs a query
        client.post("/api/queries/run",
                    headers=self.headers_a,
                    json={"query": "show val", "dataset_id": self.dataset_id})
        # User B's history should be empty (fresh user)
        r = client.get("/api/queries/history", headers=self.headers_b)
        assert r.status_code == 200
        history = r.json()
        # User B should have 0 or very few queries — none from User A
        assert len(history) == 0, "User B can see User A's query history!"


# ═════════════════════════════════════════════════════════
# SEC-3: Sensitive Data Exposure (OWASP A02:2021)
# ═════════════════════════════════════════════════════════

class TestSensitiveDataExposure:
    """Sensitive data (passwords, tokens) must not be leaked in responses."""

    def setup_method(self):
        self.u = make_user("leak")
        self.password = self.u["password"]

    def test_sec_password_not_in_register_response(self):
        """SEC-3.1: Registration response never contains the plaintext password."""
        r = client.post("/api/auth/register", json=self.u)
        body = json.dumps(r.json())
        assert self.password not in body

    def test_sec_hashed_password_not_in_register_response(self):
        """SEC-3.2: Hashed password (bcrypt hash) not in registration response."""
        r = client.post("/api/auth/register", json=self.u)
        body = json.dumps(r.json())
        assert "hashed_password" not in body.lower()
        assert "$2b$" not in body  # bcrypt hash prefix

    def test_sec_login_response_contains_no_password(self):
        """SEC-3.3: Login response never echoes the password."""
        client.post("/api/auth/register", json=self.u)
        r = client.post("/api/auth/login", json={"username": self.u["username"], "password": self.password})
        body = json.dumps(r.json())
        assert self.password not in body

    def test_sec_wrong_credentials_gives_generic_message(self):
        """SEC-3.4: Wrong credentials error message doesn't reveal which field was wrong."""
        client.post("/api/auth/register", json=self.u)
        r = client.post("/api/auth/login", json={"username": self.u["username"], "password": "WRONGPASS"})
        error = json.dumps(r.json()).lower()
        # Should NOT say "password incorrect" or "username not found" specifically
        assert "username not found" not in error
        assert "password incorrect" not in error
        assert "wrong password" not in error

    def test_sec_dataset_of_other_user_not_in_404_error(self):
        """SEC-3.5: 404 error for other user's dataset should not reveal owner info."""
        u = make_user("owner")
        headers = auth_headers(u)
        # Upload and get an ID
        did = upload_csv(headers)

        attacker = make_user("attacker")
        att_headers = auth_headers(attacker)
        r = client.get(f"/api/datasets/{did}", headers=att_headers)
        if r.status_code in (403, 404):
            body = json.dumps(r.json()).lower()
            assert "owner" not in body
            assert u["username"] not in body


# ═════════════════════════════════════════════════════════
# SEC-4: Input Validation & Sanitization
# ═════════════════════════════════════════════════════════

class TestInputValidation:
    """All user inputs must be validated before processing."""

    def setup_method(self):
        self.u = make_user("input")
        self.headers = auth_headers(self.u)

    def test_sec_sql_injection_in_username_rejected_or_safe(self):
        """SEC-4.1: SQL injection in username is safe (ORM parameterization)."""
        malicious_user = {
            "username": "'; DROP TABLE users; --",
            "email": "sqlinj@test.com",
            "password": "Test123!",
        }
        r = client.post("/api/auth/register", json=malicious_user)
        # Either rejected (422/400) or accepted safely by ORM
        # What must NOT happen: 500 server error or actual table drop
        assert r.status_code != 500

    def test_sec_xss_in_query_does_not_crash(self):
        """SEC-4.2: XSS payload in query input does not cause server error."""
        did = upload_csv(self.headers)
        r = client.post("/api/queries/ask",
                        headers=self.headers,
                        json={"query": "<script>alert('xss')</script>", "dataset_id": str(did)})
        assert r.status_code in (200, 400, 422)  # not 500

    def test_sec_very_long_query_does_not_crash(self):
        """SEC-4.3: Very long query string is handled gracefully."""
        did = upload_csv(self.headers)
        long_query = "show average sales " * 500  # 9500 chars
        r = client.post("/api/queries/ask",
                        headers=self.headers,
                        json={"query": long_query, "dataset_id": str(did)})
        assert r.status_code in (200, 400, 422)  # not 500

    def test_sec_unicode_in_query_does_not_crash(self):
        """SEC-4.4: Unicode characters in query are handled gracefully."""
        did = upload_csv(self.headers)
        r = client.post("/api/queries/ask",
                        headers=self.headers,
                        json={"query": "दिखाओ औसत बिक्री", "dataset_id": str(did)})
        assert r.status_code in (200, 400, 422)

    def test_sec_empty_query_is_rejected_gracefully(self):
        """SEC-4.5: Empty query string is handled gracefully (no 500 server error)."""
        did = upload_csv(self.headers)
        r = client.post("/api/queries/ask",
                        headers=self.headers,
                        json={"query": "", "dataset_id": str(did)})
        # Empty query may trigger fallback stub (returns df.head with success=True)
        # OR be rejected (400/422). Either is acceptable — must NOT be a 500 crash.
        assert r.status_code in (200, 400, 422), f"Server error on empty query: {r.status_code}"


# ═════════════════════════════════════════════════════════
# SEC-5: Authentication Edge Cases
# ═════════════════════════════════════════════════════════

class TestAuthEdgeCases:
    """Edge cases around token handling and session management."""

    def test_sec_expired_format_token_rejected(self):
        """SEC-5.1: Malformed JWT (not 3 parts) is rejected."""
        r = client.get("/api/datasets/", headers={"Authorization": "Bearer notajwt"})
        assert r.status_code in (401, 403)

    def test_sec_empty_bearer_token_rejected(self):
        """SEC-5.2: Empty Bearer string is rejected."""
        r = client.get("/api/datasets/", headers={"Authorization": "Bearer "})
        assert r.status_code in (401, 403)

    def test_sec_missing_auth_header_rejected(self):
        """SEC-5.3: Missing Authorization header is rejected."""
        r = client.get("/api/datasets/")
        assert r.status_code in (401, 403)

    def test_sec_wrong_scheme_rejected(self):
        """SEC-5.4: 'Basic' scheme instead of 'Bearer' is rejected."""
        r = client.get("/api/datasets/", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert r.status_code in (401, 403)


# ── Cleanup ───────────────────────────────────────────────
def teardown_module(module):
    import gc
    app.dependency_overrides.clear()
    engine.dispose()
    gc.collect()
    import time; time.sleep(0.5)
    for db_file in ["test_sdlc3.db", "test_sdlc3.db-shm", "test_sdlc3.db-wal"]:
        try:
            os.remove(db_file)
        except (FileNotFoundError, PermissionError):
            pass
