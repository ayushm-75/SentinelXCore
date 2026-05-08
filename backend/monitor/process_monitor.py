# backend/monitor/process_monitor.py
import asyncio
import time
import psutil
from typing import Dict, Set
from backend.core.logger import get_logger
from backend.core.state import state, ProcessEntry
from backend.core.event_bus import bus
from backend.utils.constants import (
    PROCESS_SCAN_INTERVAL_SEC, TEMP_PATHS,
    SUSPICIOUS_PROCESS_NAMES, SEV_HIGH, SEV_MEDIUM
)
from backend.utils.helpers import generate_alert_id

log = get_logger("proc_monitor")


class ProcessMonitor:

    def __init__(self):
        self._known_pids: Set[int] = set()
        self._first_scan = True
        self._running    = False

    async def run(self) -> None:
        self._running = True
        log.info("Process monitor started.")
        while self._running:
            try:
                await self._scan()
                await asyncio.sleep(PROCESS_SCAN_INTERVAL_SEC)
            except asyncio.CancelledError:
                break
            except RuntimeError as e:
                if "shutdown" in str(e).lower():
                    break
                log.error(f"Process scan error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                if not self._running:
                    break
                log.error(f"Process scan error: {e}")
                await asyncio.sleep(5)
        self._running = False

    async def _scan(self) -> None:
        if not self._running:
            return
        loop = asyncio.get_event_loop()
        try:
            processes = await loop.run_in_executor(None, self._collect_processes)
        except RuntimeError:
            self._running = False
            return

        current_pids = set(processes.keys())

        if not self._first_scan:
            new_pids = current_pids - self._known_pids
            for pid in new_pids:
                entry = processes[pid]
                await bus.publish("process.new", {
                    "pid":     entry.pid,
                    "name":    entry.name,
                    "exe":     entry.exe,
                    "cmdline": entry.cmdline,
                })

        gone_pids = self._known_pids - current_pids
        for pid in gone_pids:
            await bus.publish("process.gone", {"pid": pid})

        self._known_pids = current_pids
        state.processes  = processes
        self._first_scan = False

    def _collect_processes(self) -> Dict[int, ProcessEntry]:
        procs: Dict[int, ProcessEntry] = {}
        attrs = [
            "pid", "name", "exe", "cmdline",
            "cpu_percent", "memory_info",
            "status", "username", "create_time",
            "connections"
        ]

        for proc in psutil.process_iter(attrs=attrs, ad_value=None):
            try:
                info = proc.info
                if info["pid"] is None:
                    continue

                exe     = info.get("exe") or ""
                cmdline = " ".join(info.get("cmdline") or [])
                name    = info.get("name") or ""
                mem     = info.get("memory_info")
                mem_mb  = (mem.rss / 1024 / 1024) if mem else 0.0

                try:
                    conn_count = len(info.get("connections") or [])
                except Exception:
                    conn_count = 0

                entry = ProcessEntry(
                    pid=         info["pid"],
                    name=        name,
                    exe=         exe,
                    cmdline=     cmdline[:200],
                    cpu_percent= round(info.get("cpu_percent") or 0.0, 2),
                    memory_mb=   round(mem_mb, 2),
                    status=      info.get("status") or "unknown",
                    username=    info.get("username") or "unknown",
                    create_time= info.get("create_time") or 0.0,
                    connections= conn_count,
                )
                procs[entry.pid] = entry

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                log.debug(f"Process info error: {e}")

        return procs