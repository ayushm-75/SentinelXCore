# backend/protection/file_guard.py
"""
File guard — responds to file threat events.
Integrates with alert manager to surface file threats in the UI.
Provides quarantine capability (move file to safe location).
"""
import asyncio
import shutil
import time
from pathlib import Path
from typing import Optional
from backend.core.logger import get_logger
from backend.core.state import state, AlertEntry
from backend.core.event_bus import bus
from backend.utils.helpers import generate_alert_id
from backend.utils.constants import SEV_HIGH, SEV_CRITICAL

log = get_logger("file_guard")

QUARANTINE_DIR = Path("data/quarantine")


class FileGuard:

    def __init__(self):
        QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
        # Subscribe to file threat events
        bus.subscribe("file.threat", self._on_file_threat)

    async def _on_file_threat(self, event: dict) -> None:
        data = event.get("data", {})
        if not data:
            return

        path    = data.get("path", "")
        reasons = data.get("reasons", [])
        entropy = data.get("entropy", 0.0)
        sha256  = data.get("sha256", "")

        severity = SEV_CRITICAL if any(
            "PE header" in r or "encrypted" in r.lower()
            for r in reasons
        ) else SEV_HIGH

        alert = AlertEntry(
            alert_id=  generate_alert_id(),
            severity=  severity,
            category=  "file",
            title=     f"File Threat Detected: {Path(path).name}",
            detail=(
                f"Path: {path} | "
                f"Entropy: {entropy:.2f} | "
                f"Reasons: {'; '.join(reasons)} | "
                f"SHA256: {sha256[:16]}..."
                if sha256 else ""
            ),
        )

        await state.add_alert(alert)
        log.warning(f"File threat: {path} — {reasons}")

    async def quarantine_file(self, file_path: str) -> dict:
        """
        Move a suspicious file to the quarantine directory.
        Returns result dict.
        """
        src = Path(file_path)
        if not src.exists():
            return {"success": False, "error": "File not found"}

        try:
            timestamp  = int(time.time())
            dest_name  = f"{timestamp}_{src.name}"
            dest       = QUARANTINE_DIR / dest_name
            shutil.move(str(src), str(dest))

            log.warning(f"Quarantined: {src} → {dest}")

            await bus.publish("file.quarantined", {
                "original_path":   str(src),
                "quarantine_path": str(dest),
                "timestamp":       time.time(),
            })

            return {"success": True, "quarantine_path": str(dest)}

        except PermissionError:
            return {"success": False, "error": "Permission denied — file may be in use"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def delete_file(self, file_path: str) -> dict:
        """Permanently delete a threat file."""
        src = Path(file_path)
        if not src.exists():
            return {"success": False, "error": "File not found"}
        try:
            src.unlink()
            log.warning(f"Deleted threat file: {src}")
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_quarantine(self) -> list:
        """List all quarantined files."""
        try:
            return [
                {
                    "name":     f.name,
                    "path":     str(f),
                    "size_mb":  round(f.stat().st_size / 1024 / 1024, 2),
                    "modified": f.stat().st_mtime,
                }
                for f in QUARANTINE_DIR.iterdir()
                if f.is_file()
            ]
        except Exception:
            return []