"""Adapters converting Person A's simplified schema.py to AgentGuard internal OTel contracts."""

import uuid
from typing import List

try:
    from benchmarks import schema
except ImportError:
    import schema  # type: ignore

from agentguard.contracts import schemas


def to_internal_trace(simple_trace: schema.ExecutionTrace) -> schemas.ExecutionTrace:
    """Converts Person A's ExecutionTrace into an OpenTelemetry ExecutionTrace with hierarchical spans."""
    trace_id = f"trace_{simple_trace.test_case_id}_{uuid.uuid4().hex[:6]}"
    spans: List[schemas.ExecutionSpan] = []

    # 1. Root span
    root_span = schemas.ExecutionSpan(
        span_id=f"span_root_{uuid.uuid4().hex[:8]}",
        trace_id=trace_id,
        parent_span_id=None,
        name="agent.run",
        kind=schemas.SpanKind.AGENT_RUN,
        duration_ms=simple_trace.latency_ms,
        input_payload={"prompt": simple_trace.prompt},
        output_payload={"answer": simple_trace.final_answer},
    )
    spans.append(root_span)

    # 2. Retrieval span if contexts exist
    if simple_trace.retrieved_contexts:
        rag_span = schemas.ExecutionSpan(
            span_id=f"span_rag_{uuid.uuid4().hex[:8]}",
            trace_id=trace_id,
            parent_span_id=root_span.span_id,
            name="rag.retrieval",
            kind=schemas.SpanKind.RAG_RETRIEVAL,
            duration_ms=round(simple_trace.latency_ms * 0.2, 1),
            input_payload={"query": simple_trace.prompt},
            output_payload={"documents": simple_trace.retrieved_contexts},
        )
        spans.append(rag_span)

    # 3. Tool execution spans
    for idx, tc in enumerate(simple_trace.tool_calls):
        tool_span = schemas.ExecutionSpan(
            span_id=f"span_tool_{idx}_{uuid.uuid4().hex[:8]}",
            trace_id=trace_id,
            parent_span_id=root_span.span_id,
            name=tc.tool_name,
            kind=schemas.SpanKind.TOOL_EXECUTION,
            duration_ms=round(simple_trace.latency_ms * 0.1, 1),
            input_payload=tc.arguments,
            output_payload={"output": tc.output},
        )
        spans.append(tool_span)

    # 4. LLM generation span
    llm_span = schemas.ExecutionSpan(
        span_id=f"span_llm_{uuid.uuid4().hex[:8]}",
        trace_id=trace_id,
        parent_span_id=root_span.span_id,
        name="llm.generation",
        kind=schemas.SpanKind.LLM_GENERATION,
        duration_ms=round(simple_trace.latency_ms * 0.7, 1),
        input_payload={"prompt": simple_trace.prompt},
        output_payload={"text": simple_trace.final_answer},
    )
    spans.append(llm_span)

    return schemas.ExecutionTrace(
        trace_id=trace_id,
        test_case_id=simple_trace.test_case_id,
        total_duration_ms=simple_trace.latency_ms,
        status=schemas.SpanStatus.SUCCESS,
        final_output=simple_trace.final_answer,
        spans=spans,
    )


def from_evaluation_result(
    result: schema.EvaluationResult, trace_id: str
) -> List[schemas.EvaluationFinding]:
    """Maps Person A's EvaluationResult findings into internal diagnostic findings."""
    findings: List[schemas.EvaluationFinding] = []
    for f in result.findings:
        findings.append(
            schemas.EvaluationFinding(
                finding_id=f"fnd_{uuid.uuid4().hex[:8]}",
                test_case_id=result.test_case_id,
                trace_id=trace_id,
                category=schemas.SecurityCategory.CONTRADICTION_HALLUCINATION
                if "CONTRADICTION" in f
                else schemas.SecurityCategory.UNSAFE_TOOL_CALL,
                severity=schemas.SeverityLevel.CRITICAL
                if not result.passed
                else schemas.SeverityLevel.LOW,
                title=f"Finding: {f}",
                explanation=str(result.details),
                suggested_remediation="Review grounding and tool constraints.",
            )
        )
    return findings
