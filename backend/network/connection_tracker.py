# backend/network/connection_tracker.py
import asyncio
import time
import psutil
import socket
from typing import Dict, Set
from backend.core.logger import get_logger
from backend.core.state import state, ConnectionEntry
from backend.core.event_bus import bus
from backend.utils.helpers import is_private_ip
from backend.utils.constants import STATS_INTERVAL_SEC

log = get_logger("conn_tracker")

TRACKED_STATES = {
    "ESTABLISHED",
    "SYN_SENT",
    "CLOSE_WAIT",
    "FIN_WAIT1",
    "FIN_WAIT2",
}


class ConnectionTracker:

    def __init__(self):
        self._known_conns:    Set[str]        = set()
        self._dns_cache:      Dict[str, str]  = {}
        self._pid_names:      Dict[int, tuple] = {}
        self._pid_names_time: float           = 0.0
        self._running:        bool            = False

    async def run(self) -> None:
        self._running = True
        log.info("Connection tracker started.")
        while self._running:
            try:
                await self._scan()
                await asyncio.sleep(STATS_INTERVAL_SEC)
            except asyncio.CancelledError:
                break
            except RuntimeError as e:
                if "shutdown" in str(e).lower():
                    break
                log.error(f"Connection tracker error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                if not self._running:
                    break
                log.error(f"Connection tracker error: {e}")
                await asyncio.sleep(5)
        self._running = False

    async def _scan(self) -> None:
        if not self._running:
            return
        loop = asyncio.get_event_loop()
        try:
            connections = await loop.run_in_executor(None, self._collect)
        except RuntimeError:
            self._running = False
            return

        current_keys = set(connections.keys())
        new_keys     = current_keys - self._known_conns

        for key in new_keys:
            conn = connections[key]
            await bus.publish("network.connection", {
                "pid":          conn.pid,
                "process_name": conn.process_name,
                "local_addr":   conn.local_addr,
                "local_port":   conn.local_port,
                "remote_addr":  conn.remote_addr,
                "remote_port":  conn.remote_port,
                "domain":       conn.domain,
                "protocol":     conn.protocol,
                "timestamp":    conn.timestamp,
            })

        self._known_conns    = current_keys
        state.active_connections = connections

        if state.ws_clients:
            conns_data = [
                {
                    "pid":          c.pid,
                    "process_name": c.process_name,
                    "local_addr":   c.local_addr,
                    "local_port":   c.local_port,
                    "remote_addr":  c.remote_addr,
                    "remote_port":  c.remote_port,
                    "domain":       c.domain,
                    "protocol":     c.protocol,
                    "flagged":      c.flagged,
                    "threat_score": c.threat_score,
                    "bytes_sent":   c.bytes_sent,
                    "bytes_recv":   c.bytes_recv,
                }
                for c in list(connections.values())[:100]
            ]
            await bus.publish("connections.update", {"connections": conns_data})

    def _refresh_pid_names(self) -> None:
        now = time.time()
        if now - self._pid_names_time < 5.0:
            return
        self._pid_names_time = now
        self._pid_names = {}
        try:
            for proc in psutil.process_iter(
                attrs=["pid", "name", "exe"], ad_value=None
            ):
                info = proc.info
                if info["pid"]:
                    self._pid_names[info["pid"]] = (
                        info.get("name") or "unknown",
                        info.get("exe") or "",
                    )
        except Exception:
            pass

    def _resolve_domain(self, ip: str) -> str:
        cached = self._dns_cache.get(ip)
        if cached is not None:
            return cached

        result = ""
        try:
            result = socket.gethostbyaddr(ip)[0]
        except Exception:
            pass

        self._dns_cache[ip] = result

        if len(self._dns_cache) > 8000:
            keys_to_del = list(self._dns_cache.keys())[:2000]
            for k in keys_to_del:
                del self._dns_cache[k]

        return result

    def _collect(self) -> Dict[str, ConnectionEntry]:
        self._refresh_pid_names()
        conns: Dict[str, ConnectionEntry] = {}

        try:
            all_net_conns = psutil.net_connections(kind="inet")
        except Exception as e:
            log.debug(f"net_connections error: {e}")
            return conns

        for conn in all_net_conns:
            try:
                if not conn.raddr:
                    continue
                if conn.status and conn.status not in TRACKED_STATES:
                    continue

                remote_ip   = conn.raddr.ip
                remote_port = conn.raddr.port

                if remote_ip in ("127.0.0.1", "::1", "0.0.0.0"):
                    continue

                pid        = conn.pid or 0
                name, exe  = self._pid_names.get(pid, ("unknown", ""))

                if conn.type == socket.SOCK_STREAM:
                    proto = "TCP"
                elif conn.type == socket.SOCK_DGRAM:
                    proto = "UDP"
                else:
                    proto = "UNKNOWN"

                laddr  = conn.laddr
                domain = self._resolve_domain(remote_ip)
                key    = f"{pid}_{remote_ip}_{remote_port}_{proto}"

                entry = ConnectionEntry(
                    pid=          pid,
                    process_name= name,
                    local_addr=   laddr.ip if laddr else "",
                    local_port=   laddr.port if laddr else 0,
                    remote_addr=  remote_ip,
                    remote_port=  remote_port,
                    domain=       domain,
                    protocol=     proto,
                    timestamp=    time.time(),
                )
                conns[key] = entry

            except Exception as e:
                log.debug(f"Connection parse error: {e}")
                continue

        return conns