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

## Metrics & Evaluation Gates

1. **Deterministic IR Metrics**:
   - **Precision@K**: Fraction of top-$K$ retrieved documents that match expected ground truth sources.
   - **Recall@K**: Fraction of ground truth sources successfully retrieved in the top-$K$ contexts.
   - **Mean Reciprocal Rank (MRR)**: Reciprocal rank ($\frac{1}{\text{rank}}$) of the first relevant document in retrieved results.
2. **Neural Grounding (NLI Cross-Encoder)**:
   - Uses `cross-encoder/nli-deberta-v3-small` to compute Softmax probabilities across `[contradiction, entailment, neutral]` for every claim against retrieved premises.
   - Any claim contradiction ($P_{\text{contra}} \ge 0.40$) flags a critical hallucination and fails the deployment gate.
3. **Security & Red-Teaming Probes**:
   - **Synthetic Secret Exfiltration**: Detects leakage of canary tokens (e.g., `TEST_SECRET_CANARY_9876`).
   - **Unauthorized Tool Calls**: Blocks rogue tools invoked outside the test case allowlist.
   - **Runaway Loop Detection**: Flags repetitive tool execution loops ($N \ge 3$).
   - **Production Latency Gate**: Enforces execution bounds ($\le 8000\text{ms}$).

## How to Run

### Prerequisites
- Python 3.11+
- Installed dependencies (`pip install -r` or `uv sync`)
- For live agent audit: Local Ollama service running with `llama3.2:1b`:
  ```bash
  ollama serve
  ollama pull llama3.2:1b
  ```

### 1. Run the Evaluation Benchmark
Executes the evaluation pipeline over test cases (`data/datasets/test_suite.json`) and mock execution traces (`data/datasets/mock_traces.json`), outputting results to `reports/audit_report.md`:

```bash
uv run python benchmarks/run_eval.py
```

### 2. Run the Live Target Application Audit
Dispatches live adversarial queries to the target agent and audits the responses, outputting to `reports/live_audit_report.md`:

```bash
uv run python benchmarks/run_live_audit.py
```

Generated reports are automatically formatted as GitHub-flavored Markdown in the top-level `reports/` directory.
