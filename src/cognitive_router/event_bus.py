"""Event bus abstractions for in-memory and Kafka-style transports."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from threading import Lock
from typing import Any, Callable, DefaultDict, Dict, List, Protocol

Handler = Callable[[Any], None]
Serializer = Callable[[Any], bytes]
Deserializer = Callable[[bytes], Any]


class EventBus(ABC):
    """Abstract base class for pub/sub implementations."""

    @abstractmethod
    def subscribe(self, topic: str, handler: Handler) -> None:
        ...

    @abstractmethod
    def publish(self, topic: str, event: Any) -> None:
        ...


class InMemoryEventBus(EventBus):
    """Process-local bus used for simulations or tests."""

    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, event: Any) -> None:
        for handler in list(self._subscribers.get(topic, [])):
            handler(event)


class KafkaProducerProtocol(Protocol):
    def produce(self, topic: str, value: bytes) -> None:
        ...

    def flush(self, timeout: float | None = None) -> None:
        ...


class KafkaConsumerProtocol(Protocol):
    def subscribe(self, topics: List[str]) -> None:
        ...

    def poll(self, timeout: float) -> "KafkaMessageProtocol | None":
        ...


class KafkaMessageProtocol(Protocol):
    def topic(self) -> str:
        ...

    def value(self) -> bytes:
        ...

    def error(self) -> Any:
        ...


def _json_serializer(event: Any) -> bytes:
    if hasattr(event, "model_dump"):
        payload = event.model_dump()
    elif is_dataclass(event):
        payload = asdict(event)
    elif hasattr(event, "__dict__"):
        payload = event.__dict__
    else:
        payload = event
    return json.dumps(payload, default=str).encode("utf-8")


def _json_deserializer(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"))


class KafkaEventBus(EventBus):
    """Thin wrapper around Kafka producers/consumers with simple polling."""

    def __init__(
        self,
        producer: KafkaProducerProtocol,
        consumer: KafkaConsumerProtocol,
        serializer: Serializer | None = None,
        deserializer: Deserializer | None = None,
    ) -> None:
        self._producer = producer
        self._consumer = consumer
        self._serializer = serializer or _json_serializer
        self._deserializer = deserializer or _json_deserializer
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)
        self._lock = Lock()

    def subscribe(self, topic: str, handler: Handler) -> None:
        with self._lock:
            self._handlers.setdefault(topic, []).append(handler)
            self._consumer.subscribe(list(self._handlers.keys()))

    def publish(self, topic: str, event: Any) -> None:
        payload = self._serializer(event)
        self._producer.produce(topic, payload)
        # Flush with zero timeout to avoid blocking but still pump delivery queues.
        self._producer.flush(0)

    def poll_once(self, timeout: float = 0.5) -> None:
        """Poll the consumer once and dispatch messages to handlers."""
        message = self._consumer.poll(timeout)
        if message is None:
            return
        if hasattr(message, "error") and message.error():
            return
        handlers = list(self._handlers.get(message.topic(), []))
        if not handlers:
            return
        payload = self._deserializer(message.value())
        for handler in handlers:
            handler(payload)


__all__ = [
    "Deserializer",
    "EventBus",
    "InMemoryEventBus",
    "KafkaConsumerProtocol",
    "KafkaEventBus",
    "KafkaMessageProtocol",
    "KafkaProducerProtocol",
    "Serializer",
]
