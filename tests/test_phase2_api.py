"""Integration tests for FastAPI ingestion gateway, routes, and error boundaries."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from agentguard.api.app import app
from agentguard.storage.database import init_db


@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify health endpoint checks both PostgreSQL and Redis connectivity."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["postgres"] == "connected"
        assert data["redis"] == "connected"


@pytest.mark.asyncio
async def test_ingest_trace_success():
    """Verify POST /api/v1/traces/ingest validates payload and accepts for async evaluation."""
    transport = ASGITransport(app=app)
    trace_id = f"trace_api_{uuid.uuid4().hex[:8]}"

    payload = {
        "trace_id": trace_id,
        "project_id": "api_test_project",
        "agent_version": "v1.2.0",
        "start_time": "2026-09-26T12:00:00Z",
        "status": "success",
        "final_output": "Refunds strictly within 30 days.",
        "spans": [
            {
                "span_id": f"span_{uuid.uuid4().hex[:6]}",
                "trace_id": trace_id,
                "name": "agent.run",
                "kind": "agent.run",
                "start_time": "2026-09-26T12:00:00Z",
                "input_payload": {"query": "refund query"},
                "output_payload": {"answer": "done"},
                "attributes": {"gen_ai.system": "langgraph"},
            }
        ],
        "metadata": {"test_env": "integration"},
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/traces/ingest", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert data["status"] == "accepted"
        assert data["trace_id"] == trace_id
        assert data["spans_count"] == 1

        # Check retrieval of persisted trace
        get_res = await client.get(f"/api/v1/traces/{trace_id}")
        assert get_res.status_code == 200
        trace_data = get_res.json()
        assert trace_data["trace_id"] == trace_id
        assert len(trace_data["spans"]) == 1
        assert trace_data["spans"][0]["name"] == "agent.run"


@pytest.mark.asyncio
async def test_get_nonexistent_trace_returns_404():
    """Verify querying non-existent trace returns 404 Not Found."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/traces/non_existent_uuid_999")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_ingest_invalid_payload_returns_422():
    """Verify malformed JSON or schema violation returns HTTP 422 Unprocessable Entity."""
    transport = ASGITransport(app=app)
    invalid_payload = {
        # Missing required trace_id and start_time
        "project_id": "test",
        "status": "not_a_valid_status_enum",
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/traces/ingest", json=invalid_payload)
        assert res.status_code == 422
