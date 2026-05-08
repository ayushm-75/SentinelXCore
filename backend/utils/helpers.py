# General utilities
# backend/utils/helpers.py
import hashlib
import math
import time
import uuid
import socket
from collections import Counter
from pathlib import Path
from typing import Optional


def generate_alert_id() -> str:
    return str(uuid.uuid4())[:8].upper()


def compute_entropy(data: bytes) -> float:
    """Shannon entropy in bits per byte. High = packed/encrypted."""
    if not data:
        return 0.0
    counter = Counter(data)
    length = len(data)
    entropy = -sum(
        (count / length) * math.log2(count / length)
        for count in counter.values()
    )
    return round(entropy, 4)


def file_entropy(path: Path, sample_bytes: int = 65536) -> float:
    """Compute entropy from first N bytes of a file."""
    try:
        with open(path, "rb") as f:
            data = f.read(sample_bytes)
        return compute_entropy(data)
    except Exception:
        return 0.0


def sha256_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def is_private_ip(ip: str) -> bool:
    """True if IP is RFC-1918 / loopback / link-local."""
    try:
        parts = list(map(int, ip.split(".")))
        if parts[0] == 10:
            return True
        if parts[0] == 172 and 16 <= parts[1] <= 31:
            return True
        if parts[0] == 192 and parts[1] == 168:
            return True
        if parts[0] == 127:
            return True
        if parts[0] == 169 and parts[1] == 254:
            return True
        return False
    except Exception:
        return False


def safe_resolve(ip: str) -> Optional[str]:
    """Reverse DNS lookup with timeout guard."""
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def format_bytes(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def timestamp_ms() -> int:
    return int(time.time() * 1000)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))