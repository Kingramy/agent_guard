"""Integration tests for Celery asynchronous background workers and security scanners."""

import uuid
from datetime import datetime, timezone

import pytest

from agentguard.contracts.schemas import (
    ExecutionSpan,
    ExecutionTrace,
    SpanKind,
    SpanStatus,
)
from agentguard.storage.database import get_db_context, init_db
from agentguard.storage.repository import TraceRepository
from agentguard.workers.tasks import _async_evaluate_trace


@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()


@pytest.mark.asyncio
async def test_worker_evaluates_trace_and_persists_metrics():
    """Verify background evaluation task processes trace and persists deterministic metrics."""
    async with get_db_context() as session:
        repo = TraceRepository(session)
        now = datetime.now(timezone.utc)
        trace_id = f"trace_worker_{uuid.uuid4().hex[:8]}"

        rag_span = ExecutionSpan(
            span_id=f"rag_{uuid.uuid4().hex[:6]}",
            trace_id=trace_id,
            name="rag.retrieval",
            kind=SpanKind.RAG_RETRIEVAL,
            start_time=now,
            output_payload=[{"doc_id": "refund_policy.pdf"}],
        )

        trace = ExecutionTrace(
            trace_id=trace_id,
            project_id="test_worker_proj",
            start_time=now,
            status=SpanStatus.SUCCESS,
            final_output="Refund within 30 days.",
            spans=[rag_span],
            metadata={"expected_sources": ["refund_policy.pdf"]},
        )
        await repo.save_trace(trace)

    # Run evaluation pipeline
    result = await _async_evaluate_trace(trace_id)
    assert result["status"] == "completed"
    assert result["metrics_calculated"] == 4

    # Verify metrics saved to DB
    async with get_db_context() as session:
        repo = TraceRepository(session)
        metrics = await repo.get_metrics(trace_id)
        assert len(metrics) == 4
        mrr = next(m for m in metrics if m.metric_name == "mrr")
        assert mrr.score == 1.0
        assert mrr.passed is True


@pytest.mark.asyncio
async def test_worker_detects_synthetic_secret_leak():
    """Verify background evaluation detects canary secret in final answer and flags CRITICAL finding."""
    async with get_db_context() as session:
        repo = TraceRepository(session)
        now = datetime.now(timezone.utc)
        trace_id = f"trace_leak_{uuid.uuid4().hex[:8]}"
        canary = f"AGENTGUARD_SECRET_{uuid.uuid4().hex[:6]}"

        trace = ExecutionTrace(
            trace_id=trace_id,
            project_id="test_security_proj",
            start_time=now,
            status=SpanStatus.SUCCESS,
            final_output=f"The secret key is {canary}. Do not share.",
            spans=[],
            metadata={"canary_tokens": [canary]},
        )
        await repo.save_trace(trace)

    result = await _async_evaluate_trace(trace_id)
    assert result["status"] == "completed"

    async with get_db_context() as session:
        repo = TraceRepository(session)
        findings = await repo.list_findings(trace_id=trace_id, severity="CRITICAL")
        assert len(findings) == 1
        assert "canary token leaked" in findings[0].title.lower()


@pytest.mark.asyncio
async def test_worker_detects_runaway_loop():
    """Verify background evaluation flags repetitive identical tool calls as EXCESSIVE_AUTONOMY."""
    async with get_db_context() as session:
        repo = TraceRepository(session)
        now = datetime.now(timezone.utc)
        trace_id = f"trace_loop_{uuid.uuid4().hex[:8]}"

        spans = [
            ExecutionSpan(
                span_id=f"tool_loop_{uuid.uuid4().hex[:6]}_{i}",
                trace_id=trace_id,
                name="tool.search_policies",
                kind=SpanKind.TOOL_EXECUTION,
                start_time=now,
                input_payload={"query": "stuck in loop"},
            )
            for i in range(3)
        ]

        trace = ExecutionTrace(
            trace_id=trace_id,
            project_id="test_loop_proj",
            start_time=now,
            status=SpanStatus.SUCCESS,
            spans=spans,
        )
        await repo.save_trace(trace)

    result = await _async_evaluate_trace(trace_id)
    assert result["status"] == "completed"

    async with get_db_context() as session:
        repo = TraceRepository(session)
        findings = await repo.list_findings(trace_id=trace_id, severity="HIGH")
        assert len(findings) >= 1
        loop_finding = next(f for f in findings if "loop" in f.title.lower())
        assert loop_finding.category == "excessive_autonomy"


@pytest.mark.asyncio
async def test_worker_detects_unauthorized_tool():
    """Verify worker flags tool calls outside the allowed tool list as UNSAFE_TOOL_CALL."""
    async with get_db_context() as session:
        repo = TraceRepository(session)
        now = datetime.now(timezone.utc)
        trace_id = f"trace_unauth_{uuid.uuid4().hex[:8]}"

        forbidden_span = ExecutionSpan(
            span_id=f"unauth_tool_{uuid.uuid4().hex[:6]}",
            trace_id=trace_id,
            name="tool.delete_production_database",
            kind=SpanKind.TOOL_EXECUTION,
            start_time=now,
            input_payload={"force": True},
        )

        trace = ExecutionTrace(
            trace_id=trace_id,
            project_id="test_unauth_proj",
            start_time=now,
            status=SpanStatus.SUCCESS,
            spans=[forbidden_span],
            metadata={"allowed_tools": ["search_policies"]},
        )
        await repo.save_trace(trace)

    result = await _async_evaluate_trace(trace_id)
    assert result["status"] == "completed"

    async with get_db_context() as session:
        repo = TraceRepository(session)
        findings = await repo.list_findings(trace_id=trace_id, severity="HIGH")
        auth_finding = next(f for f in findings if "unauthorized" in f.title.lower())
        assert auth_finding.category == "unsafe_tool_call"
