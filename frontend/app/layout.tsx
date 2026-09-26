import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Navbar } from "../components/Navbar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export const metadata: Metadata = {
  title: "AgentGuard | AI Agent Observability & Forensic Failure Explorer",
  description:
    "Pre-deployment reliability testing, GPU-accelerated DeBERTa-v3 contradiction verification, and forensic root-cause analysis for autonomous AI agents.",
  keywords: [
    "AI Agent Observability",
    "Hallucination Detection",
    "DeBERTa NLI",
    "OpenTelemetry Traces",
    "AI Security",
    "Prompt Injection",
  ],
  authors: [{ name: "AgentGuard Engineering Team" }],
  robots: "index, follow",
  openGraph: {
    title: "AgentGuard — Autonomous Agent Reliability & Security Testing",
    description:
      "Forensic failure exploration, real-time OpenTelemetry DAG waterfalls, and claim-level NLI contradiction verification.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased dark bg-[#050811]`}>
      <body className="min-h-full flex flex-col bg-[#050811] text-slate-100 selection:bg-cyan-500/20 selection:text-cyan-200 bg-cyber-grid">
        <Navbar />
        {children}
        <footer className="border-t border-slate-900/80 bg-[#050811]/90 backdrop-blur-md py-6 mt-auto">
          <div className="max-w-[1800px] w-full mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-4">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-400">AgentGuard v0.3.0</span>
              <span>•</span>
              <span>Enterprise Agent Observability Platform</span>
            </div>
            <div className="flex items-center gap-4 font-mono text-[11px]">
              <span className="text-emerald-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                DeBERTa-v3 GPU Online
              </span>
              <span className="text-slate-700">|</span>
              <span className="text-cyan-400">PostgreSQL 16 Connected</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
