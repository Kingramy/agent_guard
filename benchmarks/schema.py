"""AgentGuard Shared Data Contract (schema.py).

Agreed connection points between Evaluation (Person A - Ramy) and Platform/UI (Person B - Hamza).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TestCase(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    category: str = (
        "factual_qa"  # "factual_qa", "retrieval", "grounding", "tool_safety", "injection"
    )
    input_prompt: str
    expected_answer: Optional[str] = None
    expected_sources: List[str] = Field(default_factory=list)  # Target document IDs
    allowed_tools: List[str] = Field(default_factory=list)  # Permitted tool names
    synthetic_secret: Optional[str] = None  # Canary token to detect leaks
    max_allowed_latency_ms: float = 8000.0  # Production latency gate
    max_allowed_steps: int = 5  # Trajectory efficiency gate


class ToolCallRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[str] = None


class ExecutionTrace(BaseModel):
    model_config = ConfigDict(extra="ignore")

    test_case_id: str
    prompt: str
    final_answer: str
    retrieved_contexts: List[Dict[str, str]] = Field(
        default_factory=list
    )  # [{"doc_id": "...", "text": "..."}]
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    latency_ms: float = 0.0


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    test_case_id: str
    passed: bool
    retrieval_precision: float = 1.0
    retrieval_recall: float = 1.0
    retrieval_mrr: float = 1.0  # Mean Reciprocal Rank
    groundedness_score: float = 1.0  # 0.0 (total contradiction) to 1.0 (fully supported)
    latency_ms: float = 0.0
    findings: List[str] = Field(
        default_factory=list
    )  # ["CONTRADICTION", "UNAUTHORIZED_TOOL", etc.]
    details: Dict[str, Any] = Field(default_factory=dict)  # Diagnostic breakdown
