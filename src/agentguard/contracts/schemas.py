"""Core data contracts for AgentGuard.

Defines schemas shared between the evaluation layer (Ramy (AI Evaluation)) and the platform/storage layer (Hamza (Platform & Security)).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SecurityCategory(str, Enum):
    BENIGN = "benign"
    DIRECT_PROMPT_INJECTION = "direct_prompt_injection"
    INDIRECT_PROMPT_INJECTION = "indirect_prompt_injection"
    SENSITIVE_SECRET_LEAKAGE = "sensitive_secret_leakage"
    UNSAFE_TOOL_CALL = "unsafe_tool_call"
    EXCESSIVE_AUTONOMY = "excessive_autonomy"
    CONTRADICTION_HALLUCINATION = "contradiction_hallucination"
    UNGROUNDED_CLAIM = "ungrounded_claim"
    RETRIEVAL_FAILURE = "retrieval_failure"


class SpanKind(str, Enum):
    AGENT_RUN = "agent.run"
    RAG_RETRIEVAL = "rag.retrieval"
    TOOL_EXECUTION = "tool.execution"
    LLM_GENERATION = "llm.generation"
    SECURITY_GATE = "security.gate"


class SpanStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    BLOCKED = "blocked"


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class TestCase(BaseModel):
    """Evaluation probe definition containing prompt inputs, expected behavior, and references."""

    __test__ = False
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(default_factory=lambda: f"tc_{uuid.uuid4().hex[:8]}")
    input: str
    expected_behavior: str
    reference_answer: Optional[str] = None
    expected_sources: List[str] = Field(default_factory=list)
    security_category: SecurityCategory = SecurityCategory.BENIGN
    allowed_tools: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Dataset(BaseModel):
    """Versioned collection of test cases."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    test_cases: List[TestCase] = Field(default_factory=list)


class ExecutionSpan(BaseModel):
    """Single span representing an execution step in an agent run."""

    model_config = ConfigDict(extra="allow")

    span_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str
    kind: SpanKind
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: SpanStatus = SpanStatus.SUCCESS
    input_payload: Any = Field(default_factory=dict)
    output_payload: Any = Field(default_factory=dict)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None

    def close(self, status: SpanStatus = SpanStatus.SUCCESS, error: Optional[str] = None) -> None:
        self.end_time = datetime.now(timezone.utc)
        self.status = status
        self.error_message = error
        if self.start_time and self.end_time:
            self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000.0


class ExecutionTrace(BaseModel):
    """Root trace capturing the full agent execution tree for a single task."""

    model_config = ConfigDict(extra="allow")

    trace_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    test_case_id: Optional[str] = None
    project_id: str = "default"
    agent_version: str = "v1.0.0"
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[float] = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    status: SpanStatus = SpanStatus.SUCCESS
    final_output: Optional[str] = None
    spans: List[ExecutionSpan] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def calculate_aggregates(self) -> None:
        in_tok = 0
        out_tok = 0
        for s in self.spans:
            if isinstance(s.attributes, dict):
                in_tok += s.attributes.get("gen_ai.usage.input_tokens", 0)
                in_tok += s.attributes.get("input_tokens", 0)
                out_tok += s.attributes.get("gen_ai.usage.output_tokens", 0)
                out_tok += s.attributes.get("output_tokens", 0)
        self.total_input_tokens = in_tok
        self.total_output_tokens = out_tok
        if self.start_time and self.end_time:
            self.total_duration_ms = (self.end_time - self.start_time).total_seconds() * 1000.0


class MetricResult(BaseModel):
    """Quantitative metric score with threshold evaluation."""

    model_config = ConfigDict(extra="forbid")

    metric_name: str
    score: float
    passed: bool
    threshold: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class EvaluationFinding(BaseModel):
    """Diagnostic record for a behavioral, groundedness, or security defect."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(default_factory=lambda: f"fnd_{uuid.uuid4().hex[:8]}")
    test_case_id: str
    trace_id: str
    span_id: Optional[str] = None
    category: SecurityCategory
    severity: SeverityLevel
    title: str
    explanation: str
    suggested_remediation: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QualityGateThresholds(BaseModel):
    min_mrr: float = 0.70
    min_precision_at_k: float = 0.60
    min_groundedness_score: float = 0.85
    max_critical_findings: int = 0
    max_high_findings: int = 0
    max_p95_latency_ms: float = 5000.0


class EvaluationRunReport(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:8]}")
    project_id: str = "default"
    agent_version: str = "v1.0.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_test_cases: int = 0
    passed_test_cases: int = 0
    failed_test_cases: int = 0
    gate_passed: bool = False
    metrics_summary: Dict[str, float] = Field(default_factory=dict)
    findings: List[EvaluationFinding] = Field(default_factory=list)
    traces: List[ExecutionTrace] = Field(default_factory=list)
