---
name: agentguard-rag-eval-harness
description: Mathematical formulations and neural NLI procedures for evaluating retrieval accuracy, grounding, and factual contradictions in AgentGuard.
---

# AgentGuard RAG Evaluation Harness

Authoritative guide for Ramy ([@Kingramy](https://github.com/Kingramy)) and the evaluation engine to compute deterministic retrieval metrics and neural groundedness scores.

## 1. Deterministic Information Retrieval (IR) Math

### Mean Reciprocal Rank (MRR)
Measures how early in the ranked results the first relevant document appears:
$$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
- If the first relevant document is at rank 1: score = 1.0.
- If at rank 2: score = 0.5.
- If no relevant document is retrieved: score = 0.0.
- Threshold: Passing score requires $\text{MRR} \ge 0.70$.

### Precision@K
Measures the proportion of the top-$K$ retrieved documents that are relevant:
$$\text{Precision@K} = \frac{|\text{Relevant Docs} \cap \text{Top-K Retrieved}|}{K}$$
- Threshold: Passing score requires $\text{Precision@K} \ge 0.60$.

### Recall@K
Measures what proportion of all expected relevant documents were captured in the top-$K$:
$$\text{Recall@K} = \frac{|\text{Relevant Docs} \cap \text{Top-K Retrieved}|}{|\text{Total Relevant Docs}|}$$

## 2. Neural Grounding (NLI Cross-Encoder)

Use `cross-encoder/nli-deberta-v3-small` to classify claim support against retrieved documents:
1. Extract atomic factual claims from the agent's generated output.
2. For each claim, construct premise-hypothesis pairs:
   - Premise: Concatenated text of retrieved chunks (`doc["content"]`).
   - Hypothesis: The generated claim.
3. Model outputs 3-class logits: `[Contradiction, Neutral, Entailment]`.
4. Apply softmax to get normalized probabilities.
5. Verdict Logic:
   - If $P(\text{Contradiction}) > 0.50$ -> Flag as `CONTRADICTION_HALLUCINATION` (`SeverityLevel.CRITICAL`).
   - If $P(\text{Entailment}) < 0.30$ and $P(\text{Neutral}) > 0.60$ -> Flag as `UNGROUNDED_CLAIM` (`SeverityLevel.MEDIUM`).
   - If $P(\text{Entailment}) \ge 0.70$ -> Pass (`Grounded`).

## 3. Emitting Standard Contracts

Evaluators must return strict `MetricResult` and `EvaluationFinding` objects defined in `agentguard.contracts.schemas`:

```python
from agentguard.contracts.schemas import MetricResult, EvaluationFinding, SecurityCategory, SeverityLevel

# Quantitative metric
metric = MetricResult(
    metric_name="mrr",
    score=1.0,
    passed=True,
    threshold=0.70,
    details={"rank": 1}
)

# Qualitative diagnostic
finding = EvaluationFinding(
    test_case_id="tc_001",
    trace_id="tr_abc123",
    span_id="sp_xyz789",
    category=SecurityCategory.CONTRADICTION_HALLUCINATION,
    severity=SeverityLevel.CRITICAL,
    title="Leave policy contradiction",
    explanation="Agent stated 30 days leave, while official policy document mandates 25 days.",
    suggested_remediation="Update agent prompt to emphasize strict adherence to retrieved leave numbers."
)
```
