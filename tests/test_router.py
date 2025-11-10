from datetime import UTC, datetime

from cognitive_router.attention import AttentionModel
from cognitive_router.context import QueueDepthContextProvider
from cognitive_router.router import RouterService
from cognitive_router.task_models import TaskIntent
from cognitive_router.telemetry import TelemetryCollector, TelemetrySample


def _build_router() -> RouterService:
    collector = TelemetryCollector()
    now = datetime.now(UTC)
    collector.record_sample(
        TelemetrySample(
            timestamp=now,
            keystrokes_per_min=100,
            mouse_moves_per_min=150,
            window_focus_changes=3,
            pager_events=1,
            active_tasks=2,
            idle_minutes=5,
        )
    )
    return RouterService(telemetry=collector, attention_model=AttentionModel())


def test_high_severity_goes_immediate():
    router = _build_router()
    task = TaskIntent(
        task_id="sev-1",
        severity=5,
        slo_risk_minutes=50,
        model_confidence=0.5,
        explanation="Critical incident",
    )
    work_item = router.handle_task(task)
    assert work_item.route_strategy == "immediate"


def test_low_severity_high_confidence_auto_resolves():
    router = _build_router()
    task = TaskIntent(
        task_id="auto-1",
        severity=1,
        slo_risk_minutes=5,
        model_confidence=0.95,
        explanation="Routine drift",
    )
    work_item = router.handle_task(task)
    assert work_item.route_strategy == "auto"


def test_medium_priority_batches():
    router = _build_router()
    task = TaskIntent(
        task_id="batch-1",
        severity=3,
        slo_risk_minutes=25,
        model_confidence=0.6,
        explanation="Follow-up",
    )
    work_item = router.handle_task(task)
    assert work_item.route_strategy in {"batch", "immediate"}


def test_context_provider_increases_attention_load():
    baseline_router = _build_router()
    queue_router = _build_router()
    queue_router.register_context_provider(QueueDepthContextProvider(lambda: 25))
    task = TaskIntent(
        task_id="queue-1",
        severity=2,
        slo_risk_minutes=15,
        model_confidence=0.7,
        explanation="Queue pressure",
    )
    baseline = baseline_router.handle_task(task)
    with_queue = queue_router.handle_task(task)
    assert with_queue.attention_load >= baseline.attention_load
