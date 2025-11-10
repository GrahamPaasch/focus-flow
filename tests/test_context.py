from cognitive_router.context import (
    CompositeContextProvider,
    QueueDepthContextProvider,
    StaticContextProvider,
)


def test_queue_depth_provider_reports_length():
    provider = QueueDepthContextProvider(lambda: 7)
    snapshot = provider.snapshot()
    assert snapshot["queue_depth"] == 7.0


def test_composite_provider_merges_values():
    composite = CompositeContextProvider([StaticContextProvider({"context_switches_last_hour": 2})])
    composite.add(QueueDepthContextProvider(lambda: 4))
    snapshot = composite.snapshot()
    assert snapshot["context_switches_last_hour"] == 2
    assert snapshot["queue_depth"] == 4.0
