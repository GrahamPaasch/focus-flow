"""Cognitive Bandwidth Router: Intelligent task routing for human-in-the-loop AI systems.

This package provides components for routing AI agent decisions based on both task
urgency (SLO risk, severity, confidence) and human availability (telemetry, queue depth,
calendar load). It helps prevent alert fatigue by respecting finite human attention.

Key components:
- TelemetryCollector: Track operator activity patterns and idle time
- AttentionModel: Estimate cognitive load from telemetry + context signals
- RoutingPolicy: Compute priority and route to immediate/batch/auto/park strategies
- RouterService: Orchestrate telemetry, attention scoring, and routing decisions
- EventBus: Pluggable event transport (in-memory or Kafka)
- WorkflowEngine: Integration with workflow systems (in-memory or Temporal)
"""

from .telemetry import TelemetrySample, TelemetryCollector
from .attention import AttentionModel, AttentionConfig
from .context import (
    CalendarLoadContextProvider,
    CallableContextProvider,
    CompositeContextProvider,
    ContextProvider,
    QueueDepthContextProvider,
    StaticContextProvider,
)
from .task_models import TaskIntent, WorkItem
from .router import RoutingPolicy, RouterService
from .event_bus import EventBus, InMemoryEventBus, KafkaEventBus
from .workflow import InMemoryWorkflowEngine, WorkflowEngine, TemporalWorkflowStub

__version__ = "0.1.0"

__all__ = [
    "TelemetrySample",
    "TelemetryCollector",
    "AttentionModel",
    "AttentionConfig",
    "CalendarLoadContextProvider",
    "CallableContextProvider",
    "CompositeContextProvider",
    "ContextProvider",
    "QueueDepthContextProvider",
    "StaticContextProvider",
    "TaskIntent",
    "WorkItem",
    "RoutingPolicy",
    "RouterService",
    "EventBus",
    "InMemoryEventBus",
    "KafkaEventBus",
    "WorkflowEngine",
    "InMemoryWorkflowEngine",
    "TemporalWorkflowStub",
]
