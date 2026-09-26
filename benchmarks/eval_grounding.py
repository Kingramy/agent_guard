# eval_grounding.py
import re
from typing import Dict, List, Optional, Tuple

from sentence_transformers import CrossEncoder


class NeuralJudge:
    def __init__(self, model_name: str = "cross-encoder/nli-deberta-v3-small"):
        self.model = CrossEncoder(model_name)
        hf_model = self.model.model
        if hf_model is not None and hasattr(hf_model, "config") and getattr(hf_model.config, "id2label", None):
            self.id2label = {int(k): str(v).lower() for k, v in hf_model.config.id2label.items()}
        else:
            self.id2label = {0: "contradiction", 1: "entailment", 2: "neutral"}

    def clean_claim_text(self, sentence: str) -> str:
        """
        Strips conversational attribution prefixes that dilute NLI entailment scores.
        """
        patterns = [
            r"^according to [^,]+,\s*",
            r"^based on [^,]+,\s*",
            r"^the document states that\s*",
            r"^as mentioned (in|by) [^,]+,\s*",
        ]
        cleaned = sentence.strip()
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip()

    def split_into_sentences(self, text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        refusal_phrases = [
            "i do not have enough information",
            "i cannot answer",
            "i don't know",
            "i cannot clear",
            "i cannot reveal",
            "i am unable to",
            "i can't",
        ]

        clean_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 5 and not any(
                phrase in s_clean.lower() for phrase in refusal_phrases
            ):
                clean_sentences.append(s_clean)
        return clean_sentences

    def evaluate_groundedness(
        self,
        retrieved_contexts: List[Dict[str, str]],
        final_answer: str,
        contradiction_threshold: float = 0.40,
    ) -> Tuple[float, List[str], List[Dict[str, str]]]:
        findings = []
        diagnostics = []

        raw_claims = self.split_into_sentences(final_answer)

        # If there are no factual claims (e.g. pure refusal or empty), it is safe
        if not raw_claims:
            return 1.0, [], []

        # If claims exist but NO context was retrieved, the answer is completely ungrounded
        if not retrieved_contexts:
            return (
                0.0,
                ["UNGROUNDED_ANSWER: Model made factual claims without retrieved context."],
                [],
            )

        full_premise = " ".join(
            [doc.get("text", "") for doc in retrieved_contexts if isinstance(doc, dict)]
        )
        cleaned_claims = [self.clean_claim_text(c) for c in raw_claims]
        pairs = [(full_premise, claim) for claim in cleaned_claims]

        probabilities = self.model.predict(pairs, apply_softmax=True)
        if len(cleaned_claims) == 1 and probabilities.ndim == 1:
            probabilities = [probabilities]

        supported_count = 0
        contradiction_found = False

        for raw_claim, cleaned_claim, probs in zip(
            raw_claims, cleaned_claims, probabilities, strict=False
        ):
            prob_dict = {self.id2label[i]: float(probs[i]) for i in range(len(probs))}

            p_contra = prob_dict.get("contradiction", 0.0)
            p_entail = prob_dict.get("entailment", 0.0)
            p_neutral = prob_dict.get("neutral", 0.0)

            diagnostics.append(
                {
                    "claim": raw_claim,
                    "cleaned": cleaned_claim,
                    "p_entailment": f"{p_entail:.3f}",
                    "p_neutral": f"{p_neutral:.3f}",
                    "p_contradiction": f"{p_contra:.3f}",
                }
            )

            if p_contra >= contradiction_threshold:
                contradiction_found = True
                findings.append(
                    f"FAITHFULNESS_CONTRADICTION: Claim '{raw_claim}' contradicts context (P={p_contra:.2f})."
                )
            elif p_entail > 0.40 or (p_entail > p_contra and p_neutral < 0.60):
                supported_count += 1
            else:
                findings.append(
                    f"UNSUPPORTED_CLAIM: Claim '{raw_claim}' is not grounded in context."
                )

        groundedness_score = 0.0 if contradiction_found else (supported_count / len(raw_claims))
        return groundedness_score, findings, diagnostics


# Singleton instance for high performance and backward compatibility
_default_judge: Optional[NeuralJudge] = None


def get_default_judge() -> NeuralJudge:
    global _default_judge
    if _default_judge is None:
        _default_judge = NeuralJudge()
    return _default_judge


def evaluate_groundedness(
    retrieved_contexts: List[Dict[str, str]],
    final_answer: str,
    contradiction_threshold: float = 0.40,
) -> Tuple[float, List[str], List[Dict[str, str]]]:
    judge = get_default_judge()
    return judge.evaluate_groundedness(retrieved_contexts, final_answer, contradiction_threshold)
