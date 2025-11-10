from datetime import UTC, datetime

from cognitive_router.attention import AttentionModel
from cognitive_router.telemetry import TelemetryCollector, TelemetrySample


def test_attention_score_increases_with_load():
    collector = TelemetryCollector()
    now = datetime.now(UTC)
    collector.record_sample(
        TelemetrySample(
            timestamp=now,
            keystrokes_per_min=120,
            mouse_moves_per_min=200,
            window_focus_changes=2,
            pager_events=0,
            active_tasks=1,
            idle_minutes=8,
        )
    )
    model = AttentionModel()

    low_load = model.score(collector.summarize(), {"context_switches_last_hour": 0})

    collector.record_sample(
        TelemetrySample(
            timestamp=now,
            keystrokes_per_min=40,
            mouse_moves_per_min=90,
            window_focus_changes=6,
            pager_events=4,
            active_tasks=5,
            idle_minutes=0,
        )
    )
    high_load = model.score(collector.summarize(), {"context_switches_last_hour": 6})

    assert high_load > low_load
    assert 0.0 <= high_load <= 1.0
