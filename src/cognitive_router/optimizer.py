"""Policy optimizer that sweeps configurations and ranks them."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from .evaluator import EvaluationResult, load_records, replay


@dataclass
class CandidateResult:
    label: str
    policy: Dict[str, float]
    evaluation: EvaluationResult
    score: float


def load_grid(path: Path) -> List[Dict[str, object]]:
    entries = json.loads(path.read_text())
    if not isinstance(entries, list):
        raise ValueError("Grid file must contain a JSON list")
    normalized = []
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict) or "policy" not in entry:
            raise ValueError("Each grid entry must include a 'policy' object")
        label = entry.get("label") or f"policy-{idx+1}"
        policy = entry["policy"]
        if not isinstance(policy, dict):
            raise ValueError("'policy' must be a JSON object")
        normalized.append({"label": label, "policy": policy})
    return normalized


def compute_score(result: EvaluationResult, objective: str) -> float:
    if objective == "human_rate":
        return result.router_human_rate
    if objective == "human_reduction":
        return -result.as_dict()["human_reduction_pct"]
    if objective == "priority":
        return -result.average_priority
    raise ValueError(f"Unknown objective '{objective}'")


def optimize(
    data_path: Path, grid_path: Path, objective: str = "human_rate", max_router_rate: float | None = None
) -> List[CandidateResult]:
    records = load_records(data_path)
    grid = load_grid(grid_path)
    results: List[CandidateResult] = []

    for entry in grid:
        label = entry["label"]
        policy = entry["policy"]
        evaluation = replay(records, policy_overrides=policy, label=str(label))
        score = compute_score(evaluation, objective)
        if max_router_rate is not None and evaluation.router_human_rate > max_router_rate:
            continue
        results.append(CandidateResult(label=str(label), policy=policy, evaluation=evaluation, score=score))

    results.sort(key=lambda c: c.score)
    return results


def _format_results(results: List[CandidateResult]) -> str:
    if not results:
        return "No candidates met the constraints."
    lines = [
        "Policy Optimization Results",
        "Rank | Label | Score | Router rate | Baseline rate | Human reduction %",
    ]
    for idx, candidate in enumerate(results, start=1):
        stats = candidate.evaluation.as_dict()
        lines.append(
            f"{idx} | {candidate.label} | {candidate.score:.3f} | "
            f"{candidate.evaluation.router_human_rate:.2f} | {candidate.evaluation.baseline_human_rate:.2f} | "
            f"{stats['human_reduction_pct']:.2f}"
        )
    best = results[0]
    lines.append("")
    lines.append("Recommended policy:")
    lines.append(json.dumps(best.policy, indent=2))
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Optimize routing policy weights using historical data")
    parser.add_argument("--data", required=True, help="Path to incidents JSON")
    parser.add_argument("--grid", required=True, help="Path to policy grid JSON")
    parser.add_argument(
        "--objective",
        default="human_rate",
        choices=["human_rate", "human_reduction", "priority"],
        help="Optimization objective",
    )
    parser.add_argument(
        "--max-router-rate",
        type=float,
        help="Optional constraint: drop candidates whose router human rate exceeds this value",
    )
    parser.add_argument("--out", help="Optional path to write JSON summary")
    args = parser.parse_args(list(argv) if argv is not None else None)

    results = optimize(Path(args.data), Path(args.grid), args.objective, args.max_router_rate)
    output = _format_results(results)
    print(output)
    if args.out and results:
        payload = [
            {
                "label": candidate.label,
                "policy": candidate.policy,
                **candidate.evaluation.as_dict(),
                "score": candidate.score,
            }
            for candidate in results
        ]
        Path(args.out).write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
