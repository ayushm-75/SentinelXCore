# backend/protection/alert_manager.py
import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path
from backend.core.logger import get_logger
from backend.core.state import state, AlertEntry
from backend.utils.helpers import generate_alert_id
from backend.utils.constants import SEV_HIGH

log = get_logger("alert_mgr")
ALERTS_LOG_PATH = Path("logs/alerts.json")

# How many blocks before we show ONE summary alert
BLOCK_SUMMARY_THRESHOLD = 20
BLOCK_SUMMARY_INTERVAL  = 60.0   # seconds


class AlertManager:

    def __init__(self):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        # Block domain counter for summary alerts
        self._blocked_domains: dict = defaultdict(int)
        self._last_block_summary    = time.time()

    def on_event(self, event: dict) -> None:
        event_type = event.get("type", "")
        alert_events = {"file.threat", "process.suspicious"}

        # network.blocked goes through summary logic, not individual alerts
        if event_type in alert_events:
            try:
                self._queue.put_nowait(event)
            except asyncio.QueueFull:
                pass
        elif event_type == "network.blocked":
            # Count silently — summary alert every N blocks
            domain = (event.get("data") or {}).get("domain", "")
            if domain:
                self._blocked_domains[domain] += 1

    async def run(self) -> None:
        log.info("Alert manager started.")
        while True:
            try:
                # Process queued alerts
                try:
                    event = await asyncio.wait_for(self._queue.get(), timeout=5.0)
                    await self._handle_event(event)
                    self._queue.task_done()
                except asyncio.TimeoutError:
                    pass

                # Periodic block summary
                await self._maybe_emit_block_summary()

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Alert manager error: {e}")

    async def _maybe_emit_block_summary(self) -> None:
        """Emit one summary alert instead of flooding with individual block events."""
        now   = time.time()
        total = sum(self._blocked_domains.values())

        if total == 0:
            return

        if (total >= BLOCK_SUMMARY_THRESHOLD or
                now - self._last_block_summary >= BLOCK_SUMMARY_INTERVAL):

            top = sorted(self._blocked_domains.items(), key=lambda x: x[1], reverse=True)[:5]
            top_str = ", ".join(f"{d}({n})" for d, n in top)

            alert = AlertEntry(
                alert_id=  generate_alert_id(),
                severity=  "info",
                category=  "network",
                title=     f"VPN Blocked {total} DNS Requests",
                detail=    f"Top blocked: {top_str}",
            )
            await state.add_alert(alert)

            self._blocked_domains.clear()
            self._last_block_summary = now

    async def _handle_event(self, event: dict) -> None:
        event_type = event.get("type", "")
        data       = event.get("data", {})

        if event_type == "file.threat":
            alert = AlertEntry(
                alert_id=  generate_alert_id(),
                severity=  SEV_HIGH,
                category=  "file",
                title=     f"File Threat: {Path(data.get('path', '')).name}",
                detail=    f"Reasons: {', '.join(data.get('reasons', []))}. "
                           f"Entropy: {data.get('entropy', 0):.2f}",
            )
            await state.add_alert(alert)
            await self._persist_alert(alert)

    async def _persist_alert(self, alert: AlertEntry) -> None:
        if alert.severity not in {SEV_HIGH, "critical"}:
            return
        try:
            ALERTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            record = {
                "alert_id":  alert.alert_id,
                "severity":  alert.severity,
                "category":  alert.category,
                "title":     alert.title,
                "detail":    alert.detail,
                "timestamp": alert.timestamp,
            }
            with open(ALERTS_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            log.debug(f"Alert persist error: {e}")