"""Deterministic Information Retrieval and tool execution evaluators.

Owned by Ramy (AI & Evaluation Lead).
"""

from typing import List

from agentguard.contracts.schemas import (
    ExecutionTrace,
    MetricResult,
    SpanKind,
    TestCase,
)


def calculate_mrr(trace: ExecutionTrace, test_case: TestCase) -> MetricResult:
    """Calculate Mean Reciprocal Rank (MRR) for retrieved documents against expected sources."""
    expected = set(test_case.expected_sources)
    if not expected:
        return MetricResult(
            metric_name="mrr",
            score=1.0,
            passed=True,
            threshold=0.70,
            details={"info": "No expected sources specified for this test case."},
        )

    retrieval_spans = [s for s in trace.spans if s.kind == SpanKind.RAG_RETRIEVAL]
    if not retrieval_spans:
        return MetricResult(
            metric_name="mrr",
            score=0.0,
            passed=False,
            threshold=0.70,
            details={"error": "No retrieval spans found in execution trace."},
        )

    retrieved_doc_ids: List[str] = []
    for span in retrieval_spans:
        payload = span.output_payload
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and "doc_id" in item:
                    retrieved_doc_ids.append(item["doc_id"])

    rank = None
    for idx, doc_id in enumerate(retrieved_doc_ids, start=1):
        if doc_id in expected:
            rank = idx
            break

    score = (1.0 / rank) if rank else 0.0
    passed = score >= 0.70

    return MetricResult(
        metric_name="mrr",
        score=round(score, 4),
        passed=passed,
        threshold=0.70,
        details={
            "first_relevant_rank": rank,
            "retrieved_count": len(retrieved_doc_ids),
            "expected_sources": list(expected),
        },
    )


def calculate_precision_at_k(
    trace: ExecutionTrace, test_case: TestCase, k: int = 3
) -> MetricResult:
    """Calculate Precision@K: proportion of top-K retrieved documents that are relevant."""
    expected = set(test_case.expected_sources)
    if not expected:
        return MetricResult(
            metric_name=f"precision_at_{k}",
            score=1.0,
            passed=True,
            threshold=0.60,
            details={"info": "No expected sources specified."},
        )

    retrieval_spans = [s for s in trace.spans if s.kind == SpanKind.RAG_RETRIEVAL]
    retrieved_doc_ids: List[str] = []
    for span in retrieval_spans:
        payload = span.output_payload
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and "doc_id" in item:
                    retrieved_doc_ids.append(item["doc_id"])

    top_k_docs = retrieved_doc_ids[:k]
    if not top_k_docs:
        return MetricResult(
            metric_name=f"precision_at_{k}",
            score=0.0,
            passed=False,
            threshold=0.60,
            details={"error": "Zero documents retrieved."},
        )

    relevant_in_top_k = sum(1 for doc in top_k_docs if doc in expected)
    score = relevant_in_top_k / len(top_k_docs)
    passed = score >= 0.60

    return MetricResult(
        metric_name=f"precision_at_{k}",
        score=round(score, 4),
        passed=passed,
        threshold=0.60,
        details={
            "k": k,
            "relevant_count": relevant_in_top_k,
            "evaluated_docs": top_k_docs,
        },
    )


def calculate_recall_at_k(trace: ExecutionTrace, test_case: TestCase, k: int = 3) -> MetricResult:
    """Calculate Recall@K: proportion of all expected documents retrieved in top-K."""
    expected = set(test_case.expected_sources)
    if not expected:
        return MetricResult(
            metric_name=f"recall_at_{k}",
            score=1.0,
            passed=True,
            threshold=0.60,
            details={"info": "No expected sources specified."},
        )

    retrieval_spans = [s for s in trace.spans if s.kind == SpanKind.RAG_RETRIEVAL]
    retrieved_doc_ids: List[str] = []
    for span in retrieval_spans:
        payload = span.output_payload
        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict) and "doc_id" in item:
                    retrieved_doc_ids.append(item["doc_id"])

    top_k_docs = set(retrieved_doc_ids[:k])
    found_relevant = len(expected.intersection(top_k_docs))
    score = found_relevant / len(expected)
    passed = score >= 0.60

    return MetricResult(
        metric_name=f"recall_at_{k}",
        score=round(score, 4),
        passed=passed,
        threshold=0.60,
        details={
            "k": k,
            "found_relevant": found_relevant,
            "total_expected": len(expected),
        },
    )


def check_step_limit_bounding(trace: ExecutionTrace, max_steps: int = 10) -> MetricResult:
    """Verify the agent trajectory did not exceed the maximum allowed step threshold."""
    step_count = len(trace.spans)
    passed = step_count <= max_steps
    return MetricResult(
        metric_name="step_limit_bound",
        score=float(step_count),
        passed=passed,
        threshold=float(max_steps),
        details={"total_spans": step_count, "max_allowed": max_steps},
    )
