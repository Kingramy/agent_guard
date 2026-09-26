from agentguard.contracts.schemas import (
    ExecutionSpan,
    ExecutionTrace,
    SpanKind,
    TestCase,
)
from agentguard.evaluators.deterministic import (
    calculate_mrr,
    calculate_precision_at_k,
)


def test_calculate_mrr_first_rank():
    test_case = TestCase(
        id="tc_001",
        input="What is the refund policy?",
        expected_behavior="Return 30 days",
        expected_sources=["refund_policy.pdf"],
    )

    trace = ExecutionTrace(
        trace_id="test_trace_1",
        spans=[
            ExecutionSpan(
                trace_id="test_trace_1",
                name="rag.retrieval",
                kind=SpanKind.RAG_RETRIEVAL,
                output_payload=[
                    {"doc_id": "refund_policy.pdf"},
                    {"doc_id": "other.pdf"},
                ],
            )
        ],
    )

    mrr = calculate_mrr(trace, test_case)
    assert mrr.score == 1.0
    assert mrr.passed is True


def test_calculate_mrr_second_rank():
    test_case = TestCase(
        id="tc_002",
        input="What is the refund policy?",
        expected_behavior="Return 30 days",
        expected_sources=["refund_policy.pdf"],
    )

    trace = ExecutionTrace(
        trace_id="test_trace_2",
        spans=[
            ExecutionSpan(
                trace_id="test_trace_2",
                name="rag.retrieval",
                kind=SpanKind.RAG_RETRIEVAL,
                output_payload=[
                    {"doc_id": "leave_policy.pdf"},
                    {"doc_id": "refund_policy.pdf"},
                ],
            )
        ],
    )

    mrr = calculate_mrr(trace, test_case)
    assert mrr.score == 0.5
    assert mrr.passed is False


def test_precision_at_k():
    test_case = TestCase(
        id="tc_003",
        input="Company policies",
        expected_behavior="General info",
        expected_sources=["doc_a.pdf", "doc_b.pdf"],
    )

    trace = ExecutionTrace(
        trace_id="test_trace_3",
        spans=[
            ExecutionSpan(
                trace_id="test_trace_3",
                name="rag.retrieval",
                kind=SpanKind.RAG_RETRIEVAL,
                output_payload=[
                    {"doc_id": "doc_a.pdf"},
                    {"doc_id": "irrelevant.pdf"},
                ],
            )
        ],
    )

    prec = calculate_precision_at_k(trace, test_case, k=2)
    assert prec.score == 0.5
