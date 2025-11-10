"""Context providers exposing operator availability signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Protocol


class ContextProvider(Protocol):
    """Protocol for pluggable operator context sources."""

    def snapshot(self) -> Dict[str, float]:
        """Return the latest context values."""


@dataclass
class StaticContextProvider:
    """Returns a fixed set of context values."""

    data: Dict[str, float]

    def snapshot(self) -> Dict[str, float]:
        return dict(self.data)


@dataclass
class CallableContextProvider:
    """Wraps a callable that returns a context dictionary."""

    producer: Callable[[], Dict[str, float]]

    def snapshot(self) -> Dict[str, float]:
        data = self.producer()
        if not isinstance(data, dict):
            raise ValueError("Context producer must return a dict[str, float].")
        return data


@dataclass
class QueueDepthContextProvider:
    """Reports the current queue depth to guide attention scoring."""

    queue_length_fn: Callable[[], int]

    def snapshot(self) -> Dict[str, float]:
        return {"queue_depth": float(self.queue_length_fn())}


@dataclass
class CalendarLoadContextProvider:
    """Reports minutes blocked on the calendar in the next hour."""

    busy_minutes_fn: Callable[[], float]

    def snapshot(self) -> Dict[str, float]:
        minutes = self.busy_minutes_fn()
        return {"calendar_block_minutes": float(max(0.0, minutes))}


class CompositeContextProvider:
    """Aggregates multiple providers into a merged dictionary."""

    def __init__(self, providers: Iterable[ContextProvider] | None = None) -> None:
        self._providers: List[ContextProvider] = list(providers or [])

    def add(self, provider: ContextProvider) -> None:
        self._providers.append(provider)

    def snapshot(self) -> Dict[str, float]:
        context: Dict[str, float] = {}
        for provider in self._providers:
            context.update(provider.snapshot())
        return context


__all__ = [
    "CalendarLoadContextProvider",
    "CallableContextProvider",
    "CompositeContextProvider",
    "ContextProvider",
    "QueueDepthContextProvider",
    "StaticContextProvider",
]
