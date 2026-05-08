# Kill / quarantine process
# backend/protection/process_guardian.py
"""Process guardian — kill/quarantine suspicious processes."""
import asyncio
import psutil
from backend.core.logger import get_logger
from backend.core.state import state
from backend.core.event_bus import bus

log = get_logger("proc_guardian")


class ProcessGuardian:

    async def kill_process(self, pid: int, reason: str = "User request") -> bool:
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            proc.terminate()

            # Wait up to 3 seconds, then force kill
            try:
                proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                proc.kill()

            log.warning(f"Process killed: {name} (PID {pid}) — Reason: {reason}")

            # Remove from state
            state.processes.pop(pid, None)

            await bus.publish("process.killed", {
                "pid":    pid,
                "name":   name,
                "reason": reason,
            })
            return True

        except psutil.NoSuchProcess:
            log.warning(f"Process {pid} already gone.")
            return False
        except psutil.AccessDenied:
            log.error(f"Access denied killing PID {pid}. Run as Administrator.")
            return False
        except Exception as e:
            log.error(f"Kill error for PID {pid}: {e}")
            return False

    async def ignore_process(self, pid: int) -> None:
        """Mark process as trusted — clear threat score."""
        if pid in state.processes:
            state.processes[pid].threat_score = 0.0
            state.processes[pid].flagged      = False
        log.info(f"Process {pid} marked as trusted.")

    async def auto_kill_if_critical(self, pid: int) -> None:
        """Auto-kill if threat score is critical (>0.9)."""
        proc = state.processes.get(pid)
        if proc and proc.threat_score >= 0.9:
            await self.kill_process(pid, reason="Auto-kill: critical threat score")