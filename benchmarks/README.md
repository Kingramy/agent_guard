# AgentGuard Evaluation & Benchmark Harness

This directory contains the standalone evaluation benchmark harness, metric computation rules, neural groundedness judges, and live agent security audit runners.

## Directory Structure

| File | Purpose |
| :--- | :--- |
| `run_eval.py` | Benchmark runner executing evaluation pipeline across test suites and execution traces. |
| `run_live_audit.py` | Live audit runner that queries a target agent against adversarial probes and evaluates output. |
| `main_evaluator.py` | Unified `AgentGuardEvaluator` engine orchestrating IR, behavior, security, and neural checks. |
| `eval_rules.py` | Rule-based evaluators: Precision@K, Recall@K, MRR, tool validation, and synthetic secret leak detection. |
| `eval_grounding.py` | `NeuralJudge` evaluating factual consistency and contradiction using DeBERTa cross-encoder NLI. |
| `report_generator.py` | Generates comprehensive markdown audit reports with severity ratings and developer remediations. |
| `target_app.py` | Sample reference target agent with ChromaDB vector search and simulated tool execution. |
| `schema.py` | Standalone Pydantic contracts for `TestCase`, `ExecutionTrace`, and `EvaluationResult`. |

## How to Run

### 1. Run the Evaluation Benchmark
Executes the evaluation pipeline over test cases (`data/datasets/test_suite.json`) and mock execution traces (`data/datasets/mock_traces.json`), outputting results to `reports/audit_report.md`:

```bash
uv run python benchmarks/run_eval.py
```

### 2. Run the Live Target Application Audit
Dispatches live queries to the local agent and audits the responses, outputting to `reports/live_audit_report.md`:

```bash
uv run python benchmarks/run_live_audit.py
```

Generated reports are saved in the top-level `reports/` directory.
