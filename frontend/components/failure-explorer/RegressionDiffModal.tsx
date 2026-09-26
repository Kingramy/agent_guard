"use client";

import { useEffect } from "react";
import { ExecutionTrace } from "../../lib/types";
import { MOCK_TRACES } from "../../lib/mock-data";
import { X, GitCompare, ArrowRight, ShieldCheck, AlertTriangle } from "lucide-react";

interface RegressionDiffModalProps {
  currentTrace: ExecutionTrace;
  onClose: () => void;
}

export function RegressionDiffModal({ currentTrace, onClose }: RegressionDiffModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  // Baseline clean pass trace
  const baseline = MOCK_TRACES.find((t) => t.trace_id === "trace_clean_pass_01") || currentTrace;

  const currentDuration = currentTrace.total_duration_ms ?? 0;
  const baselineDuration = baseline.total_duration_ms ?? 0;
  const durationDiff = currentDuration - baselineDuration;

  const currentTokens = (currentTrace.total_input_tokens || 0) + (currentTrace.total_output_tokens || 0);
  const baselineTokens = (baseline.total_input_tokens || 0) + (baseline.total_output_tokens || 0);
  const tokensDiff = currentTokens - baselineTokens;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="diff-modal-title"
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
      id="regression-diff-modal"
    >
      <div className="bg-[#0B0F19] border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-500/30 text-cyan-400">
              <GitCompare className="w-5 h-5" />
            </div>
            <div>
              <h2 id="diff-modal-title" className="text-base font-bold text-white">
                Regression Delta Inspector
              </h2>
              <p className="text-xs text-slate-400">
                Comparative telemetry diff against Golden Baseline ({baseline.trace_id})
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close regression modal"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Delta KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Latency Delta</div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold font-mono text-white">
                  {currentDuration} ms
                </span>
                <span
                  className={`text-xs font-mono font-semibold ${
                    durationDiff > 0 ? "text-red-400" : "text-emerald-400"
                  }`}
                >
                  {durationDiff > 0 ? `+${durationDiff}ms` : `${durationDiff}ms`}
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                Baseline: {baselineDuration} ms
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Token Volume Delta</div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold font-mono text-white">
                  {currentTokens} tokens
                </span>
                <span
                  className={`text-xs font-mono font-semibold ${
                    tokensDiff > 0 ? "text-amber-400" : "text-emerald-400"
                  }`}
                >
                  {tokensDiff > 0 ? `+${tokensDiff}` : `${tokensDiff}`}
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-1">
                Baseline: {baselineTokens} tokens
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Critical Defect Delta</div>
              <div className="flex items-baseline gap-2">
                <span className="text-lg font-bold font-mono text-red-400">
                  {currentTrace.findings?.length || 0} findings
                </span>
                <span className="text-xs font-mono text-red-400 font-semibold">
                  +{currentTrace.findings?.length || 0}
                </span>
              </div>
              <div className="text-[10px] text-slate-400 mt-1">Baseline: 0 findings</div>
            </div>
          </div>

          {/* Side-by-Side Output Comparison */}
          <div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-1.5">
              <span>Agent Response Differential</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> Baseline Grounded Run
                  </span>
                  <span className="text-[10px] font-mono text-emerald-300">
                    {baseline.trace_id}
                  </span>
                </div>
                <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-950/60 p-3 rounded border border-slate-800">
                  {baseline.final_output}
                </p>
              </div>

              <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-red-400 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Current Candidate Incident
                  </span>
                  <span className="text-[10px] font-mono text-red-300">
                    {currentTrace.trace_id}
                  </span>
                </div>
                <p className="text-xs text-slate-300 font-mono leading-relaxed bg-slate-950/60 p-3 rounded border border-slate-800">
                  {currentTrace.final_output}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
