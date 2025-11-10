from cognitive_router.task_models import TaskIntent, WorkItem
from cognitive_router.workflow import InMemoryWorkflowEngine, TemporalWorkflowStub


class FakeTemporalClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def start_workflow(self, *, workflow: str, id: str, task_queue: str, input: dict) -> None:
        self.calls.append({"workflow": workflow, "id": id, "task_queue": task_queue, "input": input})


def _work_item() -> WorkItem:
    task = TaskIntent(
        task_id="w1",
        severity=3,
        slo_risk_minutes=15,
        model_confidence=0.6,
        explanation="Test",
    )
    return WorkItem(
        task_id=task.task_id,
        route_strategy="immediate",
        priority=0.8,
        attention_load=0.5,
        task=task,
        rationale="priority=0.80 slo_risk=15.0m confidence=0.60 attention_load=0.50",
    )


def test_in_memory_workflow_stores_items():
    workflow = InMemoryWorkflowEngine()
    item = _work_item()
    workflow.enqueue(item)
    assert workflow.items == [item]


def test_temporal_stub_invokes_client():
    client = FakeTemporalClient()
    stub = TemporalWorkflowStub(client=client, workflow="HumanLoop", task_queue="human_queue")
    stub.enqueue(_work_item())
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["workflow"] == "HumanLoop"
    assert call["task_queue"] == "human_queue"
    assert call["input"]["task"]["task_id"] == "w1"
