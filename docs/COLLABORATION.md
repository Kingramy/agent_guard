# AgentGuard Engineering Collaboration Guide

This handbook defines the division of responsibilities, interface contracts, local development workflows, and git discipline between **Ramy** (AI Models, Metrics & Evaluation) and **Hamza** (Platform, Tracing & Infrastructure).

---

## 1. Team Ownership Matrix

| Area | Lead Engineer | Primary Directories | Key Deliverables |
| :--- | :--- | :--- | :--- |
| **AI Models & Evaluation** | **Ramy ([@Kingramy](https://github.com/Kingramy))** | `src/agentguard/evaluators/`<br>`data/datasets/` | • Deterministic IR evaluators (MRR, Precision@K, Recall@K)<br>• Tool call schema validator<br>• DeBERTa-v3 NLI cross-encoder groundedness judge<br>• Curated evaluation datasets & adversarial test cases |
| **Platform & Infrastructure** | **Hamza ([@Hamza-HATTAB](https://github.com/Hamza-HATTAB))** | `src/agentguard/tracing/`<br>`src/agentguard/storage/`<br>`src/agentguard/workers/`<br>`src/agentguard/api/`<br>`src/agentguard/security/`<br>`src/agentguard/cli/` | • OpenTelemetry tracing SDK and GenAI span decorators<br>• PostgreSQL 16 schema & SQLAlchemy 2.0 async persistence<br>• Redis 7 + Celery asynchronous evaluation queue<br>• AI Security defense (secret scanners, runaway loop checks)<br>• Next.js Failure Explorer dashboard<br>• CI/CD Quality Gate CLI (`agentguard test`) |
| **Shared Interface** | **Both Engineers** | `src/agentguard/contracts/schemas.py` | Strict Pydantic v2 data models. Neither engineer modifies this file without a mutual review. |

---

## 2. Directory Layout & Code Boundaries

```
agentguard/
├── src/agentguard/
│   ├── contracts/        <-- SHARED: Single source of truth (Pydantic v2 schemas)
│   ├── evaluators/       <-- RAMY: IR metrics, tool accuracy, DeBERTa NLI
│   ├── agent/            <-- Reference LangGraph target agent
│   ├── tracing/          <-- HAMZA: OTel provider, decorators, span buffer
│   ├── storage/          <-- HAMZA: PostgreSQL models & async repository
│   ├── workers/          <-- HAMZA: Redis & Celery task handlers
│   ├── api/              <-- HAMZA: FastAPI ingestion & query routes
│   ├── security/         <-- HAMZA: Secret leakage, loop, and escalation checks
│   └── cli/              <-- HAMZA: CLI runner for CI/CD gates
├── benchmarks/           <-- RAMY: Offline benchmark suite and live audit runners
├── data/
│   └── datasets/         <-- RAMY: Benchmark test suites & mock execution traces
├── reports/              <-- Evaluation & security audit markdown reports
├── frontend/             <-- HAMZA: Next.js Failure Explorer dashboard
├── tests/
│   ├── evaluators/       <-- RAMY: Unit tests for IR metrics & NLI models
│   ├── tracing/          <-- HAMZA: Tests for OTel context and span emission
│   └── platform/         <-- HAMZA: Tests for FastAPI, Postgres & Celery
├── docs/                 <-- Architecture, specifications, and guides
├── docker-compose.yml    <-- Infrastructure (PostgreSQL 16, Redis 7)
└── Makefile              <-- Development commands (install, test, lint, format)
```

---

## 3. Shared Interface Contracts (`contracts/schemas.py`)

All cross-module communication relies exclusively on the frozen models in `src/agentguard/contracts/schemas.py`:

```
                       ┌──────────────────────┐
                       │       TestCase       │ (Defined by Ramy)
                       └──────────┬───────────┘
                                  │ Target Agent Execution
                                  ▼
                       ┌──────────────────────┐
                       │    ExecutionTrace    │ (Emitted by Hamza's Tracer)
                       │   ├── ExecutionSpan  │
                       │   └── ExecutionSpan  │
                       └──────────┬───────────┘
                                  │ Input to Evaluators
                                  ▼
                ┌───────────────────────────────────┐
                │        Evaluation Pipeline        │ (Built by Ramy & Hamza)
                └─────────┬───────────────┬─────────┘
                          │               │
                          ▼               ▼
               ┌────────────────┐  ┌───────────────────┐
               │  MetricResult  │  │ EvaluationFinding │
               └────────────────┘  └───────────────────┘
```

### Data Flow Protocol
1. **Ramy defines the test probes** using `TestCase`.
2. **Hamza executes the target agent and captures the trajectory** inside an `ExecutionTrace` containing hierarchical `ExecutionSpan` objects.
3. **Ramy inspects the trace** and extracts:
   - Retrieved documents from `span.kind == SpanKind.RAG_RETRIEVAL`
   - Tool calls from `span.kind == SpanKind.TOOL_EXECUTION`
   - Generated claims from `span.kind == SpanKind.LLM_GENERATION`
4. **Ramy returns evaluation results**:
   - Numeric metrics as `MetricResult` (e.g. `score=0.85`, `passed=True`)
   - Qualitative defects as `EvaluationFinding` (e.g. `severity=SeverityLevel.CRITICAL`, `category=SecurityCategory.CONTRADICTION_HALLUCINATION`)
5. **Hamza stores the findings in PostgreSQL** and renders them in the Failure Explorer UI or triggers a CI exit code in `agentguard test`.

---

## 4. Local Development Decoupling (Mock-Driven Testing)

Neither engineer is blocked waiting for the other:

### How Ramy develops without the backend
Ramy does **not** need PostgreSQL, Redis, or Celery running to build and test evaluators.
Unit tests run directly against mock `ExecutionTrace` fixtures:

```python
from agentguard.contracts.schemas import ExecutionTrace, ExecutionSpan, SpanKind, TestCase
from agentguard.evaluators.deterministic import calculate_mrr

def test_mrr_calculation():
    # 1. Create a dummy test case expecting "doc_1.pdf"
    test_case = TestCase(
        id="tc_001",
        input="What is the refund window?",
        expected_behavior="State 30-day limit",
        expected_sources=["doc_1.pdf"]
    )

    # 2. Create a mock trace with a retrieval span
    trace = ExecutionTrace(
        trace_id="dummy_trace",
        spans=[
            ExecutionSpan(
                trace_id="dummy_trace",
                name="rag.kb_search",
                kind=SpanKind.RAG_RETRIEVAL,
                output_payload=[
                    {"doc_id": "irrelevant.pdf"},
                    {"doc_id": "doc_1.pdf"} # Rank 2 -> MRR = 0.5
                ]
            )
        ]
    )

    # 3. Test your metric function in isolation
    result = calculate_mrr(trace, test_case)
    assert result.score == 0.5
    assert result.passed is True
```

### How Hamza develops without the ML models
Hamza can implement the task queue, database schema, and dashboard using stubbed evaluator functions that return dummy `MetricResult` and `EvaluationFinding` objects.

---

## 5. Quickstart for Ramy

### 1. Clone the repository
```bash
git clone git@github.com:Hamza-HATTAB/agentguard.git
cd agentguard
```

### 2. Install dependencies with `uv`
Ensure you have Python 3.11+ and `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`):
```bash
make install
```

### 3. Start local services
```bash
make up
# Launches PostgreSQL 16 and Redis 7 in Docker
```

### 4. Verify test suite
```bash
make test
make lint
```

---

## 6. Git Discipline & Pull Request Standards

### Branch Naming Conventions
- Ramy (Evaluation & Models):
  - `feat/eval-mrr-precision`
  - `feat/eval-deberta-nli`
  - `feat/dataset-adversarial-hr`
- Hamza (Platform & Security):
  - `feat/platform-db-schema`
  - `feat/platform-celery-worker`
  - `feat/security-loop-detector`
- Bug fixes:
  - `fix/span-timestamp-serialization`

### Commit Message Guidelines (Conventional Commits)
Use standard prefix tags:
- `feat(...)`: New feature (e.g. `feat(eval): implement Precision@K and MRR formulas`)
- `fix(...)`: Bug fix (e.g. `fix(tracing): correct parent span id assignment`)
- `docs(...)`: Documentation updates
- `test(...)`: Adding or updating test cases
- `refactor(...)`: Code refactoring without behavioral changes

### Pull Request Checklist
Before opening a PR into `main`:
1. [ ] Run `make lint` to ensure `ruff` passes with zero errors.
2. [ ] Run `make test` to ensure all `pytest` unit tests pass.
3. [ ] If you modified `contracts/schemas.py`, obtain explicit approval from the other teammate.
