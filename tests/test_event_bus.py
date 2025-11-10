from collections import deque

from cognitive_router.event_bus import KafkaEventBus


class FakeMessage:
    def __init__(self, topic: str, value: bytes):
        self._topic = topic
        self._value = value

    def topic(self) -> str:
        return self._topic

    def value(self) -> bytes:
        return self._value

    def error(self):
        return None


class FakeConsumer:
    def __init__(self) -> None:
        self._topics: list[str] = []
        self._queue: deque[FakeMessage] = deque()

    def subscribe(self, topics: list[str]) -> None:
        self._topics = topics

    def enqueue(self, topic: str, value: bytes) -> None:
        self._queue.append(FakeMessage(topic, value))

    def poll(self, timeout: float):
        if self._queue:
            return self._queue.popleft()
        return None


class FakeProducer:
    def __init__(self, consumer: FakeConsumer) -> None:
        self.consumer = consumer

    def produce(self, topic: str, value: bytes) -> None:
        self.consumer.enqueue(topic, value)

    def flush(self, timeout: float | None = None) -> None:
        return None


def test_kafka_event_bus_round_trip():
    consumer = FakeConsumer()
    producer = FakeProducer(consumer)
    bus = KafkaEventBus(producer=producer, consumer=consumer)
    received: list[dict] = []

    bus.subscribe("tasks.intent", lambda payload: received.append(payload))
    bus.publish("tasks.intent", {"foo": "bar"})
    bus.poll_once()

    assert received == [{"foo": "bar"}]
