"""Data models for agent-emitted tasks and routed work items."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(slots=True)
class TaskIntent:
    task_id: str
    severity: int
    slo_risk_minutes: float
    model_confidence: float
    explanation: str
    sensitivity_tag: str = "standard"
    source: str = "agent"
    created_at: datetime = field(default_factory=_now)


@dataclass(slots=True)
class WorkItem:
    task_id: str
    route_strategy: str
    priority: float
    attention_load: float
    task: TaskIntent
    rationale: str
