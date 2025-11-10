"""Core package for the cognitive bandwidth router prototype."""

from .telemetry import TelemetrySample, TelemetryCollector
from .attention import AttentionModel
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

__all__ = [
    "TelemetrySample",
    "TelemetryCollector",
    "AttentionModel",
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
