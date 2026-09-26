"""Unit and integration tests for Neural NLI cross-encoder evaluator and microservice."""

import pytest
from httpx import ASGITransport, AsyncClient

from agentguard.api.app import app
from agentguard.contracts.schemas import (
    ExecutionSpan,
    ExecutionTrace,
    SecurityCategory,
    SeverityLevel,
    SpanKind,
    SpanStatus,
)
from agentguard.evaluators.neural_nli import (
    NeuralNLIClassifier,
    evaluate_grounding,
    extract_claims,
)


@pytest.fixture(scope="session")
def nli_classifier():
    return NeuralNLIClassifier.get_instance()


def test_nli_contradiction_detection(nli_classifier):
    """Verify DeBERTa NLI cross-encoder flags factual contradiction with >60% probability."""
    pairs = [
        (
            "Enterprise customers can request full refunds strictly within 30 days of purchase.",
            "Enterprise refunds are available at any time even after 90 days.",
        )
    ]
    preds = nli_classifier.predict_batch(pairs)
    assert len(preds) == 1
    assert preds[0].verdict == "CONTRADICTION"
    assert preds[0].contradiction_prob > 0.60


def test_nli_entailment_detection(nli_classifier):
    """Verify DeBERTa NLI recognizes logically entailed statements."""
    pairs = [
        (
            "Full-time engineers receive 25 standard paid vacation days per calendar year.",
            "Employees are granted 25 days of paid vacation annually.",
        )
    ]
    preds = nli_classifier.predict_batch(pairs)
    assert len(preds) == 1
    assert preds[0].verdict == "ENTAILMENT"
    assert preds[0].entailment_prob > 0.60


def test_extract_claims():
    """Verify text is split into distinct propositional claims."""
    text = "Refunds are processed within 30 days. Employees get 25 days off. Support is 24/7."
    claims = extract_claims(text)
    assert len(claims) == 3
    assert "Refunds are processed within 30 days." in claims


def test_evaluate_grounding_contradiction_finding(nli_classifier):
    """Verify trace with hallucinated output triggers CRITICAL finding and failed metric."""
    rag_span = ExecutionSpan(
        span_id="rag_span_01",
        trace_id="trace_nli_01",
        name="rag.kb_search",
        kind=SpanKind.RAG_RETRIEVAL,
        output_payload=[
            {
                "doc_id": "refund_policy.pdf",
                "content": "Enterprise customers can request refunds strictly within 30 days.",
            }
        ],
    )
    trace = ExecutionTrace(
        trace_id="trace_nli_01",
        test_case_id="tc_refund_check",
        status=SpanStatus.SUCCESS,
        final_output="Customers can request full refunds after 60 days without issue.",
        spans=[rag_span],
    )

    preds, findings, metric = evaluate_grounding(trace, classifier=nli_classifier)
    assert len(preds) >= 1
    assert len(findings) >= 1
    assert findings[0].severity == SeverityLevel.CRITICAL
    assert findings[0].category == SecurityCategory.CONTRADICTION_HALLUCINATION
    assert metric.passed is False


@pytest.mark.asyncio
async def test_nli_microservice_api():
    """Verify FastAPI NLI endpoints return correct JSON contracts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test health
        health_res = await client.get("/api/v1/nli/health")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["status"] == "healthy"
        assert "DeBERTa" in health_data["model"]

        # Test batch evaluate
        eval_payload = {
            "pairs": [
                {
                    "premise": "Full refunds are available within 30 days.",
                    "hypothesis": "Refunds are allowed after 60 days.",
                }
            ]
        }
        eval_res = await client.post("/api/v1/nli/evaluate", json=eval_payload)
        assert eval_res.status_code == 200
        preds = eval_res.json()
        assert len(preds) == 1
        assert preds[0]["verdict"] == "CONTRADICTION"

        # Test grounding check
        ground_payload = {
            "context": "Employees receive 25 paid leave days per year.",
            "generated_text": "Employees receive 25 paid leave days per year.",
        }
        ground_res = await client.post("/api/v1/nli/grounding", json=ground_payload)
        assert ground_res.status_code == 200
        ground_data = ground_res.json()
        assert ground_data["verdict"] == "PASS"
        assert ground_data["has_contradiction"] is False
