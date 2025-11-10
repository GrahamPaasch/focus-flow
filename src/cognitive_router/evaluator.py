"""Offline policy evaluation utilities."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Sequence

from .attention import AttentionModel
from .router import RouterService, RoutingPolicy
from .task_models import TaskIntent
from .telemetry import TelemetryCollector, TelemetrySample


@dataclass
class HistoricalRecord:
    """Container for a single replay record."""

    record_id: str
    telemetry: Dict[str, float]
    context: Dict[str, float]
    task: TaskIntent
    baseline_human: bool


@dataclass
class EvaluationResult:
    total_tasks: int
    strategy_counts: Dict[str, int]
    average_priority: float
    average_attention_load: float
    baseline_human_rate: float
    router_human_rate: float
    policy_label: str = "default"

    def as_dict(self) -> Dict[str, float | Dict[str, int]]:
        return {
            "total_tasks": self.total_tasks,
            "strategy_counts": self.strategy_counts,
            "average_priority": self.average_priority,
            "average_attention_load": self.average_attention_load,
            "baseline_human_rate": self.baseline_human_rate,
            "router_human_rate": self.router_human_rate,
            "human_reduction_pct": self._human_reduction_pct(),
            "policy_label": self.policy_label,
        }

    def _human_reduction_pct(self) -> float:
        if self.baseline_human_rate == 0:
            return 0.0
        reduction = self.baseline_human_rate - self.router_human_rate
        return reduction / self.baseline_human_rate * 100.0


def load_records(path: str | Path) -> List[HistoricalRecord]:
    data = json.loads(Path(path).read_text())
    records: List[HistoricalRecord] = []
    for entry in data:
        telemetry = entry.get("telemetry", {})
        context = entry.get("context", {})
        task_data = entry["task"]
        task = TaskIntent(
            task_id=task_data["task_id"],
            severity=task_data["severity"],
            slo_risk_minutes=task_data["slo_risk_minutes"],
            model_confidence=task_data["model_confidence"],
            explanation=task_data.get("explanation", ""),
            sensitivity_tag=task_data.get("sensitivity_tag", "standard"),
            source=task_data.get("source", "agent"),
        )
        baseline = entry.get("baseline", {})
        records.append(
            HistoricalRecord(
                record_id=entry.get("id", task.task_id),
                telemetry=telemetry,
                context=context,
                task=task,
                baseline_human=bool(baseline.get("human_intervention", True)),
            )
        )
    return records


def _parse_policy_arg(raw: str) -> Dict[str, float]:
    candidate = Path(raw)
    text = candidate.read_text() if candidate.exists() else raw
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("--policy must be a JSON object with RoutingPolicy fields")
    return data


def _load_grid(path: Path) -> List[Dict[str, Dict[str, float] | str]]:
    entries = json.loads(path.read_text())
    if not isinstance(entries, list):
        raise ValueError("--grid must point to a JSON list")
    grid = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict) or "policy" not in entry:
            raise ValueError("Each grid entry must include a 'policy' object")
        label = entry.get("label") or f"policy-{idx+1}"
        policy = entry["policy"]
        if not isinstance(policy, dict):
            raise ValueError("'policy' must be a JSON object")
        grid.append({"label": label, "policy": policy})
    return grid


def _sample_from_summary(summary: Dict[str, float]) -> TelemetrySample:
    timestamp = datetime.now(UTC)
    return TelemetrySample(
        timestamp=timestamp,
        keystrokes_per_min=summary.get("keystrokes_per_min", 0.0),
        mouse_moves_per_min=summary.get("mouse_moves_per_min", 0.0),
        window_focus_changes=int(summary.get("window_focus_changes", 0)),
        pager_events=int(summary.get("pager_events", 0)),
        active_tasks=int(summary.get("active_tasks", 0)),
        idle_minutes=summary.get("idle_minutes", 0.0),
        queue_depth=int(summary.get("queue_depth", 0)),
        calendar_block_minutes=summary.get("calendar_block_minutes", 0.0),
    )


def replay(
    records: Sequence[HistoricalRecord],
    policy_overrides: Dict[str, float] | None = None,
    label: str = "default",
) -> EvaluationResult:
    if not records:
        raise ValueError("No records supplied for evaluation")

    attention_model = AttentionModel()
    policy = RoutingPolicy(**policy_overrides) if policy_overrides else RoutingPolicy()
    work_items = []
    human_flags: List[bool] = []
    baseline_humans = []

    for record in records:
        collector = TelemetryCollector()
        collector.record_sample(_sample_from_summary(record.telemetry))
        router = RouterService(telemetry=collector, attention_model=attention_model, policy=policy)
        router.update_operator_context(**record.context)
        work_item = router.handle_task(record.task)
        work_items.append(work_item)
        human_flags.append(work_item.route_strategy in {"immediate", "batch"})
        baseline_humans.append(record.baseline_human)

    strategy_counts: Dict[str, int] = {}
    for item in work_items:
        strategy_counts[item.route_strategy] = strategy_counts.get(item.route_strategy, 0) + 1

    avg_priority = mean(item.priority for item in work_items)
    avg_attention = mean(item.attention_load for item in work_items)
    baseline_rate = sum(baseline_humans) / len(baseline_humans)
    router_rate = sum(human_flags) / len(human_flags)

    return EvaluationResult(
        total_tasks=len(work_items),
        strategy_counts=strategy_counts,
        average_priority=avg_priority,
        average_attention_load=avg_attention,
        baseline_human_rate=baseline_rate,
        router_human_rate=router_rate,
        policy_label=label,
    )


def _format_result(result: EvaluationResult) -> str:
    data = result.as_dict()
    lines = [f"Offline Evaluation Summary (policy: {data['policy_label']})"]
    lines.append(f"Total tasks: {data['total_tasks']}")
    lines.append(f"Strategy counts: {data['strategy_counts']}")
    lines.append(f"Average priority: {data['average_priority']:.2f}")
    lines.append(f"Average attention load: {data['average_attention_load']:.2f}")
    lines.append(
        f"Baseline human rate: {data['baseline_human_rate']:.2f} | Router human rate: {data['router_human_rate']:.2f}"
    )
    lines.append(f"Human intervention reduction: {data['human_reduction_pct']:.2f}%")
    return "\n".join(lines)


def _format_grid_results(results: Sequence[EvaluationResult]) -> List[str]:
    lines = ["Offline Evaluation Sweep", "Label | Router rate | Baseline rate | Human reduction %"]
    for result in results:
        stats = result.as_dict()
        lines.append(
            f"{result.policy_label} | {result.router_human_rate:.2f} | "
            f"{result.baseline_human_rate:.2f} | {stats['human_reduction_pct']:.2f}"
        )
    return lines


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Offline evaluation for the cognitive router")
    parser.add_argument("--data", required=True, help="Path to historical incidents JSON array")
    parser.add_argument(
        "--policy",
        help="JSON string or file path with RoutingPolicy overrides (e.g. "
        "'{\"slo_weight\":0.5,\"min_confidence_for_auto\":0.9}')",
    )
    parser.add_argument(
        "--grid",
        help="Path to JSON list of objects like "
        "'[{\"label\":\"high_slo\",\"policy\":{\"slo_weight\":0.6}}]'. Overrides --policy.",
    )
    parser.add_argument("--out", help="Optional path to write JSON results")
    args = parser.parse_args(list(argv) if argv is not None else None)

    records = load_records(args.data)

    if args.grid:
        grid = _load_grid(Path(args.grid))
        results = [replay(records, cfg["policy"], cfg["label"]) for cfg in grid]
        for formatted in _format_grid_results(results):
            print(formatted)
        if args.out:
            Path(args.out).write_text(json.dumps([r.as_dict() for r in results], indent=2))
    else:
        overrides = _parse_policy_arg(args.policy) if args.policy else None
        result = replay(records, overrides)
        print(_format_result(result))
        if args.out:
            Path(args.out).write_text(json.dumps(result.as_dict(), indent=2))


if __name__ == "__main__":
    main()
