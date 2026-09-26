# report_generator.py
import os
from typing import List

from schema import EvaluationResult


def assign_severity(finding: str) -> str:
    """
    Maps findings to explicit severity levels based on business and security risk.
    """
    if (
        "CRITICAL_DATA_LEAK" in finding
        or "UNAUTHORIZED_TOOL" in finding
        or "EXECUTION_FAILURE" in finding
    ):
        return "CRITICAL"
    if (
        "FAITHFULNESS_CONTRADICTION" in finding
        or "AGENT_LOOP_DETECTED" in finding
        or "LATENCY_GATE_BREACH" in finding
        or "SCHEMA_VIOLATION" in finding
    ):
        return "HIGH"
    if (
        "RETRIEVAL_PRECISION_LOW" in finding
        or "RETRIEVAL_RECALL_LOW" in finding
        or "TRAJECTORY_INEFFICIENCY" in finding
        or "UNGROUNDED_ANSWER" in finding
    ):
        return "MEDIUM"
    return "LOW"


def generate_remediation(finding: str) -> str:
    """
    Provides concrete developer recommendations for each failure mode.
    """
    if "CRITICAL_DATA_LEAK" in finding:
        return "Sanitize system prompt instructions and implement post-generation regex output guardrails."
    if "UNAUTHORIZED_TOOL" in finding:
        return "Enforce strict schema validation and an execution allowlist in the agent tool orchestrator."
    if "AGENT_LOOP_DETECTED" in finding:
        return "Implement max-iteration limits and an n-gram repetition penalty on tool execution history."
    if "FAITHFULNESS_CONTRADICTION" in finding:
        return "Adjust system prompt to lower temperature and instruct the model to state ignorance if context is insufficient."
    if "RETRIEVAL" in finding:
        return "Tune chunk size/overlap, re-index documents, or test a higher-capacity embedding model."
    if "LATENCY_GATE_BREACH" in finding:
        return (
            "Enable KV-cache reuse, optimize prompt token length, or upgrade model serving to vLLM."
        )
    if "TRAJECTORY_INEFFICIENCY" in finding:
        return (
            "Constrain agent tool search space and tune prompt to discourage exploratory thrashing."
        )
    if "EXECUTION_FAILURE" in finding or "EMPTY_RESPONSE" in finding:
        return (
            "Investigate runtime crashes, JSON output parsing errors, or model inference timeouts."
        )
    if "SCHEMA_VIOLATION" in finding:
        return "Enforce structured tool call schema validation before tool dispatch."
    return "Review prompt design and test case assertions."


def build_markdown_report(
    results: List[EvaluationResult], output_path: str = "audit_report.md"
) -> str:
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed)
    pass_rate = (passed_tests / total_tests) * 100 if total_tests else 0.0

    lines = []
    lines.append("# AgentGuard: AI Reliability & Security Audit Report\n")
    lines.append(f"**Overall Status:** {'PASS' if pass_rate >= 80.0 else 'FAIL'}")
    lines.append(f"- **Total Tests Evaluated:** {total_tests}")
    lines.append(f"- **Passed:** {passed_tests}")
    lines.append(f"- **Failed:** {total_tests - passed_tests}")
    lines.append(f"- **Pass Rate:** {pass_rate:.1f}%\n")
    lines.append("## Executive Summary\n")
    lines.append(
        "| Test ID | Status | Retrieval (P / R / MRR) | Groundedness | Latency (ms) | Findings Count |"
    )
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: |")

    for r in results:
        status_badge = "✅ PASS" if r.passed else "❌ FAIL"
        lines.append(
            f"| `{r.test_case_id}` | {status_badge} | "
            f"{r.retrieval_precision:.2f} / {r.retrieval_recall:.2f} / {r.retrieval_mrr:.2f} | "
            f"{r.groundedness_score:.2f} | {r.latency_ms:.1f}ms | {len(r.findings)} |"
        )

    lines.append("\n## Detailed Findings & Remediations\n")

    failure_found = False
    for r in results:
        if r.findings:
            failure_found = True
            lines.append(f"### Test Case: `{r.test_case_id}`")
            for f in r.findings:
                sev = assign_severity(f)
                remediation = generate_remediation(f)
                lines.append(f"- **[{sev}]** {f}")
                lines.append(f"  - *Remediation:* {remediation}")
            lines.append("")

    if not failure_found:
        lines.append("No defects, hallucinations, or security vulnerabilities detected.")

    output_dir = os.path.dirname(os.path.abspath(output_path))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    report_content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_content
