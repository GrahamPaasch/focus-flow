"""Workflow integrations for routed work items."""

from __future__ import annotations

from dataclasses import asdict
from typing import List, Protocol
from uuid import uuid4

from .task_models import WorkItem


class WorkflowEngine(Protocol):
    """Protocol for systems that accept routed work items."""

    def enqueue(self, work_item: WorkItem) -> None:
        ...


class InMemoryWorkflowEngine:
    """Simple queue for tests/simulations."""

    def __init__(self) -> None:
        self.items: List[WorkItem] = []

    def enqueue(self, work_item: WorkItem) -> None:
        self.items.append(work_item)


class TemporalClientProtocol(Protocol):
    def start_workflow(self, *, workflow: str, id: str, task_queue: str, input: dict) -> None:
        ...


class TemporalWorkflowStub:
    """Adapter that pushes work items into a Temporal workflow."""

    def __init__(
        self,
        client: TemporalClientProtocol,
        workflow: str = "HumanReviewWorkflow",
        task_queue: str = "human_review",
        id_prefix: str = "router",
    ) -> None:
        self.client = client
        self.workflow = workflow
        self.task_queue = task_queue
        self.id_prefix = id_prefix

    def enqueue(self, work_item: WorkItem) -> None:
        payload = {
            "task": asdict(work_item.task),
            "route_strategy": work_item.route_strategy,
            "priority": work_item.priority,
            "attention_load": work_item.attention_load,
            "rationale": work_item.rationale,
        }
        workflow_id = f"{self.id_prefix}-{work_item.task.task_id}-{uuid4().hex[:8]}"
        self.client.start_workflow(
            workflow=self.workflow,
            id=workflow_id,
            task_queue=self.task_queue,
            input=payload,
        )


__all__ = ["InMemoryWorkflowEngine", "TemporalWorkflowStub", "TemporalClientProtocol", "WorkflowEngine"]
