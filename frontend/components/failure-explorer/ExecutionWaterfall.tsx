"use client";

import { useMemo } from "react";
import { ExecutionSpan } from "../../lib/types";
import { Layers, Database, Sparkles, Terminal, ShieldAlert, AlertCircle, CheckCircle2 } from "lucide-react";

interface ExecutionWaterfallProps {
  spans: ExecutionSpan[];
  totalDurationMs?: number | null;
  selectedSpanId?: string | null;
  onSelectSpan: (span: ExecutionSpan) => void;
}

export function ExecutionWaterfall({
  spans,
  totalDurationMs,
  selectedSpanId,
  onSelectSpan,
}: ExecutionWaterfallProps) {
  // Compute timeline bounds
  const { minTime, maxDuration } = useMemo(() => {
    if (!spans || spans.length === 0) {
      return { minTime: 0, maxDuration: totalDurationMs || 1000 };
    }
    const startTimestamps = spans.map((s) => new Date(s.start_time).getTime());
    const min = Math.min(...startTimestamps);
    const endTimestamps = spans.map((s) =>
      s.end_time ? new Date(s.end_time).getTime() : min + (s.duration_ms || 100)
    );
    const maxEnd = Math.max(...endTimestamps);
    const computedDuration = Math.max(maxEnd - min, totalDurationMs || 100, 100);
    return { minTime: min, maxDuration: computedDuration };
  }, [spans, totalDurationMs]);

  const getSpanIcon = (kind: string) => {
    switch (kind) {
      case "rag.retrieval":
        return <Database className="w-3.5 h-3.5 text-cyan-400" />;
      case "llm.generation":
        return <Sparkles className="w-3.5 h-3.5 text-violet-400" />;
      case "tool.execution":
        return <Terminal className="w-3.5 h-3.5 text-amber-400" />;
      case "security.gate":
        return <ShieldAlert className="w-3.5 h-3.5 text-red-400" />;
      default:
        return <Layers className="w-3.5 h-3.5 text-blue-400" />;
    }
  };

  const getBarColor = (span: ExecutionSpan) => {
    if (span.status === "error") {
      return "bg-gradient-to-r from-red-600 via-rose-600 to-red-500 border-red-400/80 shadow-[0_0_15px_rgba(239,68,68,0.4)]";
    }
    switch (span.kind) {
      case "rag.retrieval":
        return "bg-gradient-to-r from-cyan-600 to-cyan-400 border-cyan-300/80 shadow-[0_0_10px_rgba(6,182,212,0.3)]";
      case "llm.generation":
        return "bg-gradient-to-r from-violet-600 to-purple-500 border-violet-400/80 shadow-[0_0_10px_rgba(139,92,246,0.3)]";
      case "tool.execution":
        return "bg-gradient-to-r from-amber-600 to-amber-500 border-amber-400/80 shadow-[0_0_10px_rgba(245,158,11,0.3)]";
      default:
        return "bg-gradient-to-r from-blue-600 to-blue-500 border-blue-400/80";
    }
  };

  if (!spans || spans.length === 0) {
    return (
      <div className="bg-[#090E1A] border border-slate-800 rounded-2xl p-8 text-center text-slate-500 font-mono text-xs">
        No execution spans recorded for this trace.
      </div>
    );
  }

  // Ticks for timeline header (0%, 25%, 50%, 75%, 100%)
  const ticks = [0, 0.25, 0.5, 0.75, 1.0];

  return (
    <div className="bg-[#090E1A]/95 border border-slate-800/90 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl" id="execution-waterfall">
      <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
        <div>
          <h2 className="text-xs font-mono font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span>Millisecond Execution Waterfall</span>
          </h2>
          <p className="text-[11px] font-mono text-slate-400">
            Chronological span distribution and latency breakdown
          </p>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>RAG</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-violet-400" />
            <span>LLM</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-amber-400" />
            <span>Tool</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-400" />
            <span>Error</span>
          </div>
        </div>
      </div>

      {/* Timeline Header Ruler */}
      <div className="grid grid-cols-12 px-4 py-2 border-b border-slate-800/80 text-[10px] font-mono text-slate-500 bg-slate-950/90 select-none">
        <div className="col-span-4 text-slate-400 uppercase tracking-wider">Span & Kind</div>
        <div className="col-span-8 relative">
          <div className="flex justify-between w-full">
            {ticks.map((t, idx) => (
              <span key={idx} className="tabular-nums">
                {Math.round(t * maxDuration)}ms
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Span rows */}
      <div className="divide-y divide-slate-800/50">
        {spans.map((span) => {
          const spanStart = new Date(span.start_time).getTime();
          const offsetMs = Math.max(0, spanStart - minTime);
          const duration = span.duration_ms ?? 50;

          const leftPercent = Math.min(100, Math.max(0, (offsetMs / maxDuration) * 100));
          const widthPercent = Math.min(100 - leftPercent, Math.max(2, (duration / maxDuration) * 100));

          const isSelected = selectedSpanId === span.span_id;
          const isError = span.status === "error";

          return (
            <div
              key={span.span_id}
              role="button"
              tabIndex={0}
              aria-label={`Inspect span ${span.name}, duration ${duration} milliseconds, status ${span.status}`}
              onClick={() => onSelectSpan(span)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onSelectSpan(span);
                }
              }}
              className={`grid grid-cols-12 px-4 py-3 items-center transition cursor-pointer hover:bg-slate-800/50 focus:outline-none focus:bg-slate-800/70 group ${
                isSelected ? "bg-slate-800/90 border-l-2 border-cyan-400" : ""
              }`}
            >
              {/* Left Column: Name & Metadata */}
              <div className="col-span-4 flex items-center space-x-2.5 truncate pr-2">
                {span.parent_span_id && (
                  <span className="text-slate-600 font-mono text-xs pl-1">└─</span>
                )}
                <div className="p-1 rounded bg-slate-900 border border-slate-800 flex-shrink-0 group-hover:border-slate-700">
                  {getSpanIcon(span.kind)}
                </div>
                <div className="truncate">
                  <div className="text-xs font-mono font-bold text-slate-200 truncate flex items-center gap-1.5 group-hover:text-white">
                    <span className="truncate">{span.name}</span>
                    {isError ? (
                      <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 animate-pulse" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400/80 flex-shrink-0" />
                    )}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 truncate">
                    {span.kind} • {duration}ms
                  </div>
                </div>
              </div>

              {/* Right Column: Visual Timeline Bar */}
              <div className="col-span-8 relative h-7 flex items-center">
                {/* Background gridlines */}
                <div className="absolute inset-0 flex justify-between pointer-events-none opacity-15">
                  {ticks.map((_, i) => (
                    <div key={i} className="border-r border-slate-600 h-full" />
                  ))}
                </div>

                {/* Interactive bar */}
                <div
                  style={{
                    left: `${leftPercent}%`,
                    width: `${widthPercent}%`,
                  }}
                  className={`absolute h-5 rounded-md border text-[10px] font-mono font-bold text-white flex items-center px-2 truncate transition-all duration-150 group-hover:scale-[1.01] ${getBarColor(
                    span
                  )}`}
                  title={`${span.name}: ${duration}ms (at +${offsetMs}ms)`}
                >
                  <span className="truncate drop-shadow">{duration}ms</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
