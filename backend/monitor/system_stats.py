# backend/monitor/system_stats.py
import asyncio
import time
import psutil
from backend.core.logger import get_logger
from backend.core.state import state
from backend.core.event_bus import bus
from backend.utils.constants import STATS_INTERVAL_SEC

log = get_logger("sys_stats")


class SystemStatsMonitor:

    def __init__(self):
        self._prev_net  = psutil.net_io_counters()
        self._prev_time = time.time()
        self._running   = False
        psutil.cpu_percent(interval=None)

    async def run(self) -> None:
        self._running = True
        log.info("System stats monitor started.")
        while self._running:
            try:
                await self._collect()
                await asyncio.sleep(STATS_INTERVAL_SEC)
            except asyncio.CancelledError:
                break
            except RuntimeError as e:
                # Event loop shutting down — exit cleanly
                if "shutdown" in str(e).lower():
                    break
                log.error(f"Stats error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                if not self._running:
                    break
                log.error(f"Stats error: {e}")
                await asyncio.sleep(5)
        self._running = False

    async def _collect(self) -> None:
        if not self._running:
            return
        loop = asyncio.get_event_loop()
        try:
            stats = await loop.run_in_executor(None, self._blocking_collect)
        except RuntimeError:
            # Executor shut down
            self._running = False
            return

        state.cpu_percent  = stats["cpu_percent"]
        state.ram_percent  = stats["ram_percent"]
        state.ram_used_mb  = stats["ram_used_mb"]
        state.disk_percent = stats["disk_percent"]
        state.bytes_in    += stats["net_bytes_recv_delta"]
        state.bytes_out   += stats["net_bytes_sent_delta"]

        await bus.publish("system.stats", stats)

    def _blocking_collect(self) -> dict:
        now = time.time()
        cpu = psutil.cpu_percent(interval=None)

        mem = psutil.virtual_memory()
        ram_percent = mem.percent
        ram_used_mb = mem.used / 1024 / 1024

        try:
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
        except Exception:
            try:
                disk = psutil.disk_usage("C:\\")
                disk_percent = disk.percent
            except Exception:
                disk_percent = 0.0

        net              = psutil.net_io_counters()
        elapsed          = max(now - self._prev_time, 0.001)
        bytes_sent_delta = max(net.bytes_sent - self._prev_net.bytes_sent, 0)
        bytes_recv_delta = max(net.bytes_recv - self._prev_net.bytes_recv, 0)
        self._prev_net   = net
        self._prev_time  = now

        return {
            "cpu_percent":          round(cpu, 1),
            "ram_percent":          round(ram_percent, 1),
            "ram_used_mb":          round(ram_used_mb, 1),
            "disk_percent":         round(disk_percent, 1),
            "net_bytes_sent_delta": bytes_sent_delta,
            "net_bytes_recv_delta": bytes_recv_delta,
            "net_bytes_sent_rate":  round(bytes_sent_delta / elapsed, 0),
            "net_bytes_recv_rate":  round(bytes_recv_delta / elapsed, 0),
            "timestamp":            now,
        }