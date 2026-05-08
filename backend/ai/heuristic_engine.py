# Rule-based heuristic detection (PRIMARY)
# backend/ai/heuristic_engine.py
"""
PRIMARY detection engine — rule-based heuristics.
Fast, deterministic, zero ML overhead.
All detections here are high-confidence.
"""
import time
from collections import defaultdict, deque
from typing import Dict, Set
from backend.core.logger import get_logger
from backend.core.state import state, AlertEntry
from backend.core.event_bus import bus
from backend.utils.helpers import generate_alert_id, is_private_ip
from backend.utils.constants import (
    HIGH_FREQ_CONN_PER_MIN, SUSPICIOUS_PORT_LIST,
    TEMP_PATHS, SUSPICIOUS_PROCESS_NAMES,
    SEV_CRITICAL, SEV_HIGH, SEV_MEDIUM, SEV_LOW
)

log = get_logger("heuristics")

BROWSER_PROCESSES = {"chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", "brave.exe", "iexplore.exe"}
SCRIPTING_ENGINES = {"cmd.exe", "powershell.exe", "wscript.exe", "cscript.exe", "mshta.exe"}


class HeuristicEngine:
    """
    Stateful heuristic analyzer.
    Maintains rolling windows for frequency analysis.
    """

    def __init__(self):
        # pid → deque of connection timestamps (rolling 60s window)
        self._conn_timestamps: Dict[int, deque] = defaultdict(lambda: deque(maxlen=500))
        # pid → set of unique domains queried
        self._pid_domains:     Dict[int, Set[str]] = defaultdict(set)
        # domain → deque of access timestamps
        self._domain_hits:     Dict[str, deque]    = defaultdict(lambda: deque(maxlen=100))
        # Alert dedup: (pid, rule_id) → last_alert_time
        self._alert_times:     Dict[str, float]    = {}
        # Minimum seconds between same alert type
        self._alert_cooldown = 30.0

    async def analyze_connection(self, event: dict) -> None:
        """Analyze a new network connection event."""
        data = event.get("data", {})
        if not data:
            return

        pid         = data.get("pid", 0)
        remote_ip   = data.get("remote_addr", "")
        remote_port = data.get("remote_port", 0)
        domain      = data.get("domain", "")
        proc_name   = data.get("process_name", "").lower()
        now         = time.time()

        # Skip private IPs
        if is_private_ip(remote_ip):
            return

        # Track per-pid timestamps
        self._conn_timestamps[pid].append(now)
        if domain:
            self._pid_domains[pid].add(domain)
            self._domain_hits[domain].append(now)

        # ── RULE NET_001: High-frequency connections ──────────
        recent_conns = sum(
            1 for t in self._conn_timestamps[pid]
            if now - t < 60
        )
        if recent_conns > HIGH_FREQ_CONN_PER_MIN:
            await self._emit_alert(
                rule_id="NET_001",
                dedup_key=f"NET_001_{pid}",
                severity=SEV_HIGH,
                category="network",
                title=f"High-Frequency Connections: {proc_name or pid}",
                detail=f"Process {proc_name} (PID {pid}) made {recent_conns} connections in 60s",
                source_pid=pid,
                source_domain=domain,
                threat_delta=0.4,
                pid=pid,
            )

        # ── RULE NET_002: Suspicious port ─────────────────────
        if remote_port in SUSPICIOUS_PORT_LIST:
            await self._emit_alert(
                rule_id="NET_002",
                dedup_key=f"NET_002_{pid}_{remote_port}",
                severity=SEV_HIGH,
                category="network",
                title=f"Suspicious Port: {remote_port}",
                detail=f"{proc_name} (PID {pid}) connected to {remote_ip}:{remote_port}",
                source_pid=pid,
                source_domain=domain,
                threat_delta=0.5,
                pid=pid,
            )

        # ── RULE NET_006: Tor ports ────────────────────────────
        if remote_port in {9001, 9030, 9050, 9051}:
            await self._emit_alert(
                rule_id="NET_006",
                dedup_key=f"NET_006_{pid}",
                severity=SEV_CRITICAL,
                category="network",
                title=f"Possible Tor Connection: {proc_name}",
                detail=f"{proc_name} (PID {pid}) connecting to port {remote_port} on {remote_ip}",
                source_pid=pid,
                source_domain=domain,
                threat_delta=0.7,
                pid=pid,
            )

        # ── RULE NET_003: Unknown domain repeated ─────────────
        if domain:
            recent_hits = sum(
                1 for t in self._domain_hits[domain]
                if now - t < 60
            )
            if recent_hits > 10:
                await self._emit_alert(
                    rule_id="NET_003",
                    dedup_key=f"NET_003_{domain}",
                    severity=SEV_MEDIUM,
                    category="network",
                    title=f"Repeated Unknown Domain: {domain}",
                    detail=f"Domain {domain} accessed {recent_hits}× in 60s by {proc_name}",
                    source_pid=pid,
                    source_domain=domain,
                    threat_delta=0.2,
                    pid=pid,
                )

        # ── RULE NET_007: DGA detection ────────────────────────
        unique_domains = len(self._pid_domains[pid])
        if unique_domains > 50:
            await self._emit_alert(
                rule_id="NET_007",
                dedup_key=f"NET_007_{pid}",
                severity=SEV_MEDIUM,
                category="network",
                title=f"Possible DGA Activity: {proc_name}",
                detail=f"{proc_name} queried {unique_domains} unique domains (DGA indicator)",
                source_pid=pid,
                source_domain=domain,
                threat_delta=0.3,
                pid=pid,
            )

    async def analyze_process(self, event: dict) -> None:
        """Analyze a new process spawn event."""
        data = event.get("data", {})
        if not data:
            return

        pid        = data.get("pid", 0)
        name       = (data.get("name") or "").lower()
        exe        = (data.get("exe") or "").lower()
        cmdline    = (data.get("cmdline") or "").lower()

        # ── RULE PROC_001: Temp directory ─────────────────────
        if exe and any(tp in exe for tp in TEMP_PATHS):
            await self._emit_alert(
                rule_id="PROC_001",
                dedup_key=f"PROC_001_{pid}",
                severity=SEV_HIGH,
                category="process",
                title=f"Process from Temp: {name}",
                detail=f"PID {pid} running from temp location: {exe}",
                source_pid=pid,
                threat_delta=0.5,
                pid=pid,
            )

        # ── RULE PROC_002: Known malicious name ───────────────
        if name in SUSPICIOUS_PROCESS_NAMES:
            await self._emit_alert(
                rule_id="PROC_002",
                dedup_key=f"PROC_002_{name}",
                severity=SEV_CRITICAL,
                category="process",
                title=f"Known Attack Tool Detected: {name}",
                detail=f"Process {name} (PID {pid}) matches known attack tool signature",
                source_pid=pid,
                threat_delta=0.9,
                pid=pid,
            )

        # ── RULE PROC_003: Encoded PowerShell ─────────────────
        if name == "powershell.exe" and (
            "-encodedcommand" in cmdline or
            " -enc " in cmdline or
            "-e " in cmdline
        ):
            await self._emit_alert(
                rule_id="PROC_003",
                dedup_key=f"PROC_003_{pid}",
                severity=SEV_HIGH,
                category="process",
                title="Encoded PowerShell Command Detected",
                detail=f"PowerShell launched with encoded command (PID {pid}): {cmdline[:100]}",
                source_pid=pid,
                threat_delta=0.6,
                pid=pid,
            )

        # ── RULE PROC_004: Browser spawning script engine ─────
        # We can't easily get parent PID from the event, but we check
        # if cmdline contains browser-related paths
        if name in SCRIPTING_ENGINES:
            for browser in BROWSER_PROCESSES:
                if browser.replace(".exe", "") in cmdline:
                    await self._emit_alert(
                        rule_id="PROC_004",
                        dedup_key=f"PROC_004_{pid}",
                        severity=SEV_HIGH,
                        category="process",
                        title=f"Script Engine Spawned from Browser Context: {name}",
                        detail=f"{name} (PID {pid}) appears spawned from browser context",
                        source_pid=pid,
                        threat_delta=0.6,
                        pid=pid,
                    )
                    break

        # ── RULE PROC_007: Double extension ───────────────────
        import re
        if re.search(r'\.(pdf|doc|docx|xls|xlsx|txt|jpg|png)\.(exe|bat|cmd|scr|pif)$',
                     name, re.IGNORECASE):
            await self._emit_alert(
                rule_id="PROC_007",
                dedup_key=f"PROC_007_{pid}",
                severity=SEV_HIGH,
                category="process",
                title=f"Double Extension Executable: {name}",
                detail=f"Process {name} (PID {pid}) has double extension — social engineering indicator",
                source_pid=pid,
                threat_delta=0.7,
                pid=pid,
            )

    async def analyze_file(self, event: dict) -> None:
        """Analyze file system events from watchdog."""
        data = event.get("data", {})
        if not data:
            return
        # File analysis is handled by file_scanner + crypto module
        # Heuristic engine listens for the scanned result
        pass

    async def _emit_alert(
        self, rule_id: str, dedup_key: str,
        severity: str, category: str,
        title: str, detail: str,
        threat_delta: float = 0.0,
        source_pid: int = None,
        source_domain: str = None,
        pid: int = 0,
    ) -> None:
        """Emit alert with deduplication."""
        now = time.time()

        # Cooldown check
        last = self._alert_times.get(dedup_key, 0)
        if now - last < self._alert_cooldown:
            return
        self._alert_times[dedup_key] = now

        # Update process threat score
        if pid and pid in state.processes:
            proc = state.processes[pid]
            proc.threat_score = min(1.0, proc.threat_score + threat_delta)
            proc.flagged      = proc.threat_score > 0.4

        # Create alert
        alert = AlertEntry(
            alert_id=     generate_alert_id(),
            severity=     severity,
            category=     category,
            title=        title,
            detail=       detail,
            source_pid=   source_pid,
            source_domain=source_domain,
        )

        await state.add_alert(alert)
        await bus.publish("alert.new", {
            "alert_id":      alert.alert_id,
            "severity":      severity,
            "category":      category,
            "title":         title,
            "detail":        detail,
            "source_pid":    source_pid,
            "source_domain": source_domain,
            "timestamp":     now,
        })

        log.warning(f"[{severity.upper()}] {title}: {detail}")