# Feature engineering for ML
# backend/ai/feature_extractor.py
"""
Feature extraction for anomaly detection model.
Converts raw system state into a fixed-length numeric vector.

Features (12 total — must stay lightweight):
0:  cpu_percent
1:  ram_percent
2:  active_connection_count
3:  bytes_out_rate (per interval)
4:  bytes_in_rate
5:  blocked_count_delta
6:  unique_domains_per_interval
7:  flagged_process_count
8:  alert_count_total
9:  max_process_cpu
10: max_process_memory_mb
11: suspicious_port_connections
"""
import time
from collections import deque
from typing import List, Optional
import numpy as np
from backend.core.state import state
from backend.utils.constants import SUSPICIOUS_PORT_LIST

FEATURE_DIM = 12


class FeatureExtractor:

    def __init__(self):
        self._prev_bytes_out  = 0
        self._prev_bytes_in   = 0
        self._prev_blocked    = 0
        self._domain_window: deque = deque(maxlen=100)
        self._prev_time = time.time()

    def extract(self) -> Optional[np.ndarray]:
        """Extract current feature vector. Returns None if not ready."""
        try:
            now = time.time()
            dt  = max(now - self._prev_time, 1.0)

            # Rate calculations
            bytes_out_delta = max(state.bytes_out - self._prev_bytes_out, 0)
            bytes_in_delta  = max(state.bytes_in  - self._prev_bytes_in,  0)
            blocked_delta   = max(state.blocked_count - self._prev_blocked, 0)

            bytes_out_rate = bytes_out_delta / dt
            bytes_in_rate  = bytes_in_delta  / dt

            self._prev_bytes_out = state.bytes_out
            self._prev_bytes_in  = state.bytes_in
            self._prev_blocked   = state.blocked_count
            self._prev_time      = now

            # Process stats
            procs = list(state.processes.values())
            flagged_count  = sum(1 for p in procs if p.flagged)
            max_cpu        = max((p.cpu_percent for p in procs), default=0.0)
            max_mem        = max((p.memory_mb   for p in procs), default=0.0)

            # Suspicious port connections
            susp_port_conns = sum(
                1 for c in state.active_connections.values()
                if c.remote_port in SUSPICIOUS_PORT_LIST
            )

            # Domain diversity
            domain_count = len(set(
                c.domain for c in state.active_connections.values()
                if c.domain
            ))

            # Alert counts
            total_alerts = sum(state.alert_count.values())

            features = np.array([
                state.cpu_percent,
                state.ram_percent,
                len(state.active_connections),
                bytes_out_rate / 1024,       # KB/s
                bytes_in_rate  / 1024,       # KB/s
                blocked_delta,
                domain_count,
                flagged_count,
                total_alerts,
                max_cpu,
                max_mem,
                susp_port_conns,
            ], dtype=np.float32)

            return features

        except Exception:
            return None

    @property
    def feature_names(self) -> List[str]:
        return [
            "cpu_percent", "ram_percent", "conn_count",
            "bytes_out_kbs", "bytes_in_kbs", "blocked_delta",
            "domain_diversity", "flagged_procs", "alert_total",
            "max_proc_cpu", "max_proc_mem_mb", "susp_port_conns"
        ]