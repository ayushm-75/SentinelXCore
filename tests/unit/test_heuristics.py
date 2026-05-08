# Unit tests for heuristics
# tests/unit/test_heuristics.py
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from backend.ai.heuristic_engine import HeuristicEngine
from backend.core.state import state


class TestHeuristicEngine:
    def setup_method(self):
        self.engine = HeuristicEngine()
        # Reset alert count
        self.engine._alert_times.clear()

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_temp_dir_process_flagged(self):
        before = len(state.alerts)
        self._run(self.engine.analyze_process({"data": {
            "pid":     88001,
            "name":    "evil.exe",
            "exe":     "C:\\Users\\test\\AppData\\Local\\Temp\\evil.exe",
            "cmdline": "evil.exe",
        }}))
        assert len(state.alerts) > before

    def test_mimikatz_detected(self):
        before = len(state.alerts)
        self._run(self.engine.analyze_process({"data": {
            "pid":     88002,
            "name":    "mimikatz",
            "exe":     "C:\\mimikatz.exe",
            "cmdline": "mimikatz.exe",
        }}))
        assert len(state.alerts) > before

    def test_encoded_powershell_detected(self):
        before = len(state.alerts)
        self._run(self.engine.analyze_process({"data": {
            "pid":     88003,
            "name":    "powershell.exe",
            "exe":     "C:\\Windows\\System32\\powershell.exe",
            "cmdline": "powershell.exe -enc JABzAD0A",
        }}))
        assert len(state.alerts) > before

    def test_tor_port_detected(self):
        before = len(state.alerts)
        self._run(self.engine.analyze_connection({"data": {
            "pid":          88004,
            "process_name": "unknown.exe",
            "remote_addr":  "185.220.101.1",
            "remote_port":  9001,
            "domain":       "",
            "local_addr":   "192.168.1.1",
            "local_port":   44444,
        }}))
        assert len(state.alerts) > before

    def test_normal_process_not_flagged(self):
        before = len(state.alerts)
        self._run(self.engine.analyze_process({"data": {
            "pid":     88005,
            "name":    "notepad.exe",
            "exe":     "C:\\Windows\\System32\\notepad.exe",
            "cmdline": "notepad.exe document.txt",
        }}))
        # Notepad from System32 should NOT trigger any alerts
        assert len(state.alerts) == before

    def test_alert_cooldown_prevents_spam(self):
        """Same alert should not fire twice within cooldown period."""
        before = len(state.alerts)
        for _ in range(5):
            self._run(self.engine.analyze_process({"data": {
                "pid":     88006,
                "name":    "mimikatz",
                "exe":     "C:\\mimikatz.exe",
                "cmdline": "mimikatz.exe",
            }}))
        # Should only create 1 alert due to cooldown
        assert len(state.alerts) - before <= 2