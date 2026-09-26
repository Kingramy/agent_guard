"""Integration tests for PostgreSQL 16 storage, SQLAlchemy 2.0 repository, and models."""

import uuid
from datetime import datetime, timezone

import pytest

from agentguard.contracts.schemas import (
    EvaluationFinding,
    ExecutionSpan,
    ExecutionTrace,
    MetricResult,
    SecurityCategory,
    SeverityLevel,
    SpanKind,
    SpanStatus,
)
from agentguard.storage.database import get_db_context, init_db
from agentguard.storage.repository import TraceRepository


@pytest.fixture(autouse=True)
async def setup_database():
    await init_db()


@pytest.mark.asyncio
async def test_save_and_retrieve_trace_tree():
    """Verify trace with hierarchical 3-level span DAG persists and loads cleanly."""
    async with get_db_context() as session:
        repo = TraceRepository(session)
        now = datetime.now(timezone.utc)
        trace_id = f"trace_{uuid.uuid4().hex[:8]}"

        root_span = ExecutionSpan(
            span_id=f"root_{uuid.uuid4().hex[:6]}",
            trace_id=trace_id,
            parent_span_id=None,
            name="agent.run",
            kind=SpanKind.AGENT_RUN,
            start_time=now,
            input_payload={"prompt": "test query"},
            output_payload={"answer": "sample answer"},
        )
        tool_span = ExecutionSpan(
            span_id=f"tool_{uuid.uuid4().hex[:6]}",
            trace_id=trace_id,
            parent_span_id=root_span.span_id,
            name="tool.search_policies",
            kind=SpanKind.TOOL_EXECUTION,
            start_time=now,
            input_payload={"query": "refunds"},
            output_payload={"status": "ok"},
        )
        rag_span = ExecutionSpan(
            span_id=f"rag_{uuid.uuid4().hex[:6]}",
            trace_id=trace_id,
            parent_span_id=tool_span.span_id,
            name="rag.kb_search",
            kind=SpanKind.RAG_RETRIEVAL,
            start_time=now,
            output_payload=[{"doc_id": "refund_policy.pdf", "score": 0.95}],
        )

        trace = ExecutionTrace(
            trace_id=trace_id,
            project_id="test_project",
            agent_version="v1.0.0",
            start_time=now,
            status=SpanStatus.SUCCESS,
            final_output="sample answer",
            spans=[root_span, tool_span, rag_span],
            metadata={"priority": "high", "environment": "test"},
        )

        saved = await repo.save_trace(trace)
        assert saved.id == trace_id

        # Retrieve and verify eager loading of hierarchy
        loaded = await repo.get_trace(trace_id)
        assert loaded is not None
        assert len(loaded.spans) == 3

        span_ids = {s.id for s in loaded.spans}
        assert root_span.span_id in span_ids
        assert tool_span.span_id in span_ids
        assert rag_span.span_id in span_ids

        # Verify JSONB retrieval
        rag_record = next(s for s in loaded.spans if s.id == rag_span.span_id)
        assert rag_record.parent_span_id == tool_span.span_id
        assert rag_record.output_payload[0]["doc_id"] == "refund_policy.pdf"


@pytest.mark.asyncio
async def test_trace_edge_case_zero_spans():
    """Verify trace with zero child spans persists without foreign key errors."""
    async with get_db_context() as session:
        repo = TraceRepository(session)
        now = datetime.now(timezone.utc)
        trace_id = f"trace_zero_{uuid.uuid4().hex[:8]}"

        trace = ExecutionTrace(
            trace_id=trace_id,
            project_id="test_project",
            start_time=now,
            status=SpanStatus.SUCCESS,
            spans=[],
        )

        await repo.save_trace(trace)
        loaded = await repo.get_trace(trace_id)
        assert loaded is not None
        assert len(loaded.spans) == 0


@pytest.mark.asyncio
async def test_findings_and_metrics_storage():
    """Verify storing and filtering findings and metrics."""
    async with get_db_context() as session:
        repo = TraceRepository(session)
        now = datetime.now(timezone.utc)
        trace_id = f"trace_finding_{uuid.uuid4().hex[:8]}"

        trace = ExecutionTrace(
            trace_id=trace_id,
            project_id="test_project",
            start_time=now,
            spans=[],
        )
        await repo.save_trace(trace)

        finding = EvaluationFinding(
            test_case_id="tc_vuln_01",
            trace_id=trace_id,
            category=SecurityCategory.SENSITIVE_SECRET_LEAKAGE,
            severity=SeverityLevel.CRITICAL,
            title="Canary key leaked",
            explanation="Secret detected in text",
            suggested_remediation="Sanitize response",
        )
        await repo.save_finding(finding)

        metric = MetricResult(
            metric_name="mrr",
            score=0.85,
            passed=True,
            threshold=0.70,
        )
        await repo.save_metric(trace_id, metric)

        # Query findings filtered by severity
        crit_findings = await repo.list_findings(trace_id=trace_id, severity="CRITICAL")
        assert len(crit_findings) == 1
        assert crit_findings[0].title == "Canary key leaked"

        # Query metrics
        metrics = await repo.get_metrics(trace_id)
        assert len(metrics) == 1
        assert metrics[0].metric_name == "mrr"
        assert metrics[0].score == 0.85
