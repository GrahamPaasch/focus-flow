import json
from pathlib import Path

import pytest

from cognitive_router.evaluator import EvaluationResult, load_records, replay


def test_load_records_parses_json(tmp_path: Path):
    data = [
        {
            "id": "r1",
            "telemetry": {"keystrokes_per_min": 100},
            "context": {"context_switches_last_hour": 1},
            "task": {
                "task_id": "t1",
                "severity": 3,
                "slo_risk_minutes": 20,
                "model_confidence": 0.7,
                "explanation": "test",
            },
            "baseline": {"human_intervention": True},
        }
    ]
    path = tmp_path / "records.json"
    path.write_text(json.dumps(data))

    records = load_records(path)
    assert len(records) == 1
    assert records[0].task.task_id == "t1"
    assert records[0].baseline_human is True


@pytest.fixture
def sample_records_path(tmp_path: Path) -> Path:
    records = [
        {
            "id": "inc-1",
            "telemetry": {
                "keystrokes_per_min": 140,
                "mouse_moves_per_min": 200,
                "window_focus_changes": 3,
                "pager_events": 1,
                "active_tasks": 3,
                "idle_minutes": 5,
                "queue_depth": 4,
                "calendar_block_minutes": 10,
            },
            "context": {"context_switches_last_hour": 2},
            "task": {
                "task_id": "inc-1",
                "severity": 4,
                "slo_risk_minutes": 30,
                "model_confidence": 0.6,
                "explanation": "test",
            },
            "baseline": {"human_intervention": True},
        },
        {
            "id": "inc-2",
            "telemetry": {
                "keystrokes_per_min": 100,
                "mouse_moves_per_min": 160,
                "window_focus_changes": 1,
                "pager_events": 0,
                "active_tasks": 1,
                "idle_minutes": 12,
                "queue_depth": 1,
                "calendar_block_minutes": 0,
            },
            "context": {"context_switches_last_hour": 0},
            "task": {
                "task_id": "inc-2",
                "severity": 1,
                "slo_risk_minutes": 5,
                "model_confidence": 0.95,
                "explanation": "test",
            },
            "baseline": {"human_intervention": False},
        },
    ]
    path = tmp_path / "records.json"
    path.write_text(json.dumps(records))
    return path


def test_replay_produces_metrics(sample_records_path: Path):
    records = load_records(sample_records_path)
    result = replay(records)
    assert isinstance(result, EvaluationResult)
    assert result.total_tasks == 2
    assert sum(result.strategy_counts.values()) == 2
    assert 0 <= result.router_human_rate <= 1


def test_policy_overrides_change_strategy(sample_records_path: Path):
    records = load_records(sample_records_path)
    default = replay(records)
    strict = replay(records, {"min_confidence_for_auto": 0.99}, label="strict")
    assert strict.policy_label == "strict"
    default_auto = default.strategy_counts.get("auto", 0)
    strict_auto = strict.strategy_counts.get("auto", 0)
    assert strict_auto <= default_auto
