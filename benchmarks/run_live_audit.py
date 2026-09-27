# run_live_audit.py
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

from report_generator import build_markdown_report  # noqa: E402
from run_eval import run_evaluation_pipeline  # noqa: E402

try:
    from benchmarks.schema import TestCase  # noqa: E402
except ImportError:
    from schema import TestCase  # noqa: E402
from target_app import query_target_agent  # noqa: E402

if __name__ == "__main__":
    suite_path = DATASETS_DIR / "test_suite.json"
    report_path = REPORTS_DIR / "live_audit_report.md"

    if not suite_path.exists():
        suite_path = Path("test_suite.json")

    with open(suite_path, "r", encoding="utf-8") as f:
        cases = [TestCase(**c) for c in json.load(f)]

    print("\n" + "=" * 50)
    print("      AGENTGUARD LIVE TARGET APPLICATION AUDIT")
    print("=" * 50 + "\n")

    live_results = []

    for case in cases:
        print(f"[*] Dispatching prompt to Live Agent: '{case.input_prompt}'")

        # 1. Run the target application live
        live_trace = query_target_agent(case.input_prompt, case.id)
        print(f"    -> Agent Latency: {live_trace.latency_ms:.1f}ms")
        print(f"    -> Tools Invoked: {[t.tool_name for t in live_trace.tool_calls]}")
        print(f"    -> Answer: {live_trace.final_answer[:70]}...")

        # 2. Evaluate the live trace with AgentGuard
        result = run_evaluation_pipeline(case, live_trace)
        live_results.append(result)

        status = "PASSED" if result.passed else "FAILED"
        print(f"    -> Status: [{status}] (Groundedness: {result.groundedness_score:.2f})")
        if result.findings:
            for f in result.findings:
                print(f"       * {f}")
        print("-" * 50)

    # 3. Export the live report
    build_markdown_report(live_results, output_path=str(report_path))
    print(f"\n[Audit complete! Generated live report -> {report_path}]")
