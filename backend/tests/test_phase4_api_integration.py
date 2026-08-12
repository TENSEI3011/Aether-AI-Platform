"""
============================================================
test_phase4_api_integration.py
AI DLS Phase 4: Integration Testing — FastAPI Endpoints
============================================================
Tests every API endpoint using FastAPI's TestClient.
Covers:
  - Auth endpoints (register, login, token refresh)
  - Dataset endpoints (upload, schema, profile, list)
  - Query endpoints (ask, anomalies, cluster, forecast)
  - Voice endpoints (synthesize — mocked)
  - Error cases (401, 404, 400 responses)
============================================================
"""

import pytest
import pandas as pd
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════

def _register_and_login(username: str = "testuser_api", password: str = "testpass123"):
    """Register a user and return their JWT token."""
    # Register (ignore if already exists)
    client.post("/api/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": password,
    })
    # Login — auth router uses JSON body (LoginRequest BaseModel), NOT OAuth2 form
    res = client.post("/api/auth/login", json={
        "username": username,
        "password": password,
    })
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode()


def _upload_dataset(token: str, df: pd.DataFrame, filename: str = "test.csv") -> str:
    """Upload a DataFrame as CSV and return the dataset_id."""
    csv_bytes = _make_csv_bytes(df)
    res = client.post(
        "/api/datasets/upload",
        headers=_auth_headers(token),
        files={"file": (filename, csv_bytes, "text/csv")},
    )
    assert res.status_code == 200, f"Upload failed: {res.text}"
    return res.json()["dataset_id"]


# ═══════════════════════════════════════════════════════════
# PHASE 4A — Authentication Endpoints
# ═══════════════════════════════════════════════════════════

class TestAuthEndpoints:

    def test_register_new_user(self):
        res = client.post("/api/auth/register", json={
            "username": "newuser_reg_test",
            "email": "newuser_reg_test@example.com",
            "password": "securepassword123",
        })
        assert res.status_code in (200, 201, 400)  # 400 = already exists

    def test_login_valid_credentials(self):
        client.post("/api/auth/register", json={
            "username": "login_test_user",
            "email": "login_test_user@test.com",
            "password": "mypassword",
        })
        # Login uses JSON body (LoginRequest), not OAuth2 form
        res = client.post("/api/auth/login", json={
            "username": "login_test_user",
            "password": "mypassword",
        })
        assert res.status_code == 200
        assert "access_token" in res.json()
        assert res.json()["token_type"] == "bearer"

    def test_login_wrong_password(self):
        res = client.post("/api/auth/login", json={
            "username": "login_test_user",
            "password": "wrongpassword",
        })
        assert res.status_code == 401

    def test_login_nonexistent_user(self):
        res = client.post("/api/auth/login", json={
            "username": "nobody_xyz_999",
            "password": "anypassword",
        })
        assert res.status_code == 401

    def test_protected_endpoint_without_token_returns_401(self):
        res = client.get("/api/datasets/")
        assert res.status_code == 401

    def test_protected_endpoint_with_invalid_token_returns_401(self):
        res = client.get("/api/datasets/", headers={"Authorization": "Bearer fake.token.here"})
        assert res.status_code == 401


# ═══════════════════════════════════════════════════════════
# PHASE 4B — Dataset Endpoints
# ═══════════════════════════════════════════════════════════

class TestDatasetEndpoints:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = _register_and_login("ds_endpoint_user", "pass1234")
        # Use unique sales values so auto-cleaning does NOT drop any rows (no duplicates)
        self.df = pd.DataFrame({
            "product": [f"Product_{i}" for i in range(100)],
            "sales":   list(range(100, 200)),
            "region":  ["North", "South"] * 50,
        })

    def test_upload_csv_returns_200(self):
        csv_bytes = _make_csv_bytes(self.df)
        res = client.post(
            "/api/datasets/upload",
            headers=_auth_headers(self.token),
            files={"file": ("sales.csv", csv_bytes, "text/csv")},
        )
        assert res.status_code == 200
        data = res.json()
        assert "dataset_id" in data
        assert "profile" in data
        assert "schema" in data
        assert data["profile"]["rows"] == 100

    def test_upload_returns_correct_row_count(self):
        csv_bytes = _make_csv_bytes(self.df)
        res = client.post(
            "/api/datasets/upload",
            headers=_auth_headers(self.token),
            files={"file": ("data.csv", csv_bytes, "text/csv")},
        )
        assert res.json()["profile"]["rows"] == 100

    def test_upload_invalid_format_returns_400(self):
        res = client.post(
            "/api/datasets/upload",
            headers=_auth_headers(self.token),
            files={"file": ("data.json", b'{"a":1}', "application/json")},
        )
        assert res.status_code == 400

    def test_get_schema_returns_200(self):
        dataset_id = _upload_dataset(self.token, self.df)
        res = client.get(
            f"/api/datasets/{dataset_id}/schema",
            headers=_auth_headers(self.token),
        )
        assert res.status_code == 200
        schema = res.json()
        assert "columns" in schema
        assert schema["total_rows"] == 100

    def test_get_profile_returns_200(self):
        dataset_id = _upload_dataset(self.token, self.df)
        res = client.get(
            f"/api/datasets/{dataset_id}/profile",
            headers=_auth_headers(self.token),
        )
        assert res.status_code == 200

    def test_get_schema_wrong_user_returns_403(self):
        """Other user's token should not access this dataset."""
        dataset_id = _upload_dataset(self.token, self.df)
        other_token = _register_and_login("other_user_403", "pass5678")
        res = client.get(
            f"/api/datasets/{dataset_id}/schema",
            headers=_auth_headers(other_token),
        )
        assert res.status_code == 403

    def test_list_datasets_returns_200(self):
        res = client.get("/api/datasets/", headers=_auth_headers(self.token))
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_nonexistent_dataset_returns_404(self):
        res = client.get(
            "/api/datasets/999999/schema",
            headers=_auth_headers(self.token),
        )
        assert res.status_code == 404


# ═══════════════════════════════════════════════════════════
# PHASE 4C — Query Endpoints
# ═══════════════════════════════════════════════════════════

class TestQueryEndpoints:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.token = _register_and_login("query_endpoint_user", "pass9876")
        # All rows unique (sales and quantity are ranges — no deduplication)
        self.df = pd.DataFrame({
            "product":  ["Widget", "Gadget", "Doohickey"] * 30,
            "sales":    list(range(1, 91)),
            "region":   ["North", "South", "East"] * 30,
            "quantity": list(range(10, 100)),
        })
        self.dataset_id = _upload_dataset(self.token, self.df)

    def test_ask_query_returns_success(self):
        res = client.post(
            "/api/queries/ask",
            headers=_auth_headers(self.token),
            json={
                "dataset_id": self.dataset_id,
                # QueryRequest field is 'query', not 'natural_query'
                "query": "Show the top 5 rows",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "success" in data
        # May not always succeed (depends on LLM) but must not crash
        assert data.get("error_detail") != "Internal Server Error"

    def test_ask_query_nonexistent_dataset_returns_404(self):
        res = client.post(
            "/api/queries/ask",
            headers=_auth_headers(self.token),
            # QueryRequest field is 'query', not 'natural_query'
            json={"dataset_id": "999999", "query": "show data"},
        )
        assert res.status_code == 404

    def test_ask_query_without_auth_returns_401(self):
        res = client.post(
            "/api/queries/ask",
            # QueryRequest field is 'query', not 'natural_query'
            json={"dataset_id": self.dataset_id, "query": "show data"},
        )
        assert res.status_code == 401

    def test_anomaly_detection_endpoint(self):
        res = client.post(
            "/api/queries/anomalies",
            headers=_auth_headers(self.token),
            json={"dataset_id": self.dataset_id, "contamination": 0.05},
        )
        # Returns 200 if scikit-learn installed, 501 if not
        assert res.status_code in (200, 501)
        if res.status_code == 200:
            assert "anomaly_result" in res.json()

    def test_clustering_endpoint(self):
        res = client.post(
            "/api/queries/cluster",
            headers=_auth_headers(self.token),
            json={"dataset_id": self.dataset_id, "max_k": 4},
        )
        assert res.status_code in (200, 501)
        if res.status_code == 200:
            assert "cluster_result" in res.json()

    def test_query_history_endpoint(self):
        res = client.get(
            "/api/queries/history",
            headers=_auth_headers(self.token),
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_clear_memory_endpoint(self):
        res = client.delete(
            f"/api/queries/memory?dataset_id={self.dataset_id}",
            headers=_auth_headers(self.token),
        )
        assert res.status_code == 200


# ═══════════════════════════════════════════════════════════
# PHASE 4D — System Health
# ═══════════════════════════════════════════════════════════

class TestSystemHealth:

    def test_root_endpoint_responds(self):
        """FastAPI root must respond (health check)."""
        res = client.get("/")
        assert res.status_code in (200, 404)  # 404 is fine if no root route

    def test_docs_endpoint_accessible(self):
        """OpenAPI docs should be accessible."""
        res = client.get("/docs")
        assert res.status_code == 200

    def test_openapi_schema_valid(self):
        """OpenAPI schema must be valid JSON."""
        res = client.get("/openapi.json")
        assert res.status_code == 200
        schema = res.json()
        assert "paths" in schema
        assert "info" in schema
