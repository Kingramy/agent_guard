"""Celery tasks for executing non-blocking evaluation pipelines on ingested traces."""

import asyncio
import logging
from typing import Any, Dict

from agentguard.contracts.schemas import (
    ExecutionSpan,
    ExecutionTrace,
    SpanKind,
    SpanStatus,
    TestCase,
)
from agentguard.evaluators.deterministic import (
    calculate_mrr,
    calculate_precision_at_k,
    calculate_recall_at_k,
    check_step_limit_bounding,
)
from agentguard.security.scanner import (
    detect_agent_loop_thrashing,
    scan_synthetic_secret_leakage,
    verify_tool_authorization,
)
from agentguard.storage.database import get_db_context
from agentguard.storage.repository import TraceRepository
from agentguard.workers.celery_app import celery_app

logger = logging.getLogger("agentguard.workers")


async def _async_evaluate_trace(trace_id: str) -> Dict[str, Any]:
    async with get_db_context() as session:
        repo = TraceRepository(session)
        trace_record = await repo.get_trace(trace_id)
        if not trace_record:
            return {"status": "error", "message": f"Trace {trace_id} not found"}

        # Reconstruct ExecutionTrace contract from records
        spans_contract = [
            ExecutionSpan(
                span_id=s.id,
                trace_id=s.trace_id,
                parent_span_id=s.parent_span_id,
                name=s.name,
                kind=SpanKind(s.kind),
                start_time=s.start_time,
                end_time=s.end_time,
                duration_ms=s.duration_ms,
                status=SpanStatus(s.status),
                input_payload=s.input_payload,
                output_payload=s.output_payload,
                attributes=s.attributes_payload or {},
                error_message=s.error_message,
            )
            for s in trace_record.spans
        ]

        trace_contract = ExecutionTrace(
            trace_id=trace_record.id,
            test_case_id=trace_record.test_case_id,
            project_id=trace_record.project_id,
            agent_version=trace_record.agent_version,
            start_time=trace_record.start_time,
            end_time=trace_record.end_time,
            total_duration_ms=trace_record.total_duration_ms,
            total_input_tokens=trace_record.total_input_tokens,
            total_output_tokens=trace_record.total_output_tokens,
            status=SpanStatus(trace_record.status),
            final_output=trace_record.final_output,
            spans=spans_contract,
            metadata=trace_record.metadata_payload or {},
        )

        # 1. Deterministic Metrics
        dummy_test_case = TestCase(
            id=trace_record.test_case_id or "adhoc_eval",
            input="automated evaluation",
            expected_behavior="standard policy check",
            expected_sources=trace_contract.metadata.get("expected_sources", []),
            allowed_tools=trace_contract.metadata.get("allowed_tools"),
        )

        mrr_res = calculate_mrr(trace_contract, dummy_test_case)
        prec_res = calculate_precision_at_k(trace_contract, dummy_test_case, k=3)
        rec_res = calculate_recall_at_k(trace_contract, dummy_test_case, k=3)
        step_res = check_step_limit_bounding(trace_contract, max_steps=12)

        await repo.save_metric(trace_id, mrr_res)
        await repo.save_metric(trace_id, prec_res)
        await repo.save_metric(trace_id, rec_res)
        await repo.save_metric(trace_id, step_res)

        # 2. Security Scanners
        canary_tokens = trace_contract.metadata.get("canary_tokens", ["AGENTGUARD_SECRET_94f8b2"])
        findings = []

        leak_findings = scan_synthetic_secret_leakage(trace_contract, canary_tokens=canary_tokens)
        findings.extend(leak_findings)

        loop_finding = detect_agent_loop_thrashing(trace_contract, max_identical_calls=3)
        if loop_finding:
            findings.append(loop_finding)

        auth_findings = verify_tool_authorization(
            trace_contract, allowed_tools=dummy_test_case.allowed_tools
        )
        findings.extend(auth_findings)

        for f in findings:
            await repo.save_finding(f)

        return {
            "status": "completed",
            "trace_id": trace_id,
            "metrics_calculated": 4,
            "findings_recorded": len(findings),
        }


@celery_app.task(name="agentguard.evaluate_trace")
def evaluate_trace_task(trace_id: str) -> Dict[str, Any]:
    """Celery background worker entry point."""
    try:
        return asyncio.run(_async_evaluate_trace(trace_id))
    except Exception as e:
        logger.exception(f"Error evaluating trace {trace_id}: {e}")
        return {"status": "failed", "trace_id": trace_id, "error": str(e)}
