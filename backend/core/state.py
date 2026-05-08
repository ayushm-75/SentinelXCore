# Global application state
# backend/core/state.py
"""
Global shared application state — thread-safe via asyncio locks.
No global mutable dicts scattered across modules.
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Any
from collections import deque


@dataclass
class ConnectionEntry:
    pid: int
    process_name: str
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    domain: Optional[str]
    protocol: str
    timestamp: float = field(default_factory=time.time)
    bytes_sent: int = 0
    bytes_recv: int = 0
    flagged: bool = False
    threat_score: float = 0.0


@dataclass
class AlertEntry:
    alert_id: str
    severity: str          # "critical" | "high" | "medium" | "low" | "info"
    category: str          # "network" | "process" | "file" | "ai"
    title: str
    detail: str
    timestamp: float = field(default_factory=time.time)
    acknowledged: bool = False
    source_pid: Optional[int] = None
    source_domain: Optional[str] = None


@dataclass
class ProcessEntry:
    pid: int
    name: str
    exe: str
    cmdline: str
    cpu_percent: float
    memory_mb: float
    status: str
    username: str
    create_time: float
    connections: int = 0
    threat_score: float = 0.0
    flagged: bool = False


class AppState:
    def __init__(self):
        self._lock = asyncio.Lock()

        # Network
        self.active_connections: Dict[str, ConnectionEntry] = {}
        self.recent_domains: deque = deque(maxlen=500)
        self.blocked_count: int = 0
        self.total_packets: int = 0
        self.bytes_in: int = 0
        self.bytes_out: int = 0

        # Processes
        self.processes: Dict[int, ProcessEntry] = {}

        # Alerts
        self.alerts: deque = deque(maxlen=1000)
        self.alert_count: Dict[str, int] = {
            "critical": 0, "high": 0, "medium": 0, "low": 0
        }

        # System
        self.cpu_percent: float = 0.0
        self.ram_percent: float = 0.0
        self.ram_used_mb: float = 0.0
        self.disk_percent: float = 0.0

        # VPN
        self.vpn_active: bool = False
        self.blocklist_loaded: bool = False
        self.blocklist_domain_count: int = 0

        # AI
        self.model_trained: bool = False
        self.anomalies_detected: int = 0

        # Runtime
        self.start_time: float = time.time()
        self.ws_clients: Set[Any] = set()

    async def add_alert(self, alert: AlertEntry) -> None:
        async with self._lock:
            self.alerts.appendleft(alert)
            sev = alert.severity
            if sev in self.alert_count:
                self.alert_count[sev] += 1

    async def get_alerts(self, limit: int = 100) -> List[AlertEntry]:
        async with self._lock:
            return list(self.alerts)[:limit]

    async def acknowledge_alert(self, alert_id: str) -> bool:
        async with self._lock:
            for alert in self.alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    return True
            return False

    def get_uptime(self) -> float:
        return time.time() - self.start_time

    def snapshot(self) -> dict:
        """Fast read snapshot for WS broadcast — no lock needed for primitives."""
        return {
            "cpu_percent":     self.cpu_percent,
            "ram_percent":     self.ram_percent,
            "ram_used_mb":     round(self.ram_used_mb, 1),
            "disk_percent":    self.disk_percent,
            "total_packets":   self.total_packets,
            "bytes_in":        self.bytes_in,
            "bytes_out":       self.bytes_out,
            "blocked_count":   self.blocked_count,
            "vpn_active":      self.vpn_active,
            "model_trained":   self.model_trained,
            "anomalies":       self.anomalies_detected,
            "alert_count":     self.alert_count,
            "connection_count": len(self.active_connections),
            "uptime":          round(self.get_uptime(), 1),
            "blocklist_domains": self.blocklist_domain_count,
        }


# Global singleton
state = AppState()