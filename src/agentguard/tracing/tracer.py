"""OpenTelemetry instrumentation bridge for AgentGuard."""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace import StatusCode

from agentguard.contracts.schemas import (
    ExecutionSpan,
    ExecutionTrace,
    SpanKind,
    SpanStatus,
)

logger = logging.getLogger("agentguard.tracing")


class AgentGuardTraceBuffer(SpanExporter):
    """Buffers finished OpenTelemetry spans in-memory and reconstructs execution traces."""

    def __init__(self) -> None:
        self._spans_by_trace: Dict[str, List[ExecutionSpan]] = {}
        self._traces: Dict[str, ExecutionTrace] = {}

    def export(self, spans: List[ReadableSpan]) -> SpanExportResult:
        for otel_span in spans:
            trace_id = format(otel_span.context.trace_id, "032x")
            span_id = format(otel_span.context.span_id, "016x")
            parent_id = (
                format(otel_span.parent.span_id, "016x")
                if otel_span.parent and otel_span.parent.is_valid
                else None
            )

            status = SpanStatus.SUCCESS
            if otel_span.status.status_code == StatusCode.ERROR:
                status = SpanStatus.ERROR

            kind_str = otel_span.attributes.get("agentguard.kind", SpanKind.TOOL_EXECUTION.value)
            try:
                kind = SpanKind(kind_str)
            except ValueError:
                kind = SpanKind.TOOL_EXECUTION

            input_payload = {}
            if "agentguard.input" in otel_span.attributes:
                try:
                    input_payload = json.loads(otel_span.attributes["agentguard.input"])
                except Exception:
                    input_payload = {"raw": str(otel_span.attributes["agentguard.input"])}

            output_payload = {}
            if "agentguard.output" in otel_span.attributes:
                try:
                    output_payload = json.loads(otel_span.attributes["agentguard.output"])
                except Exception:
                    output_payload = {"raw": str(otel_span.attributes["agentguard.output"])}

            clean_attrs = {
                k: v
                for k, v in otel_span.attributes.items()
                if not k.startswith("agentguard.input") and not k.startswith("agentguard.output")
            }

            start_dt = datetime.fromtimestamp(otel_span.start_time / 1e9, tz=timezone.utc)
            end_dt = (
                datetime.fromtimestamp(otel_span.end_time / 1e9, tz=timezone.utc)
                if otel_span.end_time
                else None
            )
            duration_ms = (
                (otel_span.end_time - otel_span.start_time) / 1e6 if otel_span.end_time else None
            )

            span_contract = ExecutionSpan(
                span_id=span_id,
                trace_id=trace_id,
                parent_span_id=parent_id,
                name=otel_span.name,
                kind=kind,
                start_time=start_dt,
                end_time=end_dt,
                duration_ms=duration_ms,
                status=status,
                input_payload=input_payload,
                output_payload=output_payload,
                attributes=clean_attrs,
                error_message=otel_span.status.description,
            )

            if trace_id not in self._spans_by_trace:
                self._spans_by_trace[trace_id] = []
            self._spans_by_trace[trace_id].append(span_contract)

        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        spans = self._spans_by_trace.get(trace_id, [])
        if not spans:
            return None

        root_spans = [s for s in spans if s.parent_span_id is None]
        root_span = root_spans[0] if root_spans else spans[0]

        start_time = min(s.start_time for s in spans)
        end_times = [s.end_time for s in spans if s.end_time]
        end_time = max(end_times) if end_times else None

        trace_obj = ExecutionTrace(
            trace_id=trace_id,
            test_case_id=root_span.attributes.get("agentguard.test_case_id"),
            project_id=root_span.attributes.get("agentguard.project_id", "default"),
            agent_version=root_span.attributes.get("agentguard.agent_version", "v1.0.0"),
            start_time=start_time,
            end_time=end_time,
            final_output=root_span.output_payload.get("answer")
            or root_span.output_payload.get("output"),
            spans=spans,
            metadata=root_span.attributes,
        )
        trace_obj.calculate_aggregates()
        return trace_obj

    def clear(self) -> None:
        self._spans_by_trace.clear()
        self._traces.clear()


_TRACE_BUFFER = AgentGuardTraceBuffer()


def setup_tracer(service_name: str = "agentguard-agent") -> trace.Tracer:
    provider = TracerProvider()
    processor = SimpleSpanProcessor(_TRACE_BUFFER)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


def get_trace_buffer() -> AgentGuardTraceBuffer:
    return _TRACE_BUFFER
