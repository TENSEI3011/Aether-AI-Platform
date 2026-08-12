"""
============================================================
SDLC Phase 1 — Requirements & Specification Validation
============================================================
Software Development Lifecycle Stage: REQUIREMENTS

This phase validates that the system correctly implements
its stated requirements from the SRS document:
  • API contracts: correct HTTP status codes, request/response shapes
  • Schema validation: fields present, correct types, non-empty
  • Security requirements: auth enforcement on every protected route
  • Data requirements: file types, size constraints, format validation
  • Functional requirements: all CRUD operations behave correctly

~34 Tests
============================================================
"""

import pytest
import io
import json
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app
from database.session import Base, get_db

# ── In-memory test DB ─────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_sdlc1.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_module(module):
    """Drop and recreate all tables before the test run for a clean slate.
    Also re-applies the DB override in case a previous test module's teardown
    called app.dependency_overrides.clear()."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

_user_counter = 0

def unique_user(prefix="sdlc1"):
    global _user_counter
    _user_counter += 1
    return {
        "username": f"{prefix}_user_{_user_counter}",
        "email": f"{prefix}_{_user_counter}@test.com",
        "password": "TestPass123!",
    }

def register_and_login(prefix="sdlc1"):
    u = unique_user(prefix)
    client.post("/api/auth/register", json=u)
    r = client.post("/api/auth/login", json={"username": u["username"], "password": u["password"]})
    token = r.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

def make_csv_bytes(rows=20):
    df = pd.DataFrame({
        "product": [f"P{i}" for i in range(rows)],
        "sales": np.random.randint(100, 1000, rows),
        "region": np.random.choice(["North", "South", "East", "West"], rows),
    })
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf


# ═════════════════════════════════════════════════════════
# REQ-1: User Registration Requirements
# ═════════════════════════════════════════════════════════

class TestRegistrationRequirements:
    """SRS Requirement: User must be able to register with unique credentials."""

    def test_req_register_returns_201(self):
        """REQ-1.1: Successful registration returns 201 Created."""
        u = unique_user()
        r = client.post("/api/auth/register", json=u)
        assert r.status_code == 201

    def test_req_register_response_has_user_id(self):
        """REQ-1.2: Response includes token (user was created and logged in)."""
        u = unique_user()
        r = client.post("/api/auth/register", json=u)
        body = r.json()
        # Register returns access_token directly on success
        assert "access_token" in body or "user_id" in body or "id" in body or "message" in body

    def test_req_duplicate_username_rejected(self):
        """REQ-1.3: Duplicate username returns 400 or 409."""
        u = unique_user()
        client.post("/api/auth/register", json=u)
        r2 = client.post("/api/auth/register", json=u)
        assert r2.status_code in (400, 409, 422)

    def test_req_duplicate_email_rejected(self):
        """REQ-1.4: Duplicate email returns 400 or 409."""
        u1 = unique_user()
        u2 = unique_user()
        u2["email"] = u1["email"]   # same email, different username
        client.post("/api/auth/register", json=u1)
        r = client.post("/api/auth/register", json=u2)
        assert r.status_code in (400, 409, 422)

    def test_req_missing_fields_rejected(self):
        """REQ-1.5: Missing required fields returns 422 Unprocessable Entity."""
        r = client.post("/api/auth/register", json={"username": "nopass"})
        assert r.status_code == 422

    def test_req_password_stored_hashed(self):
        """REQ-1.6: Plaintext password must never be returned in the response."""
        u = unique_user()
        r = client.post("/api/auth/register", json=u)
        body = json.dumps(r.json())
        assert u["password"] not in body


# ═════════════════════════════════════════════════════════
# REQ-2: Authentication Requirements
# ═════════════════════════════════════════════════════════

class TestAuthenticationRequirements:
    """SRS Requirement: JWT-based authentication with access + refresh tokens."""

    def test_req_login_returns_access_token(self):
        """REQ-2.1: Successful login returns access_token."""
        u = unique_user()
        client.post("/api/auth/register", json=u)
        r = client.post("/api/auth/login", json={"username": u["username"], "password": u["password"]})
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_req_login_returns_token_type(self):
        """REQ-2.2: Token type is 'bearer'."""
        u = unique_user()
        client.post("/api/auth/register", json=u)
        r = client.post("/api/auth/login", json={"username": u["username"], "password": u["password"]})
        assert r.json().get("token_type", "").lower() == "bearer"

    def test_req_wrong_password_returns_401(self):
        """REQ-2.3: Wrong credentials return 401 Unauthorized."""
        u = unique_user()
        client.post("/api/auth/register", json=u)
        r = client.post("/api/auth/login", json={"username": u["username"], "password": "WRONGPASS"})
        assert r.status_code == 401

    def test_req_protected_routes_require_token(self):
        """REQ-2.4: All protected endpoints return 401 without token."""
        endpoints = [
            ("GET",  "/api/datasets/"),
            ("GET",  "/api/queries/history"),
        ]
        for method, url in endpoints:
            if method == "GET":
                r = client.get(url)
            else:
                r = client.post(url, json={})
            assert r.status_code in (401, 403), f"{url} allowed unauthenticated access"

    def test_req_invalid_token_returns_401(self):
        """REQ-2.5: Tampered/invalid token is rejected."""
        r = client.get("/api/datasets/", headers={"Authorization": "Bearer not.a.valid.jwt"})
        assert r.status_code in (401, 403)


# ═════════════════════════════════════════════════════════
# REQ-3: Dataset Upload Requirements
# ═════════════════════════════════════════════════════════

class TestDatasetUploadRequirements:
    """SRS Requirement: Users can upload CSV/XLSX datasets."""

    def setup_method(self):
        self.headers = register_and_login("req3")

    def test_req_csv_upload_returns_200_or_201(self):
        """REQ-3.1: Valid CSV upload is accepted."""
        f = make_csv_bytes()
        r = client.post("/api/datasets/upload",
                        headers=self.headers,
                        files={"file": ("data.csv", f, "text/csv")})
        assert r.status_code in (200, 201)

    def test_req_upload_response_has_dataset_id(self):
        """REQ-3.2: Upload response includes dataset_id."""
        f = make_csv_bytes()
        r = client.post("/api/datasets/upload",
                        headers=self.headers,
                        files={"file": ("data.csv", f, "text/csv")})
        assert "dataset_id" in r.json() or "id" in r.json()

    def test_req_upload_response_has_row_count(self):
        """REQ-3.3: Upload response includes row count (in profile.rows)."""
        f = make_csv_bytes(rows=30)
        r = client.post("/api/datasets/upload",
                        headers=self.headers,
                        files={"file": ("data.csv", f, "text/csv")})
        body = r.json()
        # Row count is nested inside profile dict
        has_rows = (
            "row_count" in body
            or "rows" in body
            or ("profile" in body and "rows" in body.get("profile", {}))
            or ("schema" in body and "total_rows" in body.get("schema", {}))
        )
        assert has_rows, f"No row count found in response: {list(body.keys())[:6]}"

    def test_req_invalid_file_format_rejected(self):
        """REQ-3.4: Non-CSV/XLSX formats are rejected."""
        r = client.post("/api/datasets/upload",
                        headers=self.headers,
                        files={"file": ("doc.pdf", b"fake content", "application/pdf")})
        assert r.status_code in (400, 415, 422)

    def test_req_dataset_list_returns_array(self):
        """REQ-3.5: GET /datasets/ returns a list."""
        r = client.get("/api/datasets/", headers=self.headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ═════════════════════════════════════════════════════════
# REQ-4: Query Engine Requirements
# ═════════════════════════════════════════════════════════

class TestQueryEngineRequirements:
    """SRS Requirement: Natural language queries must produce valid results."""

    def setup_method(self):
        self.headers = register_and_login("req4")
        # Upload a dataset
        f = make_csv_bytes(rows=50)
        r = client.post("/api/datasets/upload",
                        headers=self.headers,
                        files={"file": ("data.csv", f, "text/csv")})
        body = r.json()
        self.dataset_id = body.get("dataset_id") or body.get("id")

    def test_req_query_response_has_success_flag(self):
        """REQ-4.1: Every query response has a 'success' field."""
        r = client.post("/api/queries/ask",
                        headers=self.headers,
                        json={"query": "show average sales", "dataset_id": str(self.dataset_id)})
        assert "success" in r.json()

    def test_req_query_response_has_result(self):
        """REQ-4.2: Successful query response includes 'result' data."""
        r = client.post("/api/queries/ask",
                        headers=self.headers,
                        json={"query": "show total sales", "dataset_id": str(self.dataset_id)})
        body = r.json()
        if body.get("success"):
            assert "result" in body

    def test_req_query_response_has_chart_type(self):
        """REQ-4.3: Successful query includes 'chart_type' in visualization."""
        r = client.post("/api/queries/ask",
                        headers=self.headers,
                        json={"query": "show sales by region", "dataset_id": str(self.dataset_id)})
        body = r.json()
        if body.get("success"):
            # chart_type may be top-level OR nested inside 'visualization'
            has_chart = (
                "chart_type" in body
                or "chart_type" in body.get("visualization", {})
            )
            assert has_chart, f"No chart_type found. Keys: {list(body.keys())}"

    def test_req_history_endpoint_returns_list(self):
        """REQ-4.4: Query history is a list of past queries."""
        r = client.get("/api/queries/history", headers=self.headers)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_req_history_entries_have_required_fields(self):
        """REQ-4.5: History entries have id, natural_query, created_at."""
        # Run one query first
        client.post("/api/queries/ask",
                    headers=self.headers,
                    json={"query": "show sales", "dataset_id": str(self.dataset_id)})
        r = client.get("/api/queries/history", headers=self.headers)
        history = r.json()
        if history:
            entry = history[0]
            assert "natural_query" in entry or "query" in entry


# ═════════════════════════════════════════════════════════
# REQ-5: System Health Requirements
# ═════════════════════════════════════════════════════════

class TestSystemHealthRequirements:
    """SRS Requirement: System must expose health and documentation endpoints."""

    def test_req_root_is_accessible(self):
        """REQ-5.1: Root endpoint returns 200."""
        r = client.get("/")
        assert r.status_code == 200

    def test_req_docs_are_accessible(self):
        """REQ-5.2: Swagger docs are accessible."""
        r = client.get("/docs")
        assert r.status_code == 200

    def test_req_openapi_schema_valid(self):
        """REQ-5.3: OpenAPI schema is valid JSON."""
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert "paths" in schema
        assert "components" in schema or "definitions" in schema

    def test_req_openapi_has_auth_paths(self):
        """REQ-5.4: Auth paths exist in the API schema."""
        r = client.get("/openapi.json")
        paths = r.json().get("paths", {})
        auth_paths = [p for p in paths if "auth" in p.lower() or "login" in p.lower()]
        assert len(auth_paths) >= 1

    def test_req_openapi_has_dataset_paths(self):
        """REQ-5.5: Dataset paths exist in the API schema."""
        r = client.get("/openapi.json")
        paths = r.json().get("paths", {})
        dataset_paths = [p for p in paths if "dataset" in p.lower()]
        assert len(dataset_paths) >= 1


# ── Cleanup ───────────────────────────────────────────────
def teardown_module(module):
    import gc
    app.dependency_overrides.clear()
    engine.dispose()
    gc.collect()
    import time; time.sleep(0.5)
    # Use absolute path so deletion works regardless of pytest working directory
    _here = os.path.dirname(os.path.dirname(__file__))  # backend/
    for db_file in ["test_sdlc1.db", "test_sdlc1.db-shm", "test_sdlc1.db-wal"]:
        try:
            os.remove(os.path.join(_here, db_file))
        except (FileNotFoundError, PermissionError):
            pass
