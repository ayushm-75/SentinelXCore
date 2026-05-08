# VPN toggle logic
# backend/vpn/vpn_controller.py
"""
VPN Controller — orchestrates the full ad-block VPN mode.
ON:  Load blocklists → Start DivertEngine → Block DNS queries
OFF: Stop DivertEngine
"""
import asyncio
from typing import Optional
from backend.core.logger import get_logger
from backend.core.state import state
from backend.core.event_bus import bus
from backend.vpn.blocklist_manager import BlocklistManager
from backend.vpn.divert_engine import DivertEngine, set_event_loop
from backend.utils.constants import BLOCKLIST_DIR

log = get_logger("vpn_controller")

# Global divert instance
_divert_engine: Optional[DivertEngine] = None


class VPNController:

    def __init__(self):
        self.blocklist_mgr = BlocklistManager()
        self._started = False

    async def start(self) -> bool:
        global _divert_engine

        log.info("VPN Controller starting...")

        # ── Step 1: Ensure blocklists are downloaded ──────────
        has_any = any(
            (BLOCKLIST_DIR / f"{lid}.txt").exists()
            for lid in ["adguard", "easylist", "easyprivacy", "hagezi"]
        )

        if not has_any:
            log.info("No blocklists found. Downloading now (first run)...")
            await self.blocklist_mgr.download_all()
        else:
            log.info("Loading existing blocklists...")
            await self.blocklist_mgr.load_lists()

        # ── Step 2: Start DNS interception ────────────────────
        set_event_loop(asyncio.get_event_loop())

        _divert_engine = DivertEngine(
            is_blocked_fn=self.blocklist_mgr.is_blocked
        )

        success = await asyncio.get_event_loop().run_in_executor(
            None, _divert_engine.start
        )

        if success:
            state.vpn_active = True
            self._started = True
            await bus.publish("vpn.toggled", {"enabled": True})
            log.info("VPN / AdBlock mode: ACTIVE")
        else:
            log.error("VPN failed to start — check admin rights and WinDivert.")
            state.vpn_active = False

        return success

    async def run(self) -> None:
        """Keep running until cancelled."""
        try:
            while self._started and state.vpn_active:
                await asyncio.sleep(5)
                # Periodic health check
                if _divert_engine and not _divert_engine._running:
                    log.warning("DivertEngine stopped unexpectedly. Restarting...")
                    await asyncio.get_event_loop().run_in_executor(
                        None, _divert_engine.start
                    )
        except asyncio.CancelledError:
            await self.stop()

    async def stop(self) -> None:
        global _divert_engine
        if _divert_engine:
            await asyncio.get_event_loop().run_in_executor(
                None, _divert_engine.stop
            )
            _divert_engine = None

        state.vpn_active = False
        self._started = False
        await bus.publish("vpn.toggled", {"enabled": False})
        log.info("VPN / AdBlock mode: STOPPED")

    @staticmethod
    async def stop_global() -> None:
        global _divert_engine
        if _divert_engine:
            _divert_engine.stop()
            _divert_engine = None
        state.vpn_active = False