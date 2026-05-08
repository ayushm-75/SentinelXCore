# backend/network/dns_resolver.py
"""
Async DNS resolver with LRU cache.
Resolves IPs to domain names and extracts TLD/registrable domain.
Fully offline after initial resolution (cache-based).
"""
import asyncio
import socket
import time
from collections import OrderedDict
from typing import Optional, Tuple
from backend.core.logger import get_logger

try:
    import tldextract
    _HAS_TLDEXTRACT = True
except ImportError:
    _HAS_TLDEXTRACT = False

log = get_logger("dns_resolver")


class LRUCache:
    def __init__(self, max_size: int = 5000):
        self._cache: OrderedDict = OrderedDict()
        self._max   = max_size

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: str) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._max:
            self._cache.popitem(last=False)

    def __len__(self) -> int:
        return len(self._cache)


# Global shared cache
_reverse_cache = LRUCache(5000)
_forward_cache = LRUCache(5000)


def extract_registered_domain(domain: str) -> str:
    """
    Extract the registrable domain from a full domain name.
    E.g., "ads.tracking.example.co.uk" → "example.co.uk"
    Falls back to last 2 labels if tldextract unavailable.
    """
    if not domain:
        return ""
    if _HAS_TLDEXTRACT:
        try:
            ext = tldextract.extract(domain)
            if ext.domain and ext.suffix:
                return f"{ext.domain}.{ext.suffix}"
        except Exception:
            pass
    # Fallback: last 2 labels
    parts = domain.rstrip(".").split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else domain


def reverse_lookup_sync(ip: str) -> Optional[str]:
    """Synchronous reverse DNS with cache."""
    cached = _reverse_cache.get(ip)
    if cached is not None:
        return cached or None

    try:
        result = socket.gethostbyaddr(ip)[0]
        _reverse_cache.set(ip, result)
        return result
    except Exception:
        _reverse_cache.set(ip, "")   # Cache negative result
        return None


def forward_lookup_sync(domain: str) -> Optional[str]:
    """Synchronous forward DNS with cache."""
    cached = _forward_cache.get(domain)
    if cached is not None:
        return cached or None

    try:
        result = socket.gethostbyname(domain)
        _forward_cache.set(domain, result)
        return result
    except Exception:
        _forward_cache.set(domain, "")
        return None


async def reverse_lookup(ip: str) -> Optional[str]:
    """Async reverse DNS lookup (runs in executor)."""
    cached = _reverse_cache.get(ip)
    if cached is not None:
        return cached or None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, reverse_lookup_sync, ip)


async def forward_lookup(domain: str) -> Optional[str]:
    """Async forward DNS lookup (runs in executor)."""
    cached = _forward_cache.get(domain)
    if cached is not None:
        return cached or None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, forward_lookup_sync, domain)


def get_cache_stats() -> dict:
    return {
        "reverse_cache_size": len(_reverse_cache),
        "forward_cache_size": len(_forward_cache),
    }