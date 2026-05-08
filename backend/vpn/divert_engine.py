# PyDivert packet interception
# backend/vpn/divert_engine.py
"""
WinDivert-based packet interception engine for DNS blocking.

Strategy:
- Intercept outbound UDP/TCP on port 53 (DNS queries)
- Parse DNS query to extract requested domain
- If domain in blocklist → DROP packet (DNS query never reaches server)
- Otherwise → REINJECT packet (normal flow)

For HTTPS (port 443) blocking:
- We block at DNS level — if DNS is blocked, HTTPS connection fails naturally
- This avoids complex TLS interception

WinDivert auto-install:
- Downloads WinDivert binaries if not present
- Copies WinDivert64.sys to correct location
"""
import asyncio
import struct
import socket
import threading
import os
import sys
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Callable
import requests

from backend.core.logger import get_logger
from backend.core.state import state
from backend.core.event_bus import bus
from backend.utils.constants import WINDIVERT_DIR

log = get_logger("divert_engine")

# WinDivert download (pre-built binaries)
WINDIVERT_VERSION = "2.2.2"
WINDIVERT_URL = (
    f"https://github.com/basil00/Divert/releases/download/"
    f"v{WINDIVERT_VERSION}/WinDivert-{WINDIVERT_VERSION}-A.zip"
)
WINDIVERT_ZIP = WINDIVERT_DIR / f"WinDivert-{WINDIVERT_VERSION}.zip"


def ensure_windivert() -> bool:
    """Download and install WinDivert if not present."""
    WINDIVERT_DIR.mkdir(parents=True, exist_ok=True)

    dll_path = WINDIVERT_DIR / "WinDivert.dll"
    if dll_path.exists():
        log.debug("WinDivert already installed.")
        return True

    log.info(f"WinDivert not found. Downloading v{WINDIVERT_VERSION}...")
    try:
        r = requests.get(WINDIVERT_URL, timeout=60, stream=True)
        r.raise_for_status()

        with open(WINDIVERT_ZIP, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)

        with zipfile.ZipFile(WINDIVERT_ZIP, "r") as z:
            # Extract x64 binaries
            for member in z.namelist():
                fname = Path(member).name
                if fname in {"WinDivert.dll", "WinDivert64.sys", "WinDivert.lib"}:
                    # Only extract x64 variants
                    if "x64" in member or "64" in member:
                        z.extract(member, WINDIVERT_DIR)
                        # Flatten directory
                        extracted = WINDIVERT_DIR / member
                        dest = WINDIVERT_DIR / fname
                        if extracted != dest:
                            shutil.move(str(extracted), str(dest))

        # Add to PATH so pydivert can find it
        os.environ["PATH"] = str(WINDIVERT_DIR) + os.pathsep + os.environ.get("PATH", "")
        sys.path.insert(0, str(WINDIVERT_DIR))

        log.info("WinDivert installed successfully.")
        return True

    except Exception as e:
        log.error(f"WinDivert installation failed: {e}")
        log.error("VPN/DNS blocking will be unavailable.")
        return False


def _parse_dns_query_domain(payload: bytes) -> Optional[str]:
    """
    Extract queried domain from a raw DNS query packet.
    DNS payload starts after UDP header (8 bytes from UDP start).
    We receive the DNS payload directly from pydivert.
    """
    try:
        # Skip DNS header (12 bytes): ID, flags, counts
        if len(payload) < 13:
            return None

        offset = 12
        labels = []

        while offset < len(payload):
            length = payload[offset]
            if length == 0:
                break
            # Pointer compression
            if (length & 0xC0) == 0xC0:
                break
            offset += 1
            if offset + length > len(payload):
                return None
            labels.append(payload[offset:offset + length].decode("ascii", errors="ignore"))
            offset += length

        if labels:
            return ".".join(labels).lower()
    except Exception:
        pass
    return None


class DivertEngine:
    """
    Async-compatible DNS packet interception using pydivert.
    Runs in a separate thread (pydivert is blocking).
    """

    def __init__(self, is_blocked_fn: Callable[[str], bool]):
        self._is_blocked = is_blocked_fn
        self._running    = False
        self._thread: Optional[threading.Thread] = None
        self._handle     = None

    def start(self) -> bool:
        if not ensure_windivert():
            return False

        try:
            import pydivert
            self._handle = pydivert.WinDivert(
                # Capture outbound DNS queries only (UDP port 53)
                "udp.DstPort == 53 and outbound"
            )
            self._handle.open()
            self._running = True
            self._thread  = threading.Thread(
                target=self._capture_loop,
                daemon=True,
                name="divert-dns"
            )
            self._thread.start()
            log.info("DivertEngine started — DNS interception active")
            return True
        except Exception as e:
            log.error(f"DivertEngine start failed: {e}")
            return False

    def stop(self) -> None:
        self._running = False
        try:
            if self._handle:
                self._handle.close()
        except Exception:
            pass
        log.info("DivertEngine stopped.")

    def _capture_loop(self) -> None:
        """Blocking capture loop — runs in daemon thread."""
        import pydivert
        try:
            while self._running:
                try:
                    packet = self._handle.recv()
                except Exception:
                    if self._running:
                        log.warning("DivertEngine: recv error, continuing...")
                    break

                if packet is None:
                    continue

                # Extract DNS payload from UDP
                try:
                    udp_payload = packet.udp.payload
                    domain = _parse_dns_query_domain(bytes(udp_payload))

                    if domain and self._is_blocked(domain):
                        # DROP — do not reinject
                        state.blocked_count += 1
                        asyncio.run_coroutine_threadsafe(
                            bus.publish("network.blocked", {
                                "domain":    domain,
                                "action":    "dns_drop",
                                "timestamp": __import__("time").time(),
                            }),
                            _get_event_loop()
                        )
                        log.debug(f"BLOCKED DNS: {domain}")
                        # Do NOT call handle.send(packet) → packet is dropped
                    else:
                        # ALLOW — reinject packet
                        self._handle.send(packet)

                except Exception as e:
                    # On any parse error, always reinject to avoid breaking connectivity
                    try:
                        self._handle.send(packet)
                    except Exception:
                        pass

        except Exception as e:
            log.error(f"Divert capture loop crashed: {e}")
        finally:
            self._running = False


_event_loop: Optional[asyncio.AbstractEventLoop] = None


def _get_event_loop() -> asyncio.AbstractEventLoop:
    global _event_loop
    if _event_loop is None:
        _event_loop = asyncio.get_event_loop()
    return _event_loop


def set_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _event_loop
    _event_loop = loop