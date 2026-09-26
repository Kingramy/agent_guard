"""Trace ingestion and retrieval endpoints."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from agentguard.contracts.schemas import ExecutionTrace
from agentguard.storage.database import get_db
from agentguard.storage.repository import TraceRepository
from agentguard.workers.tasks import evaluate_trace_task

router = APIRouter(prefix="/traces", tags=["Traces"])
logger = logging.getLogger("agentguard.api.traces")


@router.post(
    "/ingest",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest OpenTelemetry execution trace and dispatch background evaluation",
)
async def ingest_trace(
    trace_payload: ExecutionTrace,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    repo = TraceRepository(db)
    trace_record = await repo.save_trace(trace_payload)

    # Dispatch asynchronous background evaluation via Celery
    task_dispatched = False
    task_id = None
    try:
        celery_res = evaluate_trace_task.delay(trace_payload.trace_id)
        task_id = celery_res.id
        task_dispatched = True
    except Exception as e:
        logger.warning(f"Could not dispatch Celery task for trace {trace_payload.trace_id}: {e}")

    return {
        "status": "accepted",
        "trace_id": trace_record.id,
        "spans_count": len(trace_payload.spans),
        "task_dispatched": task_dispatched,
        "celery_task_id": task_id,
    }


@router.get(
    "/{trace_id}",
    summary="Get full execution trace hierarchy and evaluation findings by ID",
)
async def get_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    repo = TraceRepository(db)
    record = await repo.get_trace(trace_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution trace '{trace_id}' not found.",
        )

    return {
        "trace_id": record.id,
        "test_case_id": record.test_case_id,
        "project_id": record.project_id,
        "agent_version": record.agent_version,
        "start_time": record.start_time,
        "end_time": record.end_time,
        "total_duration_ms": record.total_duration_ms,
        "total_input_tokens": record.total_input_tokens,
        "total_output_tokens": record.total_output_tokens,
        "status": record.status,
        "final_output": record.final_output,
        "metadata": record.metadata_payload,
        "spans": [
            {
                "span_id": s.id,
                "parent_span_id": s.parent_span_id,
                "name": s.name,
                "kind": s.kind,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "duration_ms": s.duration_ms,
                "status": s.status,
                "input_payload": s.input_payload,
                "output_payload": s.output_payload,
                "attributes": s.attributes_payload,
                "error_message": s.error_message,
            }
            for s in record.spans
        ],
        "findings": [
            {
                "finding_id": f.id,
                "span_id": f.span_id,
                "category": f.category,
                "severity": f.severity,
                "title": f.title,
                "explanation": f.explanation,
                "suggested_remediation": f.suggested_remediation,
            }
            for f in record.findings
        ],
        "metrics": [
            {
                "metric_name": m.metric_name,
                "score": m.score,
                "passed": m.passed,
                "threshold": m.threshold,
                "details": m.details_payload,
            }
            for m in record.metrics
        ],
    }


@router.get(
    "",
    summary="List execution traces with optional project and status filtering",
)
async def list_traces(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    repo = TraceRepository(db)
    records = await repo.list_traces(
        project_id=project_id, status=status_filter, limit=limit, offset=offset
    )
    return [
        {
            "trace_id": r.id,
            "test_case_id": r.test_case_id,
            "project_id": r.project_id,
            "agent_version": r.agent_version,
            "start_time": r.start_time,
            "duration_ms": r.total_duration_ms,
            "status": r.status,
            "spans_count": len(r.spans),
            "created_at": r.created_at,
        }
        for r in records
    ]
