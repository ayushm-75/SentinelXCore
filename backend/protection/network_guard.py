# Suspicious domain alerting
# backend/protection/network_guard.py
"""Network-level protection — listens for blocked domain events and alerts."""
import asyncio
import time
from collections import defaultdict
from backend.core.logger import get_logger
from backend.core.event_bus import bus
from backend.core.state import state

log = get_logger("net_guard")


class NetworkGuard:

    def __init__(self):
        self._blocked_summary: dict = defaultdict(int)
        self._last_report = time.time()

    async def on_blocked(self, event: dict) -> None:
        domain = event.get("data", {}).get("domain", "")
        if domain:
            self._blocked_summary[domain] += 1
            state.blocked_count += 1

        # Periodic summary log
        now = time.time()
        if now - self._last_report > 60:
            top = sorted(self._blocked_summary.items(), key=lambda x: x[1], reverse=True)[:5]
            if top:
                log.info(f"Top blocked domains (last 60s): {top}")
            self._blocked_summary.clear()
            self._last_report = now