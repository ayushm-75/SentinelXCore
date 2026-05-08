# backend/core/engine.py
import asyncio
import ctypes
import sys
import os
from pathlib import Path
from backend.core.logger import get_logger, setup_logger
from backend.core.settings import get_settings
from backend.core.event_bus import bus
from backend.core.state import state

log = get_logger("engine")


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


class SentinelXEngine:
    def __init__(self):
        self.settings        = get_settings()
        self._tasks: list    = []
        self._shutdown_event = asyncio.Event()
        self._admin          = is_admin()

    async def start(self) -> None:
        log.info("=" * 55)
        log.info("  SentinelX Core v1.0.0 — Starting up")
        log.info("=" * 55)

        if not self._admin:
            log.warning("⚠  NOT running as Administrator!")
            log.warning("   Packet capture and VPN will be disabled.")

        self._tasks.append(asyncio.create_task(
            bus.dispatch_loop(), name="event_bus"
        ))

        await self._start_core_subsystems()

        if self._admin:
            await self._start_privileged_subsystems()
        else:
            log.warning("Skipping packet capture and VPN (no admin rights).")

        log.info("All subsystems online. SentinelX Core is running.")

    async def _start_core_subsystems(self) -> None:
        """Subsystems that work without admin rights."""
        log.info("Starting core subsystems...")

        # Each subsystem in its own try/except so one failure
        # doesn't silently kill all the others
        try:
            from backend.protection.alert_manager import AlertManager
            alert_mgr = AlertManager()
            bus.subscribe("*", alert_mgr.on_event)
            self._tasks.append(asyncio.create_task(
                alert_mgr.run(), name="alert_manager"
            ))
        except Exception as e:
            log.error(f"AlertManager failed to start: {e}", exc_info=True)

        try:
            from backend.protection.file_guard import FileGuard
            FileGuard()
        except Exception as e:
            log.error(f"FileGuard failed to start: {e}", exc_info=True)

        try:
            from backend.monitor.system_stats import SystemStatsMonitor
            sys_monitor = SystemStatsMonitor()
            self._tasks.append(asyncio.create_task(
                sys_monitor.run(), name="sys_stats"
            ))
        except Exception as e:
            log.error(f"SystemStatsMonitor failed to start: {e}", exc_info=True)

        try:
            from backend.monitor.process_monitor import ProcessMonitor
            proc_monitor = ProcessMonitor()
            self._tasks.append(asyncio.create_task(
                proc_monitor.run(), name="proc_monitor"
            ))
        except Exception as e:
            log.error(f"ProcessMonitor failed to start: {e}", exc_info=True)

        try:
            from backend.monitor.file_watcher import FileWatcherMonitor
            file_watcher = FileWatcherMonitor()
            self._tasks.append(asyncio.create_task(
                file_watcher.run(), name="file_watcher"
            ))
        except Exception as e:
            log.error(f"FileWatcher failed to start: {e}", exc_info=True)

        try:
            from backend.ai.heuristic_engine import HeuristicEngine
            heuristic = HeuristicEngine()
            bus.subscribe("network.connection", heuristic.analyze_connection)
            bus.subscribe("process.new",        heuristic.analyze_process)
            bus.subscribe("file.event",         heuristic.analyze_file)
        except Exception as e:
            log.error(f"HeuristicEngine failed to start: {e}", exc_info=True)

        if self.settings.ai_enabled:
            try:
                from backend.ai.anomaly_detector import AnomalyDetector
                anomaly = AnomalyDetector()
                await anomaly.load_or_train()
                self._tasks.append(asyncio.create_task(
                    anomaly.run(), name="anomaly_detector"
                ))
            except Exception as e:
                log.error(f"AnomalyDetector failed to start: {e}", exc_info=True)

    async def _start_privileged_subsystems(self) -> None:
        """Subsystems requiring admin rights."""
        log.info("Starting privileged subsystems...")

        try:
            from backend.network.packet_capture import PacketCapture
            capture = PacketCapture()
            self._tasks.append(asyncio.create_task(
                capture.run(), name="packet_capture"
            ))
        except Exception as e:
            log.error(f"PacketCapture failed to start: {e}", exc_info=True)

        try:
            from backend.network.connection_tracker import ConnectionTracker
            tracker = ConnectionTracker()
            self._tasks.append(asyncio.create_task(
                tracker.run(), name="conn_tracker"
            ))
        except Exception as e:
            log.error(f"ConnectionTracker failed to start: {e}", exc_info=True)

        if self.settings.vpn_enabled:
            await self._start_vpn()

    async def _start_vpn(self) -> None:
        try:
            from backend.vpn.vpn_controller import VPNController
            vpn     = VPNController()
            success = await vpn.start()
            if success:
                self._tasks.append(asyncio.create_task(
                    vpn.run(), name="vpn_engine"
                ))
        except Exception as e:
            log.error(f"VPN failed to start: {e}", exc_info=True)

    async def stop(self) -> None:
        log.info("Shutting down SentinelX Core...")
        self._shutdown_event.set()

        try:
            from backend.vpn.vpn_controller import VPNController
            await VPNController.stop_global()
        except Exception:
            pass

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        bus.stop()
        log.info("Shutdown complete.")

    async def wait(self) -> None:
        await self._shutdown_event.wait()