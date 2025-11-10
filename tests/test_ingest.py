import csv
import json
from pathlib import Path

from cognitive_router.ingest import ColumnMapping, convert_csv_to_json, load_mapping, transform_row


def test_load_mapping_defaults(tmp_path: Path):
    mapping = load_mapping(None)
    assert mapping.record_id == "record_id"
    config_path = tmp_path / "mapping.json"
    config_path.write_text(json.dumps({"record_id": "id", "telemetry": {"pager_events": "pager"}}))
    mapping = load_mapping(config_path)
    assert mapping.record_id == "id"
    assert mapping.telemetry["pager_events"] == "pager"


def test_transform_row_builds_record():
    mapping = ColumnMapping()
    row = {
        "record_id": "abc",
        "severity": "4",
        "slo_risk_minutes": "20",
        "model_confidence": "0.7",
        "keystrokes_per_min": "150",
        "context_switches_last_hour": "3",
        "baseline_human": "true",
    }
    record = transform_row(row, mapping)
    assert record["id"] == "abc"
    assert record["task"]["severity"] == 4
    assert record["baseline"]["human_intervention"] is True
    assert record["telemetry"]["keystrokes_per_min"] == 150.0


def test_convert_csv_to_json(tmp_path: Path):
    csv_path = tmp_path / "incidents.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "record_id",
                "severity",
                "slo_risk_minutes",
                "model_confidence",
                "keystrokes_per_min",
                "context_switches_last_hour",
                "baseline_human",
            ]
        )
        writer.writerow(["abc", "4", "20", "0.7", "150", "3", "true"])

    records = convert_csv_to_json(csv_path, ColumnMapping())
    assert len(records) == 1
    assert records[0]["task"]["task_id"] == "abc"
