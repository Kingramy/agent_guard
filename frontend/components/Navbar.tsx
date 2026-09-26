import Link from "next/link";
import { ShieldAlert, Activity, Cpu, Database, Radio } from "lucide-react";

export function Navbar() {
  return (
    <header className="border-b border-slate-800/80 bg-[#050811]/85 backdrop-blur-xl sticky top-0 z-40">
      <div className="max-w-[1800px] w-full mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-red-950 via-slate-900 to-slate-950 border border-red-500/40 flex items-center justify-center text-red-400 group-hover:border-red-400 group-hover:shadow-[0_0_15px_rgba(239,68,68,0.4)] transition-all">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="text-base font-extrabold tracking-tight text-white flex items-center gap-2">
                AgentGuard
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-red-950/90 text-red-400 border border-red-700/50 shadow-[0_0_10px_rgba(239,68,68,0.2)]">
                  Forensic Suite
                </span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono tracking-tight">
                Enterprise Autonomous Agent Telemetry & Defect Matrix
              </div>
            </div>
          </Link>
        </div>

        <div className="flex items-center space-x-5 text-xs">
          <Link
            href="/"
            className="text-slate-300 hover:text-white transition-colors flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-slate-800 hover:border-slate-700 font-medium"
          >
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            <span>Incident Command</span>
          </Link>

          {/* Live Telemetry Beacon */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-emerald-300">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-mono text-[11px] font-medium tracking-tight">
              Live Telemetry Stream Active
            </span>
          </div>

          <div className="hidden lg:flex items-center space-x-2.5 pl-4 border-l border-slate-800 text-[11px] font-mono">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#090E1A] border border-slate-800/80 text-slate-300">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <span>DeBERTa-v3 (CUDA)</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#090E1A] border border-slate-800/80 text-slate-300">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <span>PostgreSQL 16</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
