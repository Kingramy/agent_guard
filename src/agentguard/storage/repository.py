"""Storage repository layer mapping Pydantic contracts to SQLAlchemy models."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agentguard.contracts.schemas import (
    EvaluationFinding,
    ExecutionTrace,
    MetricResult,
)
from agentguard.storage.models import (
    FindingRecord,
    MetricRecord,
    ProjectRecord,
    SpanRecord,
    TestCaseRecord,
    TraceRecord,
)


class TraceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_project(self, project_id: str, name: Optional[str] = None) -> ProjectRecord:
        stmt = select(ProjectRecord).where(ProjectRecord.id == project_id)
        result = await self.session.execute(stmt)
        project = result.scalar_one_or_none()
        if not project:
            project = ProjectRecord(
                id=project_id,
                name=name or project_id,
                description="Auto-generated project record",
            )
            self.session.add(project)
            await self.session.flush()
        return project

    async def ensure_test_case(self, test_case_id: str) -> TestCaseRecord:
        stmt = select(TestCaseRecord).where(TestCaseRecord.id == test_case_id)
        result = await self.session.execute(stmt)
        tc = result.scalar_one_or_none()
        if not tc:
            tc = TestCaseRecord(
                id=test_case_id,
                dataset_name="default",
                input_prompt=f"Test case {test_case_id}",
                expected_behavior="Generated placeholder",
            )
            self.session.add(tc)
            await self.session.flush()
        return tc

    async def save_trace(self, trace_contract: ExecutionTrace) -> TraceRecord:
        await self.ensure_project(trace_contract.project_id)
        if trace_contract.test_case_id:
            await self.ensure_test_case(trace_contract.test_case_id)

        # Check if trace already exists (upsert logic)
        existing_stmt = (
            select(TraceRecord)
            .where(TraceRecord.id == trace_contract.trace_id)
            .options(selectinload(TraceRecord.spans))
        )
        existing_res = await self.session.execute(existing_stmt)
        existing_trace = existing_res.scalar_one_or_none()

        if existing_trace:
            existing_trace.end_time = trace_contract.end_time
            existing_trace.total_duration_ms = trace_contract.total_duration_ms
            existing_trace.total_input_tokens = trace_contract.total_input_tokens
            existing_trace.total_output_tokens = trace_contract.total_output_tokens
            existing_trace.status = trace_contract.status.value
            existing_trace.final_output = trace_contract.final_output
            existing_trace.metadata_payload = trace_contract.metadata
            trace_record = existing_trace
        else:
            trace_record = TraceRecord(
                id=trace_contract.trace_id,
                test_case_id=trace_contract.test_case_id,
                project_id=trace_contract.project_id,
                agent_version=trace_contract.agent_version,
                start_time=trace_contract.start_time,
                end_time=trace_contract.end_time,
                total_duration_ms=trace_contract.total_duration_ms,
                total_input_tokens=trace_contract.total_input_tokens,
                total_output_tokens=trace_contract.total_output_tokens,
                status=trace_contract.status.value,
                final_output=trace_contract.final_output,
                metadata_payload=trace_contract.metadata,
            )
            self.session.add(trace_record)
            await self.session.flush()

        # Insert child spans
        existing_span_ids = {s.id for s in trace_record.spans} if existing_trace else set()
        for span_contract in trace_contract.spans:
            if span_contract.span_id not in existing_span_ids:
                span_record = SpanRecord(
                    id=span_contract.span_id,
                    trace_id=trace_contract.trace_id,
                    parent_span_id=span_contract.parent_span_id,
                    name=span_contract.name,
                    kind=span_contract.kind.value,
                    start_time=span_contract.start_time,
                    end_time=span_contract.end_time,
                    duration_ms=span_contract.duration_ms,
                    status=span_contract.status.value,
                    input_payload=span_contract.input_payload,
                    output_payload=span_contract.output_payload,
                    attributes_payload=span_contract.attributes,
                    error_message=span_contract.error_message,
                )
                self.session.add(span_record)

        await self.session.flush()
        return trace_record

    async def get_trace(self, trace_id: str) -> Optional[TraceRecord]:
        stmt = (
            select(TraceRecord)
            .where(TraceRecord.id == trace_id)
            .options(
                selectinload(TraceRecord.spans),
                selectinload(TraceRecord.findings),
                selectinload(TraceRecord.metrics),
            )
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_traces(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TraceRecord]:
        stmt = (
            select(TraceRecord)
            .options(selectinload(TraceRecord.spans))
            .order_by(TraceRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if project_id:
            stmt = stmt.where(TraceRecord.project_id == project_id)
        if status:
            stmt = stmt.where(TraceRecord.status == status)

        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def save_finding(self, finding: EvaluationFinding) -> FindingRecord:
        record = FindingRecord(
            id=finding.finding_id,
            test_case_id=finding.test_case_id,
            trace_id=finding.trace_id,
            span_id=finding.span_id,
            category=finding.category.value,
            severity=finding.severity.value,
            title=finding.title,
            explanation=finding.explanation,
            suggested_remediation=finding.suggested_remediation,
            metadata_payload=finding.metadata,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_findings(
        self,
        trace_id: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[FindingRecord]:
        stmt = select(FindingRecord).order_by(FindingRecord.created_at.desc()).limit(limit)
        if trace_id:
            stmt = stmt.where(FindingRecord.trace_id == trace_id)
        if severity:
            stmt = stmt.where(FindingRecord.severity == severity)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def save_metric(self, trace_id: str, metric: MetricResult) -> MetricRecord:
        record = MetricRecord(
            trace_id=trace_id,
            metric_name=metric.metric_name,
            score=metric.score,
            passed=metric.passed,
            threshold=metric.threshold,
            details_payload=metric.details,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_metrics(self, trace_id: str) -> List[MetricRecord]:
        stmt = select(MetricRecord).where(MetricRecord.trace_id == trace_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
