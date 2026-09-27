# AgentGuard Failure Explorer (Frontend Command Center)

An enterprise-grade, real-time observability and security failure diagnosis dashboard for AI agents and RAG pipelines. Built with Next.js 16, Three.js WebGL, Tailwind CSS, and `@xyflow/react`.

## Key Architectural Features

- **3D Neural Defense Lattice (Three.js WebGL)**: Dynamic particle lattice canvas (`EpistemicDefenseCanvas.tsx`) responding to cursor proximity, animating real-time agent neural activity, and pulsating red upon security breaches.
- **Bento Grid Metric Command Center**: High-density glassmorphism cards featuring `NumberTicker`, `BorderBeam`, and `CardSpotlight` displaying latency percentiles, IR retrieval precision, groundedness rates, and vulnerability findings.
- **Interactive Decision DAG Flow (`@xyflow/react`)**: Interactive node-graph rendering agent execution paths:
  - User Prompts & Input Sanitization
  - Vector Retrieval Chunks & Top-K Reranking
  - Tool Invocation Nodes (Allowlisted vs Rogue Tool Calls)
  - LLM Reasoning Steps & DeBERTa NLI Grounding Verification
- **Execution Waterfall View**: Chronological Gantt chart of OpenTelemetry spans detailing exact execution durations, memory allocations, and token consumption per step.
- **DeBERTa-v3 Smoking Gun Evidence Locker**: Split-screen tensor probability view showing Softmax NLI distributions (Entailment, Contradiction, Neutral) directly mapping claims to retrieved source premises.
- **Security Audit Card & Remediation Drawer**: Clear classification of adversarial vectors (Prompt Injection, Canary Token Exfiltration, Unauthorized Tool Execution) with auto-generated inline code patches.
- **Regression Delta Diff Inspector**: Side-by-side visual diff modal comparing passing baseline traces against broken regression runs.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Visuals & 3D**: Three.js, Lucide Icons, Canvas API
- **Graph & DAG**: `@xyflow/react`
- **Styling**: Tailwind CSS, CSS Grid, Glassmorphism, Modern Typography
- **Testing**: Playwright End-to-End Test Suite

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Run the Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### 3. Run Playwright E2E Tests
```bash
npx playwright test
```

To run tests with UI:
```bash
npx playwright test --ui
```

## Directory Structure

```
frontend/
├── app/
│   ├── page.tsx               # Primary Bento Grid & Incident Matrix
│   ├── traces/[id]/page.tsx   # Detailed Trace Waterfall & Smoking Gun Workbench
│   ├── layout.tsx             # Root layout with Dark Obsidian theme
│   └── globals.css            # Custom CSS animations and cybernetic grid styles
├── components/
│   ├── Navbar.tsx             # System status, breadcrumb, and navigation bar
│   ├── failure-explorer/
│   │   ├── AgentDAGFlow.tsx           # Interactive React Flow DAG
│   │   ├── ClaimGroundingView.tsx     # DeBERTa NLI Claim & Premise analyzer
│   │   ├── ExecutionWaterfall.tsx     # OTel Gantt-style span waterfall
│   │   ├── RegressionDiffModal.tsx    # Split-screen regression comparison
│   │   ├── SecurityAuditCard.tsx      # Vulnerability severity & remediations
│   │   ├── SpanDetailDrawer.tsx       # Slide-over raw telemetry metadata
│   │   └── TraceHeader.tsx            # Trace telemetry badges and H1 header
│   └── ui/
│       ├── EpistemicDefenseCanvas.tsx # Three.js WebGL 3D lattice
│       ├── border-beam.tsx            # Animated perimeter border beam
│       ├── card-spotlight.tsx         # Radial gradient hover spotlight
│       └── number-ticker.tsx          # Animated KPI metric ticker
└── tests/
    └── failure-explorer.spec.ts       # 13 comprehensive Playwright E2E tests
```
