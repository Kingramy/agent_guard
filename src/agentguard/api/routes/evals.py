"""Evaluation findings and metrics query endpoints."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from agentguard.storage.database import get_db
from agentguard.storage.repository import TraceRepository

router = APIRouter(prefix="/evals", tags=["Evaluations"])


@router.get("/findings", summary="List diagnostic findings filtered by severity or trace ID")
async def list_findings(
    trace_id: Optional[str] = Query(None, description="Filter by trace ID"),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, HIGH, etc."),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    repo = TraceRepository(db)
    records = await repo.list_findings(trace_id=trace_id, severity=severity, limit=limit)
    return [
        {
            "finding_id": f.id,
            "test_case_id": f.test_case_id,
            "trace_id": f.trace_id,
            "span_id": f.span_id,
            "category": f.category,
            "severity": f.severity,
            "title": f.title,
            "explanation": f.explanation,
            "suggested_remediation": f.suggested_remediation,
            "created_at": f.created_at,
        }
        for f in records
    ]


@router.get("/metrics/{trace_id}", summary="Get evaluation metrics for a specific trace")
async def get_metrics(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
) -> List[Dict[str, Any]]:
    repo = TraceRepository(db)
    records = await repo.get_metrics(trace_id)
    return [
        {
            "metric_name": m.metric_name,
            "score": m.score,
            "passed": m.passed,
            "threshold": m.threshold,
            "details": m.details_payload,
            "created_at": m.created_at,
        }
        for m in records
    ]
