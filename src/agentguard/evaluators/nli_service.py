"""Standalone high-performance FastAPI microservice for DeBERTa-v3 NLI evaluations."""

from typing import Any, Dict, List

import torch
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel, Field

from agentguard.evaluators.neural_nli import (
    NeuralNLIClassifier,
    NLIPrediction,
    extract_claims,
)

router = APIRouter(prefix="/api/v1/nli", tags=["Neural NLI"])


class BatchNLIRequest(BaseModel):
    pairs: List[Dict[str, str]] = Field(
        ...,
        description="List of {'premise': '...', 'hypothesis': '...'} dictionaries",
        json_schema_extra={
            "example": [
                {
                    "premise": "Full refunds are available within 30 days.",
                    "hypothesis": "Refunds are allowed after 60 days.",
                }
            ]
        },
    )


class GroundingCheckRequest(BaseModel):
    context: str = Field(..., description="Retrieved background context")
    generated_text: str = Field(..., description="Agent generated answer to verify")


@router.post("/evaluate", response_model=List[NLIPrediction])
async def evaluate_pairs(request: BatchNLIRequest) -> List[NLIPrediction]:
    classifier = NeuralNLIClassifier.get_instance()
    pair_tuples = [(p.get("premise", ""), p.get("hypothesis", "")) for p in request.pairs]
    return classifier.predict_batch(pair_tuples)


@router.post("/grounding")
async def verify_grounding(request: GroundingCheckRequest) -> Dict[str, Any]:
    classifier = NeuralNLIClassifier.get_instance()
    claims = extract_claims(request.generated_text)
    pairs = [(request.context, c) for c in claims]
    predictions = classifier.predict_batch(pairs)

    contradictions = [p for p in predictions if p.verdict == "CONTRADICTION"]
    entailments = [p for p in predictions if p.verdict == "ENTAILMENT"]

    score = round(len(entailments) / max(len(claims), 1), 4)
    has_contradiction = len(contradictions) > 0

    return {
        "claims_count": len(claims),
        "groundedness_score": score,
        "has_contradiction": has_contradiction,
        "verdict": "FAIL" if has_contradiction or score < 0.85 else "PASS",
        "claims_breakdown": [
            {
                "claim": p.hypothesis,
                "verdict": p.verdict,
                "contradiction_prob": p.contradiction_prob,
                "entailment_prob": p.entailment_prob,
                "neutral_prob": p.neutral_prob,
            }
            for p in predictions
        ],
    }


@router.get("/health")
async def nli_health() -> Dict[str, Any]:
    cuda_avail = torch.cuda.is_available()
    vram_alloc = round(torch.cuda.memory_allocated() / (1024**2), 2) if cuda_avail else 0.0
    device_name = torch.cuda.get_device_name(0) if cuda_avail else "CPU"
    return {
        "status": "healthy",
        "model": "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
        "cuda_available": cuda_avail,
        "device": device_name,
        "vram_allocated_mb": vram_alloc,
    }


# Standalone App entrypoint if run directly
nli_app = FastAPI(title="AgentGuard Neural NLI Microservice", version="0.1.0")
nli_app.include_router(router)
