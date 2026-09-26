"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { fetchTraceById } from "../../../lib/api";
import { ExecutionTrace, ExecutionSpan } from "../../../lib/types";
import { TraceHeader } from "../../../components/failure-explorer/TraceHeader";
import { ExecutionWaterfall } from "../../../components/failure-explorer/ExecutionWaterfall";
import { AgentDAGFlow } from "../../../components/failure-explorer/AgentDAGFlow";
import { ClaimGroundingView } from "../../../components/failure-explorer/ClaimGroundingView";
import { SecurityAuditCard } from "../../../components/failure-explorer/SecurityAuditCard";
import { SpanDetailDrawer } from "../../../components/failure-explorer/SpanDetailDrawer";
import { RegressionDiffModal } from "../../../components/failure-explorer/RegressionDiffModal";
import { Activity, GitFork, BookOpen, ShieldAlert, AlertCircle, ArrowLeft, Layers, Terminal } from "lucide-react";
import Link from "next/link";

export default function TraceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const traceId = Array.isArray(params.id) ? params.id[0] : (params.id as string);

  const [trace, setTrace] = useState<ExecutionTrace | null>(null);
  const [loading, setLoading] = useState(true);
  const [leftTab, setLeftTab] = useState<"waterfall" | "dag">("waterfall");
  const [rightTab, setRightTab] = useState<"grounding" | "security">("grounding");
  const [selectedSpan, setSelectedSpan] = useState<ExecutionSpan | null>(null);
  const [showDiffModal, setShowDiffModal] = useState(false);

  useEffect(() => {
    if (traceId) {
      setLoading(true);
      fetchTraceById(traceId).then((data) => {
        setTrace(data);
        setLoading(false);
      });
    }
  }, [traceId]);

  if (loading) {
    return (
      <main className="flex-1 w-full max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="w-10 h-10 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-sm font-mono text-slate-400">Streaming forensic telemetry for {traceId}...</p>
      </main>
    );
  }

  if (!trace) {
    return (
      <main className="flex-1 w-full max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="w-14 h-14 rounded-2xl bg-red-950/60 border border-red-500/40 flex items-center justify-center text-red-400 mx-auto mb-4 shadow-[0_0_20px_rgba(239,68,68,0.3)]">
          <AlertCircle className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-bold font-mono text-white mb-2">Trace Record Not Found</h1>
        <p className="text-xs font-mono text-slate-400 max-w-md mx-auto mb-6 leading-relaxed">
          Could not locate execution trace with identifier &quot;{traceId}&quot;. It may have expired or not yet been ingested.
        </p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-700 text-xs font-mono font-semibold text-slate-200 hover:text-white hover:border-cyan-500/60 transition shadow-lg"
        >
          <ArrowLeft className="w-4 h-4 text-cyan-400" />
          <span>Return to Incident Matrix</span>
        </Link>
      </main>
    );
  }

  return (
    <main className="flex-1 w-full max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Trace Header */}
      <TraceHeader trace={trace} onOpenDiff={() => setShowDiffModal(true)} />

      {/* Split-Screen Forensic War Room Workbench */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6 items-start">
        {/* Left Panel: Execution Topology (Waterfall / Decision DAG) */}
        <section aria-label="Execution Topology" className="xl:col-span-6 space-y-4">
          <div className="flex items-center justify-between bg-[#090E1A]/95 border border-slate-800/80 rounded-2xl p-2 shadow-xl backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs font-mono" role="tablist" aria-label="Execution Topology Tabs">
              <button
                role="tab"
                aria-selected={leftTab === "waterfall"}
                id="tab-waterfall"
                onClick={() => setLeftTab("waterfall")}
                className={`flex items-center gap-2 py-2 px-3.5 rounded-xl border transition-all ${
                  leftTab === "waterfall"
                    ? "bg-cyan-950/90 text-cyan-300 border-cyan-500/80 font-bold shadow-[0_0_12px_rgba(6,182,212,0.25)]"
                    : "bg-slate-900/40 text-slate-400 border-transparent hover:text-white"
                }`}
              >
                <Activity className="w-4 h-4 text-cyan-400" />
                <span>Waterfall Timeline</span>
              </button>

              <button
                role="tab"
                aria-selected={leftTab === "dag"}
                id="tab-dag"
                onClick={() => setLeftTab("dag")}
                className={`flex items-center gap-2 py-2 px-3.5 rounded-xl border transition-all ${
                  leftTab === "dag"
                    ? "bg-cyan-950/90 text-cyan-300 border-cyan-500/80 font-bold shadow-[0_0_12px_rgba(6,182,212,0.25)]"
                    : "bg-slate-900/40 text-slate-400 border-transparent hover:text-white"
                }`}
              >
                <GitFork className="w-4 h-4 text-cyan-400" />
                <span>Decision DAG Flow</span>
              </button>
            </div>

            <span className="text-[11px] font-mono text-slate-500 pr-3 hidden sm:inline">
              {trace.spans.length} OpenTelemetry Spans
            </span>
          </div>

          {leftTab === "waterfall" ? (
            <ExecutionWaterfall
              spans={trace.spans}
              totalDurationMs={trace.total_duration_ms}
              selectedSpanId={selectedSpan?.span_id}
              onSelectSpan={(span) => setSelectedSpan(span)}
            />
          ) : (
            <AgentDAGFlow
              spans={trace.spans}
              selectedSpanId={selectedSpan?.span_id}
              onSelectSpan={(span) => setSelectedSpan(span)}
            />
          )}
        </section>

        {/* Right Panel: The Smoking Gun Evidence Locker (DeBERTa Grounding / Security Audit) */}
        <section aria-label="Evidence Locker & Remediation" className="xl:col-span-6 space-y-4">
          <div className="flex items-center justify-between bg-[#090E1A]/95 border border-slate-800/80 rounded-2xl p-2 shadow-xl backdrop-blur-md">
            <div className="flex items-center gap-2 text-xs font-mono" role="tablist" aria-label="Evidence Locker Tabs">
              <button
                role="tab"
                aria-selected={rightTab === "grounding"}
                id="tab-grounding"
                onClick={() => setRightTab("grounding")}
                className={`flex items-center gap-2 py-2 px-3.5 rounded-xl border transition-all ${
                  rightTab === "grounding"
                    ? "bg-red-950/90 text-red-300 border-red-600/80 font-bold shadow-[0_0_12px_rgba(239,68,68,0.25)]"
                    : "bg-slate-900/40 text-slate-400 border-transparent hover:text-white"
                }`}
              >
                <BookOpen className="w-4 h-4 text-red-400" />
                <span>DeBERTa Tensor Grounding</span>
              </button>

              <button
                role="tab"
                aria-selected={rightTab === "security"}
                id="tab-security"
                onClick={() => setRightTab("security")}
                className={`flex items-center gap-2 py-2 px-3.5 rounded-xl border transition-all ${
                  rightTab === "security"
                    ? "bg-red-950/90 text-red-300 border-red-600/80 font-bold shadow-[0_0_12px_rgba(239,68,68,0.25)]"
                    : "bg-slate-900/40 text-slate-400 border-transparent hover:text-white"
                }`}
              >
                <ShieldAlert className="w-4 h-4 text-red-400" />
                <span>Security & Remediation ({trace.findings?.length || 0})</span>
              </button>
            </div>

            <span className="text-[11px] font-mono text-slate-500 pr-3 hidden sm:inline">
              PyTorch CUDA Accelerated
            </span>
          </div>

          {rightTab === "grounding" ? (
            <ClaimGroundingView trace={trace} />
          ) : (
            <SecurityAuditCard findings={trace.findings || []} />
          )}
        </section>
      </div>

      {/* Slide-over Span Inspection Drawer */}
      {selectedSpan && (
        <SpanDetailDrawer
          span={selectedSpan}
          onClose={() => setSelectedSpan(null)}
        />
      )}

      {/* Regression Diff Modal */}
      {showDiffModal && (
        <RegressionDiffModal
          currentTrace={trace}
          onClose={() => setShowDiffModal(false)}
        />
      )}
    </main>
  );
}
