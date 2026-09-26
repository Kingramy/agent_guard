"use client";

import { useEffect, useState } from "react";
import { ExecutionSpan } from "../../lib/types";
import { X, Copy, Check, Terminal, Clock, Info } from "lucide-react";

interface SpanDetailDrawerProps {
  span: ExecutionSpan | null;
  onClose: () => void;
}

export function SpanDetailDrawer({ span, onClose }: SpanDetailDrawerProps) {
  const [activeTab, setActiveTab] = useState<"overview" | "input" | "output" | "attributes" | "raw">("overview");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!span) return null;

  const copyPayload = (data: unknown) => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isError = span.status === "error";

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="drawer-title"
      className="fixed inset-y-0 right-0 w-full sm:w-[540px] bg-[#0B0F19] border-l border-slate-800 shadow-2xl z-50 flex flex-col transform transition-transform duration-300 ease-in-out"
      id="span-detail-drawer"
    >
      {/* Drawer Header */}
      <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                isError
                  ? "bg-red-950 text-red-400 border-red-800"
                  : "bg-emerald-950 text-emerald-400 border-emerald-800"
              }`}
            >
              {span.status}
            </span>
            <span className="text-xs font-mono text-cyan-400">{span.kind}</span>
          </div>
          <h2 id="drawer-title" className="text-base font-bold text-white truncate max-w-[380px]">
            {span.name}
          </h2>
        </div>

        <button
          onClick={onClose}
          aria-label="Close span inspector drawer"
          className="p-1.5 rounded-lg text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 bg-slate-950/50 px-4 text-xs font-medium">
        {(["overview", "input", "output", "attributes", "raw"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`py-2.5 px-3 border-b-2 font-mono uppercase tracking-wider text-[11px] transition-colors ${
              activeTab === tab
                ? "border-cyan-400 text-cyan-400 font-semibold"
                : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {activeTab === "overview" && (
          <div className="space-y-4">
            {span.error_message && (
              <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-500/50 text-red-200 text-xs leading-relaxed">
                <div className="font-bold flex items-center gap-1.5 mb-1 text-red-400 font-mono uppercase text-[10px]">
                  <Info className="w-3.5 h-3.5" /> Error Diagnostic
                </div>
                {span.error_message}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <div className="text-slate-400 mb-1 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-cyan-400" /> Duration
                </div>
                <div className="font-mono font-semibold text-white">{span.duration_ms ?? 0} ms</div>
              </div>
              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
                <div className="text-slate-400 mb-1 flex items-center gap-1">
                  <Terminal className="w-3 h-3 text-violet-400" /> Kind
                </div>
                <div className="font-mono font-semibold text-white truncate">{span.kind}</div>
              </div>
            </div>

            <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-2 text-xs">
              <div>
                <span className="text-slate-400">Span ID: </span>
                <span className="font-mono text-cyan-400 select-all">{span.span_id}</span>
              </div>
              <div>
                <span className="text-slate-400">Trace ID: </span>
                <span className="font-mono text-slate-300 select-all">{span.trace_id}</span>
              </div>
              <div>
                <span className="text-slate-400">Parent Span: </span>
                <span className="font-mono text-slate-400">
                  {span.parent_span_id || "None (Root Span)"}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Start Time: </span>
                <span className="font-mono text-slate-300">{span.start_time}</span>
              </div>
              {span.end_time && (
                <div>
                  <span className="text-slate-400">End Time: </span>
                  <span className="font-mono text-slate-300">{span.end_time}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "input" && (
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Input Payload</span>
              <button
                onClick={() => copyPayload(span.input_payload)}
                className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy JSON"}</span>
              </button>
            </div>
            <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto max-h-[460px]">
              {JSON.stringify(span.input_payload || {}, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === "output" && (
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Output Payload</span>
              <button
                onClick={() => copyPayload(span.output_payload)}
                className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy JSON"}</span>
              </button>
            </div>
            <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto max-h-[460px]">
              {JSON.stringify(span.output_payload || {}, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === "attributes" && (
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">OpenTelemetry Attributes</span>
              <button
                onClick={() => copyPayload(span.attributes)}
                className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy JSON"}</span>
              </button>
            </div>
            <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto max-h-[460px]">
              {JSON.stringify(span.attributes || {}, null, 2)}
            </pre>
          </div>
        )}

        {activeTab === "raw" && (
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Complete Span Record</span>
              <button
                onClick={() => copyPayload(span)}
                className="flex items-center gap-1 text-[11px] text-cyan-400 hover:text-cyan-300"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy JSON"}</span>
              </button>
            </div>
            <pre className="p-4 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 overflow-x-auto max-h-[460px]">
              {JSON.stringify(span, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
