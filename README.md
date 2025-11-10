# Cognitive Bandwidth Router

**Intelligent task routing for human-in-the-loop AI systems**

## The Problem

AI agents increasingly make autonomous decisions—auto-resolving incidents, handling support tickets, enforcing compliance policies. But they can't handle everything: edge cases require human judgment, low-confidence predictions need verification, and critical situations demand expert oversight.

The traditional approach is binary: either the AI does it alone, or it always escalates to a human. This creates two problems:

1. **Alert fatigue**: Humans get interrupted constantly, even when they're overloaded or the task could wait
2. **Missed urgency**: Important decisions get queued alongside trivial ones because the system doesn't understand operator availability

**Human attention is finite.** When you're on-call with 4 active incidents, in back-to-back meetings, and context-switching every 10 minutes, you can't handle the same workload as when you're fresh at 9am with an empty queue.

## The Solution

This system routes AI agent decisions based on **task urgency AND human availability**:

- **Immediate**: Critical tasks that need attention right now (SLO breach + low AI confidence)
- **Batch**: Medium-priority items queued for your next review window  
- **Auto**: High-confidence, low-severity tasks the AI handles autonomously
- **Park**: Defer entirely when you're overloaded and the task isn't urgent

Routing decisions combine:
- Task metadata (SLO risk, severity, AI confidence)
- Lightweight telemetry (activity patterns, idle time, pager events)
- Context signals (queue depth, calendar blocks, context switches)

The result: AI agents respect your cognitive bandwidth instead of treating you like an infinitely-available approval button.

## Architecture

The `cognitive_router` package provides a runnable prototype for integrating intelligent routing into HITL workflows. See `docs/cognitive_bandwidth_router.md` for the full architecture, simulation instructions, and production deployment guidance.

## Quick Start

### Installation

```bash
pip install -e .
```

### Try It Now (No Setup Required)

Test with simulated data:

```bash
# Generate random tasks and see routing decisions
cog-router-sim --tasks 10 --seed 42

# Run live integration demo with webhook examples
python live_integration_example.py
```

### Connect Real Data Sources

See **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** for:
- Webhook server setup (Datadog, PagerDuty, Prometheus)
- Real telemetry collection (system activity, calendar, queue depth)
- Production deployment options

Quick webhook server start:
```bash
pip install flask
python webhook_server.py  # Starts server on http://localhost:5000
```

### Run a simulation

Generate random AI agent tasks and see how they get routed based on simulated operator load:

```bash
cog-router-sim --tasks 10 --seed 42
```

Example output:
```
[IMMEDIATE] task-1 -> priority=0.78 slo_risk=42.3m confidence=0.43 attention_load=0.38 queue=2
[PARK] task-2 -> priority=0.30 slo_risk=7.9m confidence=0.78 attention_load=0.36 queue=1
[AUTO] task-3 -> priority=0.22 slo_risk=5.2m confidence=0.92 attention_load=0.35 queue=1
[BATCH] task-4 -> priority=0.56 slo_risk=18.5m confidence=0.65 attention_load=0.41 queue=3
```

### Evaluate policies on historical data

Test different routing policies against past incidents to measure human intervention rates:

```bash
cog-router-eval --data samples/incidents.json
```

Optimize policy weights using grid search:

```bash
cog-router-opt --data samples/incidents.json --grid samples/policy_grid.json --objective human_rate
```

### Run tests

```bash
pytest
```

## Use Cases

- **Incident response**: Route AI-triaged alerts to on-call engineers only when confidence is low or SLOs are at risk
- **Support automation**: Escalate AI chatbot conversations to humans based on urgency and current queue depth
- **Compliance review**: Batch policy decisions for review during scheduled windows instead of interrupting constantly
- **Content moderation**: Surface high-severity or ambiguous cases immediately while queuing routine decisions

## How It Works

1. **Telemetry Collection**: Lightweight tracking of operator activity (keystrokes, idle time, pager events)
2. **Attention Modeling**: Combine telemetry with context signals (queue depth, calendar, context switches) into a load score
3. **Routing Policy**: Weight task urgency (SLO risk, severity) against AI confidence and operator availability
4. **Workflow Integration**: Route decisions to immediate/batch/auto/park queues with pluggable sinks (Kafka, Temporal, etc.)

## Configuration

Tune routing behavior via policy weights:

```python
from cognitive_router.router import RoutingPolicy

policy = RoutingPolicy(
    slo_weight=0.4,              # How much SLO risk matters
    uncertainty_weight=0.25,      # How much AI confidence matters
    severity_weight=0.25,         # How much task severity matters
    attention_weight=0.1,         # How much operator load matters
    immediate_threshold=0.75,     # Priority cutoff for immediate routing
    batch_threshold=0.45,         # Priority cutoff for batch routing
    min_confidence_for_auto=0.85  # AI confidence needed for auto-resolution
)
```

## Next Steps

See `docs/cognitive_bandwidth_router.md` for:
- Detailed architecture and module descriptions
- Production deployment guidance (Kafka, Temporal)
- CSV import for historical incident data
- Policy optimization workflows
- Governance and privacy considerations
