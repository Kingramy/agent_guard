---
name: agentguard-otel-tracing
description: Implementation runbook for OpenTelemetry GenAI semantic conventions, context propagation, and span hierarchy in AgentGuard.
---

# AgentGuard OpenTelemetry Tracing

Runbook for instrumenting AI agents, tool calls, and RAG pipelines to emit standardized OpenTelemetry spans that AgentGuard can parse, persist, and visualize.

## 1. GenAI Semantic Conventions

Spans emitted by target agents must populate standard attributes:
- `gen_ai.system`: Identifier of the LLM provider or local engine (e.g. `openai`, `anthropic`, `ollama`).
- `gen_ai.request.model`: Model identifier (e.g. `llama-3-70b`, `gpt-4o`).
- `gen_ai.usage.input_tokens`: Prompt token count (integer).
- `gen_ai.usage.output_tokens`: Completion token count (integer).
- `agentguard.kind`: Span category enum (`agent.run`, `rag.retrieval`, `tool.execution`, `llm.generation`, `security.gate`).

## 2. Span Hierarchy Mapping

An execution trace forms a Directed Acyclic Graph (DAG):
```
agent.run (Root Span: parent_span_id = None)
├── tool.search_policies (Parent: agent.run)
│   └── rag.retrieval (Parent: tool.search_policies, records retrieved docs & scores)
├── llm.generation (Parent: agent.run, records prompt, completion, token usage)
└── tool.process_refund (Parent: agent.run, records financial transaction parameters)
```

## 3. Decorator Usage

Use higher-order decorators from `agentguard.tracing.decorators`:
```python
from agentguard.tracing.decorators import (
    trace_agent_run,
    trace_retrieval,
    trace_tool_call,
    trace_llm_generation
)

@trace_agent_run(agent_name="PolicyAgent", project_id="demo", agent_version="v1.0.0")
def run_agent(query: str, test_case_id: str | None = None):
    ...

@trace_tool_call(tool_name="lookup_user")
def tool_lookup(user_id: str):
    ...
```

## 4. In-Memory Buffering vs. HTTP Exporters

- In unit tests: Use `AgentGuardTraceBuffer` via `get_trace_buffer()` to inspect reconstructed `ExecutionTrace` objects in-memory.
- In production / live agents: Configure standard `OTLPSpanExporter` pointing to AgentGuard's FastAPI endpoint (`POST /api/v1/traces/ingest`).
