# Scapy async packet capture
# backend/network/packet_capture.py
"""
Scapy-based async packet capture.
Captures DNS responses to extract domains being queried.
Lightweight — only sniffs DNS (port 53) to minimize CPU overhead.
"""
import asyncio
import threading
import time
from typing import Optional
from backend.core.logger import get_logger
from backend.core.state import state
from backend.core.event_bus import bus

log = get_logger("packet_cap")


class PacketCapture:

    def __init__(self):
        self._running  = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def run(self) -> None:
        log.info("Packet capture starting...")
        self._loop = asyncio.get_event_loop()

        try:
            import scapy.all as scapy
            # Test that scapy works
            ifaces = scapy.get_if_list()
            log.info(f"Scapy ready. Interfaces: {ifaces[:3]}...")
        except Exception as e:
            log.error(f"Scapy not available: {e}")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._capture_thread,
            daemon=True,
            name="packet-cap"
        )
        self._thread.start()

        try:
            while self._running:
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            self._running = False

    def _capture_thread(self) -> None:
        """Blocking capture loop in daemon thread."""
        try:
            import scapy.all as scapy

            def packet_handler(pkt):
                try:
                    self._process_packet(pkt)
                except Exception:
                    pass

            # Only capture DNS (UDP port 53) — very low overhead
            scapy.sniff(
                filter="udp port 53",
                prn=packet_handler,
                store=False,
                stop_filter=lambda _: not self._running,
            )
        except Exception as e:
            log.error(f"Capture thread error: {e}")
        finally:
            self._running = False
            log.info("Packet capture thread stopped.")

    def _process_packet(self, pkt) -> None:
        """Process a captured DNS packet."""
        try:
            import scapy.all as scapy

            state.total_packets += 1

            if pkt.haslayer(scapy.DNS):
                dns = pkt[scapy.DNS]

                # DNS Response (qr=1) with answers
                if dns.qr == 1 and dns.an:
                    for i in range(dns.ancount):
                        try:
                            rr = dns.an[i]
                            if hasattr(rr, "rrname"):
                                domain = rr.rrname.decode("utf-8", errors="ignore").rstrip(".")
                                if domain:
                                    state.recent_domains.append({
                                        "domain":    domain,
                                        "timestamp": time.time(),
                                    })
                                    asyncio.run_coroutine_threadsafe(
                                        bus.publish("dns.resolved", {
                                            "domain":    domain,
                                            "timestamp": time.time(),
                                        }),
                                        self._loop
                                    )
                        except Exception:
                            pass

                # DNS Query (qr=0)
                elif dns.qr == 0 and dns.qd:
                    try:
                        domain = dns.qd.qname.decode("utf-8", errors="ignore").rstrip(".")
                        if domain:
                            asyncio.run_coroutine_threadsafe(
                                bus.publish("dns.query", {
                                    "domain":    domain,
                                    "timestamp": time.time(),
                                }),
                                self._loop
                            )
                    except Exception:
                        pass

        except Exception:
            pass