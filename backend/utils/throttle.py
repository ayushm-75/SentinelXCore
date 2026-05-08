# backend/utils/throttle.py
"""
Simple async rate limiter / throttle utilities.
Used to prevent alert storms and sensor overload.
"""
import asyncio
import time
from collections import defaultdict
from typing import Dict


class TokenBucket:
    """
    Token bucket rate limiter.
    Allows `rate` operations per second with a burst of `capacity`.
    """
    def __init__(self, rate: float, capacity: float):
        self._rate     = rate
        self._capacity = capacity
        self._tokens   = capacity
        self._last     = time.monotonic()

    def consume(self, tokens: float = 1.0) -> bool:
        """Try to consume tokens. Returns True if allowed."""
        now    = time.monotonic()
        delta  = now - self._last
        self._last = now
        self._tokens = min(self._capacity, self._tokens + delta * self._rate)
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False


class RateLimiter:
    """
    Per-key rate limiter.
    Example: limit alerts per rule_id, limit scans per file path.
    """
    def __init__(self, rate: float = 1.0, capacity: float = 5.0):
        self._rate     = rate
        self._capacity = capacity
        self._buckets: Dict[str, TokenBucket] = {}

    def is_allowed(self, key: str) -> bool:
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(self._rate, self._capacity)
        return self._buckets[key].consume()

    def cleanup(self) -> None:
        """Remove stale buckets (call periodically)."""
        # Simple cleanup — remove if not accessed recently
        # In production you'd track last-access time
        if len(self._buckets) > 10000:
            self._buckets.clear()


class Debouncer:
    """
    Debounce async calls — only execute after N seconds of silence.
    Useful for file change events.
    """
    def __init__(self, delay: float = 1.0):
        self._delay   = delay
        self._tasks: Dict[str, asyncio.Task] = {}

    async def call(self, key: str, coro_fn, *args) -> None:
        # Cancel previous pending call for this key
        if key in self._tasks:
            self._tasks[key].cancel()
            try:
                await self._tasks[key]
            except asyncio.CancelledError:
                pass

        async def _delayed():
            await asyncio.sleep(self._delay)
            await coro_fn(*args)

        self._tasks[key] = asyncio.create_task(_delayed())


# ── Module-level shared limiters ─────────────────────────────
alert_limiter   = RateLimiter(rate=1.0, capacity=3.0)   # 3 alerts/key burst, 1/sec sustained
scan_limiter    = RateLimiter(rate=2.0, capacity=10.0)  # file scan rate
network_limiter = RateLimiter(rate=10.0, capacity=50.0) # network event rate