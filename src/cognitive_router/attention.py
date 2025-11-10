"""Attention/load estimation based on telemetry summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(value, high))


@dataclass
class AttentionConfig:
    incident_weight: float = 0.4
    pager_weight: float = 0.25
    idle_weight: float = 0.2
    context_switch_weight: float = 0.15
    max_active_tasks: float = 5.0
    max_pager_events: float = 4.0
    max_context_switches: float = 6.0
    max_idle_minutes: float = 30.0


class AttentionModel:
    """Produces a scalar load score in [0, 1]."""

    def __init__(self, config: AttentionConfig | None = None) -> None:
        self.config = config or AttentionConfig()

    def score(self, telemetry_summary: Dict[str, float], operator_context: Dict[str, float] | None = None) -> float:
        ctx = operator_context or {}
        incidents = telemetry_summary.get("active_tasks", 0.0)
        pager_events = telemetry_summary.get("pager_events", 0.0)
        idle_minutes = telemetry_summary.get("idle_minutes", self.config.max_idle_minutes)
        context_switches = ctx.get("context_switches_last_hour", 0.0)

        incident_component = _clamp(incidents / self.config.max_active_tasks)
        pager_component = _clamp(pager_events / self.config.max_pager_events)
        idle_component = 1.0 - _clamp(idle_minutes / self.config.max_idle_minutes)
        context_component = _clamp(context_switches / self.config.max_context_switches)

        score = (
            incident_component * self.config.incident_weight
            + pager_component * self.config.pager_weight
            + idle_component * self.config.idle_weight
            + context_component * self.config.context_switch_weight
        )
        return _clamp(score)
