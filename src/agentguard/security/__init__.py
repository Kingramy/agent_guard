"""Security and adversarial red-teaming modules for AgentGuard."""

from agentguard.security.entropy import calculate_shannon_entropy, scan_high_entropy_secrets
from agentguard.security.fuzzer import AdversarialProbe, AdversarialPromptFuzzer, OWASPCategory
from agentguard.security.guardrail import (
    CircuitBreakerDecision,
    MarkovCircuitBreaker,
    RuntimeGuardrailInterceptor,
    evaluate_runtime_guardrails,
)
from agentguard.security.scanner import (
    detect_agent_loop_thrashing,
    scan_synthetic_secret_leakage,
    verify_tool_authorization,
)
from agentguard.security.xpia import (
    detect_markdown_exfiltration,
    detect_zero_width_smuggling,
    generate_poisoned_retrieval_chunk,
    scan_xpia_vulnerabilities,
)

__all__ = [
    "calculate_shannon_entropy",
    "scan_high_entropy_secrets",
    "AdversarialProbe",
    "AdversarialPromptFuzzer",
    "OWASPCategory",
    "CircuitBreakerDecision",
    "MarkovCircuitBreaker",
    "RuntimeGuardrailInterceptor",
    "evaluate_runtime_guardrails",
    "detect_agent_loop_thrashing",
    "scan_synthetic_secret_leakage",
    "verify_tool_authorization",
    "detect_markdown_exfiltration",
    "detect_zero_width_smuggling",
    "generate_poisoned_retrieval_chunk",
    "scan_xpia_vulnerabilities",
]
