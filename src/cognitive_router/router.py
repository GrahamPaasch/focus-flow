"""Routing policy and service implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from .attention import AttentionModel
from .context import ContextProvider
from .task_models import TaskIntent, WorkItem
from .telemetry import TelemetryCollector

Sink = Callable[[WorkItem], None]


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(value, high))


@dataclass
class RoutingPolicy:
    slo_weight: float = 0.4
    uncertainty_weight: float = 0.25
    severity_weight: float = 0.25
    attention_weight: float = 0.1
    slo_risk_norm: float = 30.0
    immediate_threshold: float = 0.75
    batch_threshold: float = 0.45
    min_confidence_for_auto: float = 0.85

    def compute_priority(self, task: TaskIntent, attention_load: float) -> float:
        slo_component = _clamp(task.slo_risk_minutes / self.slo_risk_norm)
        uncertainty_component = _clamp(1.0 - task.model_confidence)
        severity_component = _clamp(task.severity / 5.0)
        attention_component = _clamp(attention_load)

        priority = (
            slo_component * self.slo_weight
            + uncertainty_component * self.uncertainty_weight
            + severity_component * self.severity_weight
            + attention_component * self.attention_weight
        )
        return _clamp(priority)

    def route_strategy(self, task: TaskIntent, priority: float) -> str:
        if task.severity >= 5 or priority >= self.immediate_threshold:
            return "immediate"
        if priority >= self.batch_threshold:
            return "batch"
        if task.model_confidence >= self.min_confidence_for_auto and task.severity <= 2:
            return "auto"
        return "park"


class RouterService:
    """Transforms TaskIntent events into actionable WorkItems."""

    def __init__(
        self,
        telemetry: TelemetryCollector,
        attention_model: AttentionModel,
        policy: RoutingPolicy | None = None,
    ) -> None:
        self.telemetry = telemetry
        self.attention_model = attention_model
        self.policy = policy or RoutingPolicy()
        self.operator_context: Dict[str, float] = {"context_switches_last_hour": 0.0}
        self._sinks: Dict[str, List[Sink]] = {"immediate": [], "batch": [], "auto": [], "park": []}
        self._context_providers: List[ContextProvider] = []

    def update_operator_context(self, **fields: float) -> None:
        self.operator_context.update(fields)

    def register_sink(self, strategy: str, handler: Sink) -> None:
        if strategy not in self._sinks:
            raise ValueError(f"Unknown strategy '{strategy}'")
        self._sinks[strategy].append(handler)

    def register_context_provider(self, provider: ContextProvider) -> None:
        self._context_providers.append(provider)

    def handle_task(self, task: TaskIntent) -> WorkItem:
        telemetry_summary = self.telemetry.summarize()
        context_snapshot = self._build_context_snapshot()
        for key in ("queue_depth", "calendar_block_minutes"):
            if key in context_snapshot:
                telemetry_summary[key] = context_snapshot[key]
        attention_load = self.attention_model.score(telemetry_summary, context_snapshot)
        priority = self.policy.compute_priority(task, attention_load)
        strategy = self.policy.route_strategy(task, priority)
        rationale = self._build_rationale(task, priority, attention_load)
        work_item = WorkItem(
            task_id=task.task_id,
            route_strategy=strategy,
            priority=priority,
            attention_load=attention_load,
            task=task,
            rationale=rationale,
        )
        for sink in self._sinks.get(strategy, []):
            sink(work_item)
        return work_item

    def _build_context_snapshot(self) -> Dict[str, float]:
        snapshot = dict(self.operator_context)
        for provider in self._context_providers:
            snapshot.update(provider.snapshot())
        return snapshot

    def _build_rationale(self, task: TaskIntent, priority: float, attention_load: float) -> str:
        return (
            f"priority={priority:.2f} slo_risk={task.slo_risk_minutes:.1f}m "
            f"confidence={task.model_confidence:.2f} attention_load={attention_load:.2f}"
        )
