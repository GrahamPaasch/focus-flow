"""Utilities for importing real incidents/queues into evaluator-ready JSON."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


@dataclass
class ColumnMapping:
    record_id: str = "record_id"
    severity: str = "severity"
    slo_risk_minutes: str = "slo_risk_minutes"
    model_confidence: str = "model_confidence"
    explanation: str = "explanation"
    sensitivity_tag: str = "sensitivity_tag"
    telemetry: Dict[str, str] = field(
        default_factory=lambda: {
            "keystrokes_per_min": "keystrokes_per_min",
            "mouse_moves_per_min": "mouse_moves_per_min",
            "window_focus_changes": "window_focus_changes",
            "pager_events": "pager_events",
            "active_tasks": "active_tasks",
            "idle_minutes": "idle_minutes",
            "queue_depth": "queue_depth",
            "calendar_block_minutes": "calendar_block_minutes",
        }
    )
    context_switches: str = "context_switches_last_hour"
    baseline_flag: str = "baseline_human"
    baseline_response_minutes: str = "response_minutes"


def load_mapping(path: str | Path | None) -> ColumnMapping:
    if not path:
        return ColumnMapping()
    text = Path(path).read_text()
    data = json.loads(text)
    telemetry = data.get("telemetry", {})
    mapping = ColumnMapping(
        record_id=data.get("record_id", "record_id"),
        severity=data.get("severity", "severity"),
        slo_risk_minutes=data.get("slo_risk_minutes", "slo_risk_minutes"),
        model_confidence=data.get("model_confidence", "model_confidence"),
        explanation=data.get("explanation", "explanation"),
        sensitivity_tag=data.get("sensitivity_tag", "sensitivity_tag"),
        telemetry={**ColumnMapping().telemetry, **telemetry},
        context_switches=data.get("context_switches", "context_switches_last_hour"),
        baseline_flag=data.get("baseline_flag", "baseline_human"),
        baseline_response_minutes=data.get("baseline_response_minutes", "response_minutes"),
    )
    return mapping


def parse_bool(value: str | None) -> bool:
    if value is None:
        return False
    value = value.strip().lower()
    return value in {"1", "true", "yes", "y"}


def transform_row(row: Dict[str, str], mapping: ColumnMapping) -> Dict[str, object]:
    telemetry = {}
    for key, column in mapping.telemetry.items():
        telemetry[key] = float(row.get(column, 0) or 0)

    context = {
        "context_switches_last_hour": float(row.get(mapping.context_switches, 0) or 0),
    }

    baseline = {
        "human_intervention": parse_bool(row.get(mapping.baseline_flag)),
        "response_minutes": float(row.get(mapping.baseline_response_minutes, 0) or 0),
    }

    task = {
        "task_id": row.get(mapping.record_id, "record"),
        "severity": int(row.get(mapping.severity, 0) or 0),
        "slo_risk_minutes": float(row.get(mapping.slo_risk_minutes, 0) or 0),
        "model_confidence": float(row.get(mapping.model_confidence, 0) or 0),
        "explanation": row.get(mapping.explanation, "") or "",
        "sensitivity_tag": row.get(mapping.sensitivity_tag, "standard") or "standard",
    }

    return {
        "id": row.get(mapping.record_id, "record"),
        "telemetry": telemetry,
        "context": context,
        "task": task,
        "baseline": baseline,
    }


def convert_csv_to_json(csv_path: str | Path, mapping: ColumnMapping) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            records.append(transform_row(row, mapping))
    return records


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Convert incident CSV exports into evaluator JSON")
    parser.add_argument("--csv", required=True, help="Path to CSV export")
    parser.add_argument("--out", required=True, help="Destination JSON file")
    parser.add_argument(
        "--mapping",
        help="Optional JSON file describing column mappings. Defaults assume headers like "
        "'severity', 'keystrokes_per_min', 'baseline_human', etc.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    mapping = load_mapping(args.mapping)
    records = convert_csv_to_json(args.csv, mapping)
    Path(args.out).write_text(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()

