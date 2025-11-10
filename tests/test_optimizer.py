import json
from pathlib import Path

from cognitive_router.optimizer import compute_score, load_grid, optimize


def test_load_grid_normalizes_labels(tmp_path: Path):
    grid_path = tmp_path / "grid.json"
    grid_path.write_text(json.dumps([{"policy": {"slo_weight": 0.5}}, {"label": "custom", "policy": {}}]))
    grid = load_grid(grid_path)
    assert grid[0]["label"] == "policy-1"
    assert grid[1]["label"] == "custom"


def test_compute_score_variants(sample_eval_result):
    assert compute_score(sample_eval_result, "human_rate") == sample_eval_result.router_human_rate
    assert compute_score(sample_eval_result, "human_reduction") == -sample_eval_result.as_dict()[
        "human_reduction_pct"
    ]
    assert compute_score(sample_eval_result, "priority") == -sample_eval_result.average_priority


def test_optimize_orders_candidates(tmp_path: Path, sample_records_json: Path, sample_grid_json: Path):
    results = optimize(sample_records_json, sample_grid_json, objective="human_rate")
    assert results
    assert results[0].score <= results[-1].score
    assert results[0].evaluation.policy_label == results[0].label


# Fixtures
import pytest
from cognitive_router.evaluator import EvaluationResult, load_records


@pytest.fixture
def sample_eval_result() -> EvaluationResult:
    return EvaluationResult(
        total_tasks=2,
        strategy_counts={"immediate": 1, "auto": 1},
        average_priority=0.5,
        average_attention_load=0.4,
        baseline_human_rate=0.6,
        router_human_rate=0.5,
    )


@pytest.fixture
def sample_records_json(tmp_path: Path) -> Path:
    data = [
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
    path.write_text(json.dumps(data))
    return path


@pytest.fixture
def sample_grid_json(tmp_path: Path) -> Path:
    data = [
        {"label": "baseline", "policy": {}},
        {"label": "strict", "policy": {"min_confidence_for_auto": 0.99}},
    ]
    path = tmp_path / "grid.json"
    path.write_text(json.dumps(data))
    return path

