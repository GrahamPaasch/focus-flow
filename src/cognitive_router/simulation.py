"""Command-line simulation for the cognitive bandwidth router."""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime, timedelta
from typing import Iterable, List

from .attention import AttentionModel
from .context import CalendarLoadContextProvider, QueueDepthContextProvider, StaticContextProvider
from .event_bus import InMemoryEventBus
from .router import RouterService
from .task_models import TaskIntent
from .telemetry import TelemetryCollector, TelemetrySample
from .workflow import InMemoryWorkflowEngine


def _seed_telemetry(collector: TelemetryCollector, now: datetime) -> None:
    for minutes_ago in range(30, -1, -5):
        timestamp = now - timedelta(minutes=minutes_ago)
        collector.record_sample(
            TelemetrySample(
                timestamp=timestamp,
                keystrokes_per_min=random.uniform(80, 200),
                mouse_moves_per_min=random.uniform(120, 350),
                window_focus_changes=random.randint(1, 6),
                pager_events=random.randint(0, 2),
                active_tasks=random.randint(1, 4),
                idle_minutes=random.uniform(0, 10),
                queue_depth=random.randint(0, 10),
                calendar_block_minutes=random.uniform(0, 25),
            )
        )


def _random_task(task_id: int) -> TaskIntent:
    severity = random.randint(1, 5)
    slo_risk = random.uniform(5, 45)
    confidence = random.uniform(0.4, 0.99)
    explanation = random.choice(
        [
            "SLO drift detected",
            "Policy compliance uncertainty",
            "Data ambiguity requires review",
            "User escalation waiting",
        ]
    )
    sensitivity = random.choice(["standard", "pii", "security"])
    return TaskIntent(
        task_id=f"task-{task_id}",
        severity=severity,
        slo_risk_minutes=slo_risk,
        model_confidence=confidence,
        explanation=explanation,
        sensitivity_tag=sensitivity,
    )


def run_simulation(tasks: int, seed: int) -> List[str]:
    random.seed(seed)
    telemetry = TelemetryCollector()
    attention_model = AttentionModel()
    router = RouterService(telemetry=telemetry, attention_model=attention_model)
    workflow = InMemoryWorkflowEngine()
    now = datetime.now(UTC)
    _seed_telemetry(telemetry, now)

    router.register_context_provider(QueueDepthContextProvider(lambda: len(workflow.items)))
    router.register_context_provider(
        CalendarLoadContextProvider(lambda: random.uniform(0, 30))
    )
    router.register_context_provider(
        StaticContextProvider({"context_switches_last_hour": random.randint(1, 6)})
    )

    outputs: List[str] = []

    def sink_printer(strategy: str):
        def _inner(work_item):
            outputs.append(
                f"[{strategy.upper()}] {work_item.task.task_id} -> {work_item.rationale} "
                f"queue={len(workflow.items)}"
            )

        return _inner

    for strategy in ("immediate", "batch"):
        router.register_sink(strategy, workflow.enqueue)

    for strategy in ("immediate", "batch", "auto", "park"):
        router.register_sink(strategy, sink_printer(strategy))

    bus = InMemoryEventBus()
    bus.subscribe("tasks.intent", router.handle_task)

    for idx in range(1, tasks + 1):
        bus.publish("tasks.intent", _random_task(idx))

    return outputs


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Simulate the cognitive bandwidth router")
    parser.add_argument("--tasks", type=int, default=5, help="Number of task intents to simulate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args(list(argv) if argv is not None else None)

    outputs = run_simulation(tasks=args.tasks, seed=args.seed)
    for line in outputs:
        print(line)


if __name__ == "__main__":
    main()
