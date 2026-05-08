# Async pub/sub event bus
# backend/core/event_bus.py
"""
Async pub/sub event bus — zero external dependencies.
Modules publish events; WebSocket handler subscribes and forwards to UI.
"""
import asyncio
from collections import defaultdict
from typing import Callable, Any, Dict, List
from backend.core.logger import get_logger

log = get_logger("event_bus")


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=2000)
        self._running = False

    def subscribe(self, event_type: str, callback: Callable) -> None:
        self._subscribers[event_type].append(callback)

    def subscribe_all(self, callback: Callable) -> None:
        """Subscribe to every event type."""
        self.subscribe("*", callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: str, data: Any = None) -> None:
        """Non-blocking publish — drops if queue full to avoid memory bloat."""
        event = {"type": event_type, "data": data}
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            pass  # Drop oldest — we never block the sensor

    async def dispatch_loop(self) -> None:
        """Main dispatch coroutine — run as background task."""
        self._running = True
        log.info("Event bus dispatch loop started")
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch(event)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                log.error(f"Dispatch error: {e}")

    async def _dispatch(self, event: dict) -> None:
        event_type = event["type"]
        handlers = (
            self._subscribers.get(event_type, []) +
            self._subscribers.get("*", [])
        )
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                log.error(f"Handler error for {event_type}: {e}")

    def stop(self) -> None:
        self._running = False


# Global singleton
bus = EventBus()