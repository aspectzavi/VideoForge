"""
VideoForge Event Dispatcher

A lightweight synchronous event bus.

Responsibilities
----------------
- Register listeners
- Remove listeners
- Emit events
- Support wildcard listeners

Does NOT:
- Log
- Store history
- Perform async execution
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from contextlib import suppress
from typing import Any

EventHandler = Callable[[Any], None]


class EventDispatcher:
    """
    Simple synchronous event dispatcher.
    """

    def __init__(self) -> None:

        self._listeners: dict[type, list[EventHandler]] = defaultdict(list)

        self._wildcard: list[EventHandler] = []

    # ---------------------------------------------------------

    def subscribe(
        self,
        event_type: type,
        handler: EventHandler,
    ) -> EventHandler:
        """
        Register a handler for an event class.

        Example
        -------
        dispatcher.subscribe(
            ProgressEvent,
            print_progress,
        )
        """

        if handler not in self._listeners[event_type]:
            self._listeners[event_type].append(handler)

        return handler

    # ---------------------------------------------------------

    def unsubscribe(
        self,
        event_type: type,
        handler: EventHandler,
    ) -> None:
        """
        Remove a handler.
        """

        listeners = self._listeners.get(event_type)

        if not listeners:
            return

        with suppress(ValueError):
            listeners.remove(handler)

    # ---------------------------------------------------------

    def subscribe_all(
        self,
        handler: EventHandler,
    ) -> EventHandler:
        """
        Subscribe to every event.
        """

        if handler not in self._wildcard:
            self._wildcard.append(handler)

        return handler

    # ---------------------------------------------------------

    def unsubscribe_all(
        self,
        handler: EventHandler,
    ) -> None:

        with suppress(ValueError):
            self._wildcard.remove(handler)

    # ---------------------------------------------------------

    def emit(
        self,
        event: Any,
    ) -> None:
        """
        Emit an event.
        """

        event_type = type(event)

        # Exact listeners

        for handler in tuple(self._listeners.get(event_type, [])):
            handler(event)

        # Wildcard listeners

        for handler in tuple(self._wildcard):
            handler(event)

    # ---------------------------------------------------------

    def clear(self) -> None:
        """
        Remove every listener.
        """

        self._listeners.clear()
        self._wildcard.clear()

    # ---------------------------------------------------------

    def listeners(
        self,
        event_type: type | None = None,
    ) -> Iterable[EventHandler]:
        """
        Return registered listeners.
        """

        if event_type is None:
            return tuple(self._wildcard)

        return tuple(self._listeners.get(event_type, []))

    # ---------------------------------------------------------

    def has_listeners(
        self,
        event_type: type,
    ) -> bool:

        return bool(self._listeners.get(event_type)) or bool(self._wildcard)


# Singleton dispatcher used by the application.

dispatcher = EventDispatcher()
