"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Position,
  Handle,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { ExecutionSpan } from "../../lib/types";
import { Database, Sparkles, Terminal, ShieldAlert, Layers } from "lucide-react";

interface AgentDAGFlowProps {
  spans: ExecutionSpan[];
  selectedSpanId?: string | null;
  onSelectSpan: (span: ExecutionSpan) => void;
}

// Custom Node component
function CustomSpanNode({ data }: { data: any }) {
  const isError = data.status === "error";
  const isSelected = data.isSelected;

  const getIcon = () => {
    switch (data.kind) {
      case "rag.retrieval":
        return <Database className="w-4 h-4 text-cyan-400" />;
      case "llm.generation":
        return <Sparkles className="w-4 h-4 text-violet-400" />;
      case "tool.execution":
        return <Terminal className="w-4 h-4 text-amber-400" />;
      case "security.gate":
        return <ShieldAlert className="w-4 h-4 text-red-400" />;
      default:
        return <Layers className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div
      className={`min-w-[210px] rounded-xl p-3 shadow-2xl transition-all duration-200 border text-left ${
        isSelected
          ? "border-cyan-400 bg-slate-900 ring-2 ring-cyan-400/40"
          : isError
          ? "border-red-500/80 bg-red-950/40 hover:border-red-400"
          : "border-slate-800 bg-slate-900/95 hover:border-slate-700"
      }`}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-slate-500 !w-2 !h-2"
      />
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-slate-800 border border-slate-700">
            {getIcon()}
          </div>
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
            {data.kind}
          </div>
        </div>
        <span
          className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
            isError
              ? "bg-red-950 text-red-400 border border-red-800/80"
              : "bg-emerald-950 text-emerald-400 border border-emerald-800/80"
          }`}
        >
          {data.status}
        </span>
      </div>

      <div className="text-xs font-bold text-white truncate mb-1">
        {data.label}
      </div>

      <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 pt-2 border-t border-slate-800/80">
        <span>Latency:</span>
        <span className="text-slate-200">{data.duration_ms ?? 0} ms</span>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-slate-500 !w-2 !h-2"
      />
    </div>
  );
}

const nodeTypes = {
  customSpan: CustomSpanNode,
};

export function AgentDAGFlow({
  spans,
  selectedSpanId,
  onSelectSpan,
}: AgentDAGFlowProps) {
  const { nodes, edges } = useMemo(() => {
    if (!spans || spans.length === 0) {
      return { nodes: [], edges: [] };
    }

    const calculatedNodes: Node[] = [];
    const calculatedEdges: Edge[] = [];

    // Group spans by depth / parent relationships
    const spanMap = new Map<string, ExecutionSpan>();
    spans.forEach((s) => spanMap.set(s.span_id, s));

    // Calculate hierarchical level
    const depthMap = new Map<string, number>();
    const getDepth = (id: string): number => {
      if (depthMap.has(id)) return depthMap.get(id)!;
      const s = spanMap.get(id);
      if (!s || !s.parent_span_id || !spanMap.has(s.parent_span_id)) {
        depthMap.set(id, 0);
        return 0;
      }
      const d = 1 + getDepth(s.parent_span_id);
      depthMap.set(id, d);
      return d;
    };

    spans.forEach((s) => getDepth(s.span_id));

    // Group by depth
    const levels: ExecutionSpan[][] = [];
    spans.forEach((s) => {
      const d = depthMap.get(s.span_id) || 0;
      if (!levels[d]) levels[d] = [];
      levels[d].push(s);
    });

    const levelHeight = 160;
    const nodeWidth = 260;

    levels.forEach((levelSpans, depth) => {
      const totalWidth = levelSpans.length * nodeWidth;
      levelSpans.forEach((span, index) => {
        const xPos = index * nodeWidth - totalWidth / 2 + 150;
        const yPos = depth * levelHeight + 30;

        calculatedNodes.push({
          id: span.span_id,
          type: "customSpan",
          position: { x: xPos, y: yPos },
          data: {
            label: span.name,
            kind: span.kind,
            status: span.status,
            duration_ms: span.duration_ms,
            isSelected: selectedSpanId === span.span_id,
          },
        });

        if (span.parent_span_id && spanMap.has(span.parent_span_id)) {
          calculatedEdges.push({
            id: `edge_${span.parent_span_id}_${span.span_id}`,
            source: span.parent_span_id,
            target: span.span_id,
            animated: span.status === "error",
            style: {
              stroke: span.status === "error" ? "#ef4444" : "#475569",
              strokeWidth: 2,
            },
          });
        }
      });
    });

    return { nodes: calculatedNodes, edges: calculatedEdges };
  }, [spans, selectedSpanId]);

  if (nodes.length === 0) {
    return (
      <div className="bg-[#0B0F19] border border-slate-800 rounded-xl p-8 text-center text-slate-400">
        No DAG nodes available to render.
      </div>
    );
  }

  return (
    <div
      className="bg-[#0B0F19] border border-slate-800 rounded-xl overflow-hidden shadow-xl h-[480px] relative"
      id="agent-dag-flow"
    >
      <div className="absolute top-3 left-4 z-10 bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-1.5 backdrop-blur-md">
        <h2 className="text-xs font-semibold text-white">Execution Decision DAG</h2>
        <p className="text-[10px] font-mono text-slate-400">
          Node relationships and causal propagation
        </p>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => {
          const span = spans.find((s) => s.span_id === node.id);
          if (span) onSelectSpan(span);
        }}
        fitView
        className="bg-[#090D16]"
      >
        <Background color="#1e293b" gap={16} size={1} />
        <Controls className="!bg-slate-900 !border-slate-800 !text-slate-200" />
        <MiniMap
          nodeColor={(n) => {
            const data = n.data as any;
            return data?.status === "error" ? "#ef4444" : "#0284c7";
          }}
          className="!bg-slate-950/80 !border !border-slate-800 rounded-lg"
          maskColor="rgba(15, 23, 42, 0.7)"
        />
      </ReactFlow>
    </div>
  );
}
