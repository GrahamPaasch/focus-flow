"""Minimal in-memory pub/sub bus for simulations."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, List

Handler = Callable[[Any], None]


class EventBus:
    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, event: Any) -> None:
        for handler in list(self._subscribers.get(topic, [])):
            handler(event)
