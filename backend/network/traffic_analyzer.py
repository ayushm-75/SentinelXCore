# Traffic frequency analysis
# backend/network/traffic_analyzer.py
"""
Traffic frequency analyzer.
Detects high-volume outbound transfers.
"""
import time
from collections import defaultdict, deque
from backend.core.state import state
from backend.core.logger import get_logger
from backend.utils.constants import HIGH_BYTES_OUT_PER_SEC

log = get_logger("traffic_analyzer")


class TrafficAnalyzer:

    def __init__(self):
        # pid → deque of (timestamp, bytes) tuples
        self._pid_bytes: dict = defaultdict(lambda: deque(maxlen=60))

    def record(self, pid: int, bytes_sent: int) -> None:
        self._pid_bytes[pid].append((time.time(), bytes_sent))

    def get_rate(self, pid: int, window_sec: float = 10.0) -> float:
        """Return bytes/sec for pid over last window_sec seconds."""
        now     = time.time()
        samples = [b for t, b in self._pid_bytes[pid] if now - t < window_sec]
        if not samples:
            return 0.0
        return sum(samples) / window_sec

    def check_exfiltration(self, pid: int) -> bool:
        rate = self.get_rate(pid, window_sec=10.0)
        return rate > HIGH_BYTES_OUT_PER_SEC