"""AgentGuard Pre-Deployment Gate CLI.

Provides command-line interfaces for CI/CD gates, pre-commit hooks,
and automated evaluation of agent execution traces.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def get_default_paths() -> tuple[Path, Path, Path]:
    root = Path(__file__).resolve().parent.parent.parent.parent
    suite_path = root / "data" / "datasets" / "test_suite.json"
    traces_path = root / "data" / "datasets" / "mock_traces.json"
    report_path = root / "reports" / "ci_gate_report.md"
    return suite_path, traces_path, report_path


def run_gate(
    suite_file: Path,
    traces_file: Path,
    report_file: Optional[Path] = None,
    min_pass_rate: float = 80.0,
    fail_on_critical: bool = True,
) -> int:
    """Executes the pre-deployment quality gate against trace benchmarks."""
    console.print(
        Panel.fit(
            "[bold cyan]AgentGuard CI/CD Quality Gate[/bold cyan]\n"
            "[dim]Evaluating agent traces against IR precision, neural groundedness & security constraints[/dim]",
            border_style="cyan",
        )
    )

    if not suite_file.exists():
        console.print(f"[bold red]Error:[/bold red] Test suite file not found at: {suite_file}")
        return 1

    if not traces_file.exists():
        console.print(f"[bold red]Error:[/bold red] Traces file not found at: {traces_file}")
        return 1

    try:
        from benchmarks.main_evaluator import AgentGuardEvaluator
        from benchmarks.report_generator import build_markdown_report
        from benchmarks.schema import ExecutionTrace, TestCase
    except ImportError:
        import sys
        root = Path(__file__).resolve().parent.parent.parent.parent
        benchmarks_dir = root / "benchmarks"
        if str(benchmarks_dir) not in sys.path:
            sys.path.insert(0, str(benchmarks_dir))
        from main_evaluator import AgentGuardEvaluator
        from report_generator import build_markdown_report
        from schema import ExecutionTrace, TestCase

    with open(suite_file, "r", encoding="utf-8") as f:
        suite_cases = {c["id"]: TestCase(**c) for c in json.load(f)}

    with open(traces_file, "r", encoding="utf-8") as f:
        traces = [ExecutionTrace(**t) for t in json.load(f)]

    evaluator = AgentGuardEvaluator()
    results = []

    table = Table(title="AgentGuard Gate Results", show_header=True, header_style="bold magenta")
    table.add_column("Test ID", style="dim", width=26)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Precision@K", justify="right", width=12)
    table.add_column("Recall@K", justify="right", width=10)
    table.add_column("Groundedness", justify="right", width=14)
    table.add_column("Latency", justify="right", width=10)
    table.add_column("Findings", justify="left")

    has_critical_failure = False

    for trace in traces:
        case = suite_cases.get(trace.test_case_id)
        if not case:
            console.print(f"[yellow]Warning: No test case definition for ID: {trace.test_case_id}[/yellow]")
            continue

        res = evaluator.evaluate(case, trace)
        results.append(res)

        status_str = "[bold green]PASS[/bold green]" if res.passed else "[bold red]FAIL[/bold red]"
        findings_summary = ", ".join(res.findings[:2]) if res.findings else "[dim]None[/dim]"
        if len(res.findings) > 2:
            findings_summary += f" (+{len(res.findings) - 2} more)"

        if any("CRITICAL" in f or "LEAK" in f or "UNAUTHORIZED" in f for f in res.findings):
            has_critical_failure = True

        table.add_row(
            res.test_case_id,
            status_str,
            f"{res.retrieval_precision:.2f}",
            f"{res.retrieval_recall:.2f}",
            f"{res.groundedness_score:.2f}",
            f"{res.latency_ms:.1f}ms",
            findings_summary,
        )

    console.print(table)

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    pass_rate = (passed / total * 100) if total else 0.0

    if report_file:
        build_markdown_report(results, output_path=str(report_file))
        console.print(f"[dim]Audit report written to: {report_file}[/dim]")

    console.print(f"\n[bold]Summary:[/bold] {passed}/{total} tests passed ([bold]{pass_rate:.1f}%[/bold])")

    if fail_on_critical and has_critical_failure:
        console.print("[bold red]❌ CI Gate Rejected: Critical security or safety vulnerability detected![/bold red]")
        return 1

    if pass_rate < min_pass_rate:
        console.print(f"[bold red]❌ CI Gate Rejected: Pass rate {pass_rate:.1f}% is below required {min_pass_rate:.1f}%[/bold red]")
        return 1

    console.print("[bold green]✅ CI Gate Approved: All agent reliability and security gates passed![/bold green]")
    return 0


def cli_main() -> None:
    parser = argparse.ArgumentParser(
        prog="agentguard",
        description="AgentGuard Enterprise AI Reliability & Security Platform CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Command: agentguard test
    test_parser = subparsers.add_parser("test", help="Run pre-deployment quality and security gate")
    test_parser.add_argument(
        "--suite",
        type=Path,
        default=None,
        help="Path to test_suite.json",
    )
    test_parser.add_argument(
        "--traces",
        type=Path,
        default=None,
        help="Path to mock_traces.json or live traces",
    )
    test_parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Path to save markdown report",
    )
    test_parser.add_argument(
        "--min-pass-rate",
        type=float,
        default=80.0,
        help="Minimum required pass rate percentage (default: 80.0)",
    )
    test_parser.add_argument(
        "--fail-on-critical",
        action="store_true",
        default=True,
        help="Immediately fail if critical security findings exist (default: True)",
    )

    # Command: agentguard version
    subparsers.add_parser("version", help="Show AgentGuard version")

    args = parser.parse_args()

    if args.subcommand == "version":
        console.print("[bold cyan]AgentGuard[/bold cyan] version [bold green]1.0.0[/bold green]")
        sys.exit(0)

    elif args.subcommand == "test" or args.subcommand is None:
        def_suite, def_traces, def_report = get_default_paths()
        suite_path = args.suite or def_suite
        traces_path = args.traces or def_traces
        report_path = args.report or def_report

        exit_code = run_gate(
            suite_file=suite_path,
            traces_file=traces_path,
            report_file=report_path,
            min_pass_rate=getattr(args, "min_pass_rate", 80.0),
            fail_on_critical=getattr(args, "fail_on_critical", True),
        )
        sys.exit(exit_code)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
