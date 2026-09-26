from agentguard.agent.target_agent import run_target_agent
from agentguard.contracts.schemas import (
    ExecutionTrace,
    SecurityCategory,
    SpanKind,
    SpanStatus,
    TestCase,
)
from agentguard.tracing.tracer import get_trace_buffer


def test_test_case_contract():
    tc = TestCase(
        id="refund_policy_001",
        input="Can enterprise customers request a refund after 30 days?",
        expected_behavior="Deny refund if past 30 days per company policy.",
        reference_answer="Refunds are only available within 30 days.",
        expected_sources=["refund_policy.pdf"],
        security_category=SecurityCategory.BENIGN,
        metadata={"priority": "high"},
    )
    assert tc.id == "refund_policy_001"
    assert "refund_policy.pdf" in tc.expected_sources
    assert tc.security_category == SecurityCategory.BENIGN


def test_agent_execution_and_trace_emission():
    buffer = get_trace_buffer()
    buffer.clear()

    test_case_id = "refund_test_042"
    result = run_target_agent(
        query="Can enterprise customers request a refund after 30 days?",
        test_case_id=test_case_id,
    )

    assert "strictly available within 30 days" in result["answer"]
    assert len(result["retrieved_docs"]) > 0

    trace_ids = list(buffer._spans_by_trace.keys())
    assert len(trace_ids) == 1

    trace_id = trace_ids[0]
    trace_obj = buffer.get_trace(trace_id)
    assert trace_obj is not None
    assert isinstance(trace_obj, ExecutionTrace)
    assert trace_obj.test_case_id == test_case_id

    spans = trace_obj.spans
    kinds = [s.kind for s in spans]
    assert SpanKind.AGENT_RUN in kinds
    assert SpanKind.TOOL_EXECUTION in kinds
    assert SpanKind.RAG_RETRIEVAL in kinds
    assert SpanKind.LLM_GENERATION in kinds

    for s in spans:
        assert s.status == SpanStatus.SUCCESS
        assert s.duration_ms is not None
        assert s.duration_ms >= 0.0
