# Cognitive Bandwidth Router Prototype

This prototype turns the research brief into runnable scaffolding. It focuses on:

1. Capturing lightweight telemetry (keystrokes, pager events, queue depth, calendar blocks) and summarizing operator load.
2. Translating agent `TaskIntent` events into routed `WorkItem`s through a tunable policy + workflow sink.
3. Offering configurable context providers and event buses so you can evolve from the in-memory sim to Kafka/Temporal wiring.

## Package layout

```
src/cognitive_router/
  attention.py        # Load/attention model with configurable weights
  telemetry.py        # Rolling telemetry collector and summary logic
  context.py          # Queue/calendar/context providers (composite-friendly)
  task_models.py      # Dataclasses for agent intents and work items
  router.py           # Routing policy + service with sinks + providers
  event_bus.py        # In-memory + Kafka-style pub/sub implementations
  workflow.py         # In-memory queue + Temporal workflow stub
  simulation.py       # CLI entrypoint wiring bus → router → workflow
```

Key ideas:
- `TelemetryCollector` keeps a time-windowed deque of interaction samples (keystrokes, pager events, queue depth, calendar block minutes) and emits normalized aggregates.
- `AttentionModel` converts telemetry + provider context (queue depth, calendar load, context switches) into a scalar load score in `[0,1]`.
- `ContextProvider`s let you inject new availability signals (static, callable, queue-aware, calendar-aware) without touching router internals.
- `RoutingPolicy` mixes SLO risk, model uncertainty, severity, and attention load, producing four strategies: `immediate`, `batch`, `auto`, `park`.
- `EventBus` exposes both in-memory and Kafka-style transports; the Kafka variant accepts real producers/consumers and a `poll_once` helper.
- `WorkflowEngine` includes an in-memory queue and a Temporal stub so routed work can join long-running HITL workflows while feeding queue depth back into attention scoring.

## Usage

### Run the simulation

```
python -m cognitive_router.simulation --tasks 6 --seed 13
# or, after installing the package:
cog-router-sim --tasks 6 --seed 13
```

Sample output:

```
[IMMEDIATE] task-1 -> priority=0.73 slo_risk=24.6m confidence=0.54 attention_load=0.37 queue=1
[PARK] task-2 -> priority=0.30 slo_risk=7.9m confidence=0.78 attention_load=0.36 queue=1
[IMMEDIATE] task-3 -> priority=0.78 slo_risk=42.3m confidence=0.43 attention_load=0.38 queue=2
```

### Run tests

```
pytest -q
```

Tests cover:
- Attention scores rising with higher load.
- Routing outcomes (immediate/auto/batch) plus context-provider effects.
- Kafka-style event bus, workflow adapters, and context provider utilities.
- Offline evaluator JSON parsing and metric calculations.

### Offline policy evaluation

1. Capture or author historical incidents in JSON (example: `samples/incidents.json`). Each entry includes telemetry/context summaries, a `task`, and optional `baseline.human_intervention`.
2. Run the evaluator (single policy or sweeps):

```
python -m cognitive_router.evaluator --data samples/incidents.json
# override policy weights inline or via file
cog-router-eval --data samples/incidents.json --policy '{"slo_weight":0.5,"batch_threshold":0.4}'
# sweep multiple configs
cog-router-eval --data samples/incidents.json --grid samples/policy_grid.json --out sweep.json
```

Sample output:

```
Offline Evaluation Summary
Total tasks: 5
Strategy counts: {'batch': 2, 'immediate': 1, 'auto': 2}
Average priority: 0.53
Average attention load: 0.52
Baseline human rate: 0.60 | Router human rate: 0.60
Human intervention reduction: 0.00%
```

Sweep output rolls up each label:

```
Offline Evaluation Sweep
Label | Router rate | Baseline rate | Human reduction %
baseline | 0.60 | 0.60 | 0.00
high_slo_bias | 0.80 | 0.60 | -33.33
uncertainty_first | 0.60 | 0.60 | 0.00
```

## Next steps

1. **Swap the in-memory wiring for production infra**: connect `KafkaEventBus` to a real producer/consumer pair and point `TemporalWorkflowStub` (or an Airflow HITL operator) at your orchestration stack.
2. **Add richer context providers** via wearable feeds, calendar APIs, or scheduling systems so attention scores reflect availability windows and PTO.
3. **Offline policy evaluation** using historical incident/queue traces to measure MTTA/MTTR/alert volume deltas before tuning weights.
4. **Dashboard prototype** that consumes `WorkItem`s, shows SLA countdowns + queue depth, and captures operator overrides/feedback.
5. **Governance hooks** (consent prompts, data retention, on-device processing) so higher-intrusion sensors can be deployed responsibly.
