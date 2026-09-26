"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Clock, Layers, Copy, Check, GitCompare, AlertTriangle, ShieldCheck, Cpu } from "lucide-react";
import { ExecutionTrace } from "../../lib/types";

interface TraceHeaderProps {
  trace: ExecutionTrace;
  onOpenDiff?: () => void;
}

export function TraceHeader({ trace, onOpenDiff }: TraceHeaderProps) {
  const [copied, setCopied] = useState(false);

  const copyId = () => {
    navigator.clipboard.writeText(trace.trace_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isError = trace.status === "error";

  return (
    <div className="bg-[#090E1A]/95 border border-slate-800/90 rounded-2xl p-6 shadow-2xl backdrop-blur-xl">
      <div className="flex flex-wrap items-center justify-between gap-4 pb-5 border-b border-slate-800/80">
        <div className="flex items-center space-x-4">
          <Link
            href="/"
            aria-label="Back to Incident Command"
            className="p-2 rounded-xl bg-slate-900 border border-slate-700/80 text-slate-400 hover:text-white hover:border-cyan-500/50 transition-all shadow-md"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>

          <div>
            <div className="flex items-center gap-2.5">
              <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-widest font-bold">
                Forensic Incident Investigation
              </span>
              <span className="text-xs text-slate-600">•</span>
              <button
                onClick={copyId}
                className="flex items-center gap-1.5 text-xs font-mono text-slate-300 hover:text-white bg-slate-900 px-2.5 py-1 rounded-md border border-slate-800 hover:border-slate-700 transition"
                title="Click to copy Trace ID"
              >
                <span>{trace.trace_id}</span>
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-500" />}
              </button>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-white mt-1 flex items-center gap-3">
              {trace.test_case_id ? `Probe: ${trace.test_case_id}` : `Trace: ${trace.trace_id}`}
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {onOpenDiff && (
            <button
              onClick={onOpenDiff}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-900/90 hover:bg-slate-800 text-slate-200 border border-slate-700 hover:border-cyan-400 text-xs font-mono font-semibold transition shadow-lg group"
              id="diff-compare-btn"
            >
              <GitCompare className="w-4 h-4 text-cyan-400 group-hover:rotate-180 transition-transform" />
              <span>Regression Diff</span>
            </button>
          )}

          <div
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold uppercase tracking-wider border shadow-lg ${
              isError
                ? "bg-red-950/80 text-red-300 border-red-700/80 shadow-[0_0_15px_rgba(239,68,68,0.25)]"
                : "bg-emerald-950/80 text-emerald-300 border-emerald-700/80 shadow-[0_0_15px_rgba(16,185,129,0.25)]"
            }`}
          >
            {isError ? <AlertTriangle className="w-4 h-4 text-red-400" /> : <ShieldCheck className="w-4 h-4 text-emerald-400" />}
            <span>{isError ? "Incident Detected" : "Grounded Pass"}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-5 text-xs font-mono">
        <div className="bg-slate-950/70 rounded-xl p-3.5 border border-slate-800/80">
          <div className="text-slate-400 flex items-center gap-1.5 mb-1 text-[11px] uppercase tracking-wider">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>Trace Latency</span>
          </div>
          <div className="text-base font-bold text-white">
            {trace.total_duration_ms ? `${trace.total_duration_ms} ms` : "N/A"}
          </div>
        </div>

        <div className="bg-slate-950/70 rounded-xl p-3.5 border border-slate-800/80">
          <div className="text-slate-400 flex items-center gap-1.5 mb-1 text-[11px] uppercase tracking-wider">
            <Layers className="w-3.5 h-3.5 text-violet-400" />
            <span>Tokens (In / Out)</span>
          </div>
          <div className="text-base font-bold text-white">
            {trace.total_input_tokens ?? 0} <span className="text-slate-500 font-normal">/</span> {trace.total_output_tokens ?? 0}
          </div>
        </div>

        <div className="bg-slate-950/70 rounded-xl p-3.5 border border-slate-800/80">
          <div className="text-slate-400 mb-1 text-[11px] uppercase tracking-wider">Agent Version</div>
          <div className="text-base font-bold text-white">{trace.agent_version}</div>
        </div>

        <div className="bg-slate-950/70 rounded-xl p-3.5 border border-slate-800/80">
          <div className="text-slate-400 mb-1 text-[11px] uppercase tracking-wider">Project ID</div>
          <div className="text-base font-bold text-cyan-400 truncate">{trace.project_id}</div>
        </div>
      </div>
    </div>
  );
}
