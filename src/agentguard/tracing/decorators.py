"""Semantic tracing decorators for agent workflows, retrievals, and tool executions."""

import functools
import inspect
import json
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from agentguard.contracts.schemas import SpanKind


def _serialize_safe(obj: Any) -> str:
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return json.dumps({"repr": repr(obj)})


def trace_agent_run(
    agent_name: str = "agent.run",
    project_id: str = "default",
    agent_version: str = "v1.0.0",
) -> Callable:
    """Decorator marking the root execution span of an agent trajectory."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer("agentguard")
            test_case_id = kwargs.get("test_case_id")

            with tracer.start_as_current_span(agent_name) as span:
                span.set_attribute("agentguard.kind", SpanKind.AGENT_RUN.value)
                span.set_attribute("agentguard.project_id", project_id)
                span.set_attribute("agentguard.agent_version", agent_version)
                if test_case_id:
                    span.set_attribute("agentguard.test_case_id", test_case_id)

                span.set_attribute(
                    "agentguard.input", _serialize_safe({"args": args, "kwargs": kwargs})
                )
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("agentguard.output", _serialize_safe(result))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer("agentguard")
            test_case_id = kwargs.get("test_case_id")

            with tracer.start_as_current_span(agent_name) as span:
                span.set_attribute("agentguard.kind", SpanKind.AGENT_RUN.value)
                span.set_attribute("agentguard.project_id", project_id)
                span.set_attribute("agentguard.agent_version", agent_version)
                if test_case_id:
                    span.set_attribute("agentguard.test_case_id", test_case_id)

                span.set_attribute(
                    "agentguard.input", _serialize_safe({"args": args, "kwargs": kwargs})
                )
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("agentguard.output", _serialize_safe(result))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


def trace_retrieval(source_name: str = "rag.retrieval") -> Callable:
    """Decorator capturing document retrieval operations and result counts."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer("agentguard")
            with tracer.start_as_current_span(source_name) as span:
                span.set_attribute("agentguard.kind", SpanKind.RAG_RETRIEVAL.value)
                span.set_attribute(
                    "agentguard.input", _serialize_safe({"query": args, "kwargs": kwargs})
                )
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("agentguard.output", _serialize_safe(result))
                    if isinstance(result, list):
                        span.set_attribute("rag.retrieved_count", len(result))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer("agentguard")
            with tracer.start_as_current_span(source_name) as span:
                span.set_attribute("agentguard.kind", SpanKind.RAG_RETRIEVAL.value)
                span.set_attribute(
                    "agentguard.input", _serialize_safe({"query": args, "kwargs": kwargs})
                )
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("agentguard.output", _serialize_safe(result))
                    if isinstance(result, list):
                        span.set_attribute("rag.retrieved_count", len(result))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


def trace_tool_call(tool_name: Optional[str] = None) -> Callable:
    """Decorator capturing tool execution payloads and error statuses."""

    def decorator(func: Callable) -> Callable:
        name = tool_name or func.__name__

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer("agentguard")
            with tracer.start_as_current_span(f"tool.{name}") as span:
                span.set_attribute("agentguard.kind", SpanKind.TOOL_EXECUTION.value)
                span.set_attribute("tool.name", name)
                span.set_attribute(
                    "agentguard.input", _serialize_safe({"args": args, "kwargs": kwargs})
                )
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("agentguard.output", _serialize_safe(result))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer("agentguard")
            with tracer.start_as_current_span(f"tool.{name}") as span:
                span.set_attribute("agentguard.kind", SpanKind.TOOL_EXECUTION.value)
                span.set_attribute("tool.name", name)
                span.set_attribute(
                    "agentguard.input", _serialize_safe({"args": args, "kwargs": kwargs})
                )
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("agentguard.output", _serialize_safe(result))
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator


def trace_llm_generation(model_name: str = "mock-llm") -> Callable:
    """Decorator tracking model inference latency, prompts, and token usage."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer("agentguard")
            with tracer.start_as_current_span("llm.generation") as span:
                span.set_attribute("agentguard.kind", SpanKind.LLM_GENERATION.value)
                span.set_attribute("gen_ai.system", "agentguard-llm")
                span.set_attribute("gen_ai.request.model", model_name)
                span.set_attribute(
                    "agentguard.input", _serialize_safe({"prompt": args, "kwargs": kwargs})
                )
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("agentguard.output", _serialize_safe(result))
                    if isinstance(result, dict) and "usage" in result:
                        span.set_attribute(
                            "gen_ai.usage.input_tokens", result["usage"].get("prompt_tokens", 0)
                        )
                        span.set_attribute(
                            "gen_ai.usage.output_tokens",
                            result["usage"].get("completion_tokens", 0),
                        )
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = trace.get_tracer("agentguard")
            with tracer.start_as_current_span("llm.generation") as span:
                span.set_attribute("agentguard.kind", SpanKind.LLM_GENERATION.value)
                span.set_attribute("gen_ai.system", "agentguard-llm")
                span.set_attribute("gen_ai.request.model", model_name)
                span.set_attribute(
                    "agentguard.input", _serialize_safe({"prompt": args, "kwargs": kwargs})
                )
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("agentguard.output", _serialize_safe(result))
                    if isinstance(result, dict) and "usage" in result:
                        span.set_attribute(
                            "gen_ai.usage.input_tokens", result["usage"].get("prompt_tokens", 0)
                        )
                        span.set_attribute(
                            "gen_ai.usage.output_tokens",
                            result["usage"].get("completion_tokens", 0),
                        )
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
