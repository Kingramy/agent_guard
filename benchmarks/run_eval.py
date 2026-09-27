# run_eval.py
import json
import sys
from pathlib import Path

# Ensure benchmarks directory and project root are in sys.path
BENCHMARKS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BENCHMARKS_DIR.parent
DATASETS_DIR = PROJECT_ROOT / "data" / "datasets"
REPORTS_DIR = PROJECT_ROOT / "reports"

if str(BENCHMARKS_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARKS_DIR))

from main_evaluator import AgentGuardEvaluator  # noqa: E402
from report_generator import build_markdown_report  # noqa: E402

try:
    from benchmarks.schema import EvaluationResult, ExecutionTrace, TestCase  # noqa: E402
except ImportError:
    from schema import EvaluationResult, ExecutionTrace, TestCase  # noqa: E402

evaluator_instance = AgentGuardEvaluator()


def run_evaluation_pipeline(test_case: TestCase, trace: ExecutionTrace) -> EvaluationResult:
    return evaluator_instance.evaluate(test_case, trace)


if __name__ == "__main__":
    suite_path = DATASETS_DIR / "test_suite.json"
    traces_path = DATASETS_DIR / "mock_traces.json"
    report_path = REPORTS_DIR / "audit_report.md"

    if not suite_path.exists():
        suite_path = Path("test_suite.json")
    if not traces_path.exists():
        traces_path = Path("mock_traces.json")

    with open(suite_path, "r", encoding="utf-8") as f:
        cases = {c["id"]: TestCase(**c) for c in json.load(f)}

    with open(traces_path, "r", encoding="utf-8") as f:
        traces = [ExecutionTrace(**t) for t in json.load(f)]

    print("\n" + "=" * 55)
    print("      AGENTGUARD COMPREHENSIVE EVALUATION BENCHMARK")
    print("=" * 55 + "\n")

    collected_results = []

    for trace in traces:
        case = cases[trace.test_case_id]
        result = run_evaluation_pipeline(case, trace)
        collected_results.append(result)

        status = "PASSED" if result.passed else "FAILED"
        print(f"[{status}] Test: {result.test_case_id}")
        print(
            f"  Retrieval: P={result.retrieval_precision:.2f} | R={result.retrieval_recall:.2f} | MRR={result.retrieval_mrr:.2f}"
        )
        print(
            f"  Groundedness: {result.groundedness_score:.2f} | Latency: {result.latency_ms:.1f}ms"
        )

        if result.details.get("claims_analysis"):
            print("  NLI Analysis:")
            for diag in result.details["claims_analysis"]:
                print(f'    * Text: "{diag["cleaned"]}"')
                print(
                    f"      Entail: {diag['p_entailment']} | Neutral: {diag['p_neutral']} | Contra: {diag['p_contradiction']}"
                )

        if result.findings:
            print("  Findings:")
            for f in result.findings:
                print(f"   * {f}")
        print("-" * 55)

    # Generate the unified markdown report
    build_markdown_report(collected_results, output_path=str(report_path))
    print(f"\n[Audit Report generated successfully -> {report_path}]")
