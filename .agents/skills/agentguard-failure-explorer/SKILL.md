---
name: agentguard-failure-explorer
description: Engineering guidelines for building the Failure Explorer UI, span waterfall DAGs, and trace-based diff diagnosis.
---

# AgentGuard Failure Explorer UI

Runbook for constructing the Failure Explorer interface in Next.js / React to provide visual, trace-based root-cause diagnosis.

## 1. Trace Waterfall Visualization

Traditional test runners show only a red failure text. The Failure Explorer visualizes the exact execution tree:

```
[0ms] ── agent.run ────────────────────────────────────────────── [450ms]
         ├── [10ms] ── tool.search_policies ────── [120ms]
         │              └── [20ms] ── rag.retrieval ── [110ms] (Found 2 chunks)
         ├── [130ms] ── llm.generation ─────────── [380ms] (250 tokens)
         └── [390ms] ── tool.process_refund ────── [440ms] [FAILED: >$500 limit]
```

### Key UI Features
- **Hierarchical Indentation**: Group child spans beneath their parent span based on `span.parent_span_id`.
- **Horizontal Bar Positioning**:
  - `offset_left = ((span.start_time - trace.start_time) / trace.total_duration) * 100%`
  - `bar_width = (span.duration_ms / trace.total_duration_ms) * 100%`
- **Color by Status**:
  - Emerald (`#10b981`): Success
  - Rose (`#f43f5e`): Error / Blocked
  - Blue (`#3b82f6`): Retrieval
  - Violet (`#8b5cf6`): LLM Generation

## 2. Root-Cause Diagnostic Card

When a developer clicks on a failed test case, render an evidence card showing:
1. **Finding Summary**: Badge (`CRITICAL`, `HIGH`), Title, Category (`Prompt Injection`, `Hallucination`).
2. **Culprit Span**: Highlighting the exact step that introduced the failure (e.g. `rag.retrieval` returning 0 relevant docs, or `llm.generation` introducing ungrounded claims).
3. **Evidence Diff**: Side-by-side view comparing:
   - Retrieved Context Chunks vs. Generated Output.
   - Reference Answer vs. Generated Output.
4. **Remediation Recommendation**: Direct technical guidance (e.g. `"Tighten tool parameter validation before execution"` or `"Increase dense retrieval top_k from 2 to 4"`).

## 3. Regression Diffing (Version A vs. Version B)

Support comparing two evaluation runs:
- Display metric deltas ($\Delta \text{MRR}$, $\Delta \text{Latency}$, $\Delta \text{Tokens}$).
- Highlight newly introduced findings (regressions) in red, and resolved findings in green.
