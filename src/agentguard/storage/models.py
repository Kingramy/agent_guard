"""SQLAlchemy 2.0 declarative database models for AgentGuard storage."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    traces: Mapped[List["TraceRecord"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )


class TestCaseRecord(Base):
    __tablename__ = "test_cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_name: Mapped[str] = mapped_column(String(128), index=True, default="default")
    input_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expected_sources: Mapped[List[str]] = mapped_column(JSONB, default=list)
    security_category: Mapped[str] = mapped_column(String(64), index=True, default="benign")
    allowed_tools: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    metadata_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class TraceRecord(Base):
    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    test_case_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("test_cases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("projects.id", ondelete="CASCADE"), default="default", index=True
    )
    agent_version: Mapped[str] = mapped_column(String(32), default="v1.0.0", index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="success", index=True)
    final_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    project: Mapped[Optional["ProjectRecord"]] = relationship(back_populates="traces")
    spans: Mapped[List["SpanRecord"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan", lazy="selectin"
    )
    findings: Mapped[List["FindingRecord"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan", lazy="selectin"
    )
    metrics: Mapped[List["MetricRecord"]] = relationship(
        back_populates="trace", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_traces_meta_gin", metadata_payload, postgresql_using="gin"),
        Index("ix_traces_proj_created", project_id, created_at.desc()),
    )


class SpanRecord(Base):
    __tablename__ = "spans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trace_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_span_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="success", index=True)
    input_payload: Mapped[Any] = mapped_column(JSONB, default=dict)
    output_payload: Mapped[Any] = mapped_column(JSONB, default=dict)
    attributes_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    trace: Mapped["TraceRecord"] = relationship(back_populates="spans")

    __table_args__ = (
        Index("ix_spans_attrs_gin", attributes_payload, postgresql_using="gin"),
        Index("ix_spans_trace_parent", trace_id, parent_span_id),
    )


class FindingRecord(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    test_case_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    trace_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    span_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_remediation: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    trace: Mapped["TraceRecord"] = relationship(back_populates="findings")


class MetricRecord(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    threshold: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    details_payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    trace: Mapped["TraceRecord"] = relationship(back_populates="metrics")
