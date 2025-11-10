# Cognitive Bandwidth Router Prototype

This prototype turns the research brief into runnable scaffolding. It focuses on:

1. Capturing lightweight telemetry and summarizing operator load.
2. Translating agent `TaskIntent` events into routed `WorkItem`s using a tunable policy.
3. Providing a CLI simulation plus pytest coverage so policies can be iterated safely.

## Package layout

```
src/cognitive_router/
  attention.py        # Load/attention model with configurable weights
  telemetry.py        # Rolling telemetry collector and summary logic
  task_models.py      # Dataclasses for agent intents and work items
  router.py           # Routing policy + service with pluggable sinks
  event_bus.py        # Simple pub/sub (not wired yet, ready for Kafka/Temporal swap)
  simulation.py       # CLI entrypoint to exercise the flow end-to-end
```

Key ideas:
- `TelemetryCollector` keeps a time-windowed deque of interaction samples (keystrokes, pager events, idle minutes). It outputs normalized aggregates for downstream models.
- `AttentionModel` converts telemetry + context (e.g., context switches/hour) into a scalar load score in `[0,1]` representing how taxed the operator currently is.
- `RoutingPolicy` mixes SLO risk, model uncertainty, severity, and attention load. Thresholds define four strategies: `immediate`, `batch`, `auto`, `park`.
- `RouterService` glues the above pieces, emits `WorkItem`s, and notifies any registered sinks (dashboards, workflow engines, etc.).

## Usage

### Run the simulation

```
python -m cognitive_router.simulation --tasks 6 --seed 13
```

Sample output:

```
[IMMEDIATE] task-1 -> priority=0.79 slo_risk=43.2m confidence=0.58 attention_load=0.35
[BATCH] task-2 -> priority=0.53 slo_risk=21.1m confidence=0.44 attention_load=0.35
[AUTO] task-3 -> priority=0.32 slo_risk=8.4m confidence=0.93 attention_load=0.35
```

### Run tests

```
pytest -q
```

Tests cover:
- Attention scores rising with higher load.
- Routing outcomes for immediate, auto, and batch scenarios.

## Next steps

1. **Wire a real event bus + workflow engine** (Kafka → Temporal/Airflow) using the `EventBus` abstraction as a seam.
2. **Expand telemetry ingestion** (calendar, queue depth, wearable hooks) by extending `TelemetrySample`/`Collector` without breaking callers.
3. **Offline policy evaluation** via historical incident/queue replays—drop JSON traces into tests to compare MTTA/MTTR deltas.
4. **Dashboard prototype** that consumes `WorkItem`s and exposes the rationale metadata plus override controls.
5. **Governance hooks** for consent/privacy so higher-intrusion sensors can be toggled per site policy.
