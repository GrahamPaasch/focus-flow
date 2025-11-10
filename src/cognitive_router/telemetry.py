"""Telemetry collection utilities for estimating operator load."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean
from typing import Deque, Dict


@dataclass
class TelemetrySample:
    """Snapshot of interaction and workload signals."""

    timestamp: datetime
    keystrokes_per_min: float
    mouse_moves_per_min: float
    window_focus_changes: int
    pager_events: int
    active_tasks: int
    idle_minutes: float


class TelemetryCollector:
    """Maintains a rolling window of telemetry samples."""

    def __init__(self, window: timedelta | None = None) -> None:
        self.window = window or timedelta(minutes=30)
        self._samples: Deque[TelemetrySample] = deque()

    def record_sample(self, sample: TelemetrySample) -> None:
        self._samples.append(sample)
        self._prune(sample.timestamp)

    def summarize(self) -> Dict[str, float]:
        if not self._samples:
            return {
                "avg_keystrokes": 0.0,
                "avg_mouse_moves": 0.0,
                "window_changes": 0.0,
                "pager_events": 0.0,
                "active_tasks": 0.0,
                "idle_minutes": 0.0,
            }

        samples = list(self._samples)
        return {
            "avg_keystrokes": mean(s.keystrokes_per_min for s in samples),
            "avg_mouse_moves": mean(s.mouse_moves_per_min for s in samples),
            "window_changes": mean(s.window_focus_changes for s in samples),
            "pager_events": mean(s.pager_events for s in samples),
            "active_tasks": mean(s.active_tasks for s in samples),
            "idle_minutes": samples[-1].idle_minutes,
        }

    def _prune(self, latest_timestamp: datetime) -> None:
        cutoff = latest_timestamp - self.window
        while self._samples and self._samples[0].timestamp < cutoff:
            self._samples.popleft()
