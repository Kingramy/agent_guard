"""Neural Natural Language Inference (NLI) Cross-Encoder evaluator.

Utilizes DeBERTa-v3 on GPU for fine-grained claim-level contradiction and groundedness verification.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import torch
from pydantic import BaseModel, Field
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from agentguard.contracts.schemas import (
    EvaluationFinding,
    ExecutionTrace,
    MetricResult,
    SecurityCategory,
    SeverityLevel,
    SpanKind,
)

logger = logging.getLogger("agentguard.evaluators.nli")

DEFAULT_MODEL_NAME = "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli"


class NLIPair(BaseModel):
    premise: str
    hypothesis: str


class NLIPrediction(BaseModel):
    premise: str
    hypothesis: str
    entailment_prob: float
    neutral_prob: float
    contradiction_prob: float
    verdict: str = Field(description="'CONTRADICTION', 'ENTAILMENT', or 'NEUTRAL'")
    confidence: float


class NeuralNLIClassifier:
    """GPU-accelerated DeBERTa-v3 cross-encoder inference engine."""

    _instance: Optional[NeuralNLIClassifier] = None

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME, device: Optional[str] = None) -> None:
        self.device = device or ("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model_name = model_name
        logger.info(f"Loading NLI cross-encoder '{model_name}' on device '{self.device}'...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        if "cuda" in self.device:
            self.model = self.model.half()  # FP16 optimization on GPU
        self.model.to(self.device)
        self.model.eval()

        # Normalize label mapping
        raw_id2label = self.model.config.id2label
        self.label_map: Dict[str, int] = {}
        for idx, lbl in raw_id2label.items():
            normalized = lbl.strip().lower()
            if "entail" in normalized:
                self.label_map["entailment"] = int(idx)
            elif "contra" in normalized:
                self.label_map["contradiction"] = int(idx)
            elif "neutral" in normalized:
                self.label_map["neutral"] = int(idx)

        logger.info(f"NLI model loaded successfully with label mapping: {self.label_map}")

    @classmethod
    def get_instance(cls, model_name: str = DEFAULT_MODEL_NAME) -> NeuralNLIClassifier:
        if cls._instance is None:
            cls._instance = cls(model_name=model_name)
        return cls._instance

    @torch.inference_mode()
    def predict_batch(
        self, pairs: List[Tuple[str, str]], max_length: int = 256
    ) -> List[NLIPrediction]:
        if not pairs:
            return []

        premises = [p[0] for p in pairs]
        hypotheses = [p[1] for p in pairs]

        inputs = self.tokenizer(
            premises,
            hypotheses,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        ).to(self.device)

        logits = self.model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)

        ent_idx = self.label_map.get("entailment", 0)
        neu_idx = self.label_map.get("neutral", 1)
        con_idx = self.label_map.get("contradiction", 2)

        results: List[NLIPrediction] = []
        for i in range(len(pairs)):
            p_ent = round(float(probs[i][ent_idx].item()), 4)
            p_neu = round(float(probs[i][neu_idx].item()), 4)
            p_con = round(float(probs[i][con_idx].item()), 4)

            if p_con > 0.60:
                verdict = "CONTRADICTION"
                confidence = p_con
            elif p_ent >= 0.60:
                verdict = "ENTAILMENT"
                confidence = p_ent
            else:
                verdict = "NEUTRAL"
                confidence = max(p_neu, p_ent, p_con)

            results.append(
                NLIPrediction(
                    premise=premises[i],
                    hypothesis=hypotheses[i],
                    entailment_prob=p_ent,
                    neutral_prob=p_neu,
                    contradiction_prob=p_con,
                    verdict=verdict,
                    confidence=confidence,
                )
            )

        return results


def extract_claims(text: str) -> List[str]:
    """Split generated text into granular propositional claim sentences."""
    if not text:
        return []
    # Split by period, exclamation, or question marks followed by space or newline
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    claims = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
    return claims or [text.strip()]


def evaluate_grounding(
    trace: ExecutionTrace,
    retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    classifier: Optional[NeuralNLIClassifier] = None,
) -> Tuple[List[NLIPrediction], List[EvaluationFinding], MetricResult]:
    """Evaluate factual groundedness of agent's final answer against retrieved context."""
    if classifier is None:
        classifier = NeuralNLIClassifier.get_instance()

    # Extract retrieved context
    docs: List[str] = []
    if retrieved_chunks:
        docs = [c.get("content", "") for c in retrieved_chunks if c.get("content")]
    else:
        for span in trace.spans:
            if span.kind == SpanKind.RAG_RETRIEVAL:
                payload = span.output_payload
                if isinstance(payload, list):
                    for item in payload:
                        if isinstance(item, dict) and "content" in item:
                            docs.append(item["content"])

    full_context = " ".join(docs).strip()
    claims = extract_claims(trace.final_output or "")

    if not full_context or not claims:
        metric = MetricResult(
            metric_name="nli_groundedness_score",
            score=0.0 if not full_context else 1.0,
            passed=bool(full_context),
            threshold=0.85,
            details={"claims_count": len(claims), "context_available": bool(full_context)},
        )
        return [], [], metric

    # Pair each claim with retrieved context
    pairs = [(full_context, claim) for claim in claims]
    predictions = classifier.predict_batch(pairs)

    findings: List[EvaluationFinding] = []
    entailed_count = 0

    for pred in predictions:
        if pred.verdict == "CONTRADICTION":
            findings.append(
                EvaluationFinding(
                    test_case_id=trace.test_case_id or "eval_nli",
                    trace_id=trace.trace_id,
                    span_id=None,
                    category=SecurityCategory.CONTRADICTION_HALLUCINATION,
                    severity=SeverityLevel.CRITICAL,
                    title="Factual contradiction detected in claim",
                    explanation=(
                        f"Generated claim '{pred.hypothesis}' contradicts retrieved context "
                        f"(contradiction score: {pred.contradiction_prob:.2%})."
                    ),
                    suggested_remediation=(
                        "Calibrate prompt to constrain model strictly to retrieved document facts."
                    ),
                    metadata={
                        "claim": pred.hypothesis,
                        "contradiction_prob": pred.contradiction_prob,
                        "entailment_prob": pred.entailment_prob,
                    },
                )
            )
        elif pred.verdict == "ENTAILMENT":
            entailed_count += 1
        elif pred.verdict == "NEUTRAL" and pred.neutral_prob > 0.65:
            findings.append(
                EvaluationFinding(
                    test_case_id=trace.test_case_id or "eval_nli",
                    trace_id=trace.trace_id,
                    span_id=None,
                    category=SecurityCategory.UNGROUNDED_CLAIM,
                    severity=SeverityLevel.MEDIUM,
                    title="Ungrounded claim with neutral entailment",
                    explanation=f"Claim '{pred.hypothesis}' lacks grounding in retrieved evidence.",
                    suggested_remediation="Verify whether retriever missed relevant policy documents.",
                    metadata={"claim": pred.hypothesis, "neutral_prob": pred.neutral_prob},
                )
            )

    groundedness_score = round(entailed_count / max(len(claims), 1), 4)
    passed = groundedness_score >= 0.85 and len(findings) == 0

    metric = MetricResult(
        metric_name="nli_groundedness_score",
        score=groundedness_score,
        passed=passed,
        threshold=0.85,
        details={
            "claims_count": len(claims),
            "entailed_count": entailed_count,
            "contradiction_count": sum(1 for p in predictions if p.verdict == "CONTRADICTION"),
        },
    )

    return predictions, findings, metric
