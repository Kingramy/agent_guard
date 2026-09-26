import { EvaluationFinding } from "../../lib/types";
import { ShieldAlert, AlertTriangle, CheckCircle2, Wrench, FileCode2 } from "lucide-react";

interface SecurityAuditCardProps {
  findings: EvaluationFinding[];
}

export function SecurityAuditCard({ findings }: SecurityAuditCardProps) {
  if (!findings || findings.length === 0) {
    return (
      <div className="bg-[#0B0F19] border border-slate-800 rounded-xl p-6 text-center shadow-xl">
        <div className="w-10 h-10 rounded-full bg-emerald-950/60 border border-emerald-500/30 flex items-center justify-center text-emerald-400 mx-auto mb-3">
          <CheckCircle2 className="w-5 h-5" />
        </div>
        <h2 className="text-sm font-semibold text-white">Zero Security Deficiencies Detected</h2>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Automated canary token exfiltration checks, prompt injection fuzzers, and loop circuit breakers passed with 100% compliance.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4" id="security-audit-card">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-red-400" />
          <span>Security & Reliability Findings ({findings.length})</span>
        </h2>
        <span className="text-xs font-mono text-slate-400">
          OWASP Top 10 for LLMs / Automated Red-Team Audit
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {findings.map((f) => {
          const isCritical = f.severity === "CRITICAL";

          return (
            <div
              key={f.finding_id}
              className="bg-[#0B0F19] border border-red-500/30 rounded-xl p-5 shadow-xl relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 bottom-0 w-1.5 bg-red-500" />

              <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                      isCritical
                        ? "bg-red-950 text-red-300 border-red-800"
                        : "bg-amber-950 text-amber-300 border-amber-800"
                    }`}
                  >
                    {f.severity}
                  </span>
                  <span className="text-xs font-mono text-slate-400 uppercase">
                    {f.category}
                  </span>
                </div>
                <span className="text-xs font-mono text-slate-500">
                  ID: {f.finding_id}
                </span>
              </div>

              <h3 className="text-base font-bold text-white mb-2">{f.title}</h3>
              <p className="text-xs text-slate-300 leading-relaxed mb-4 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                {f.explanation}
              </p>

              {/* Remediation Patch Suggestion */}
              <div className="border-t border-slate-800 pt-3">
                <div className="text-xs font-semibold text-cyan-400 flex items-center gap-1.5 mb-2">
                  <Wrench className="w-3.5 h-3.5" />
                  <span>Recommended Architectural Remediation</span>
                </div>
                <p className="text-xs text-slate-300 mb-2">
                  {f.suggested_remediation}
                </p>

                <div className="bg-slate-950 rounded-lg p-3 border border-slate-800 font-mono text-xs text-slate-200">
                  <div className="text-[10px] text-slate-400 flex items-center gap-1 mb-1.5">
                    <FileCode2 className="w-3 h-3 text-cyan-400" /> Suggested Defense Gate Diff
                  </div>
                  <pre className="text-emerald-400 font-mono text-[11px] overflow-x-auto">
{`+ @guardrail.enforce(
+     contradiction_threshold=0.50,
+     redact_patterns=[r"AGY_SEC_[a-zA-Z0-9_]+"],
+     max_consecutive_tool_invocations=2
+ )`}
                  </pre>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
