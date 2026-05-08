# backend/monitor/file_watcher.py
import asyncio
import time
from pathlib import Path
from typing import List, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from backend.core.logger import get_logger
from backend.core.event_bus import bus
from backend.utils.constants import DOWNLOAD_WATCH_DIRS
from backend.utils.crypto import check_file_threat

log = get_logger("file_watcher")


class SentinelFileHandler(FileSystemEventHandler):
    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self._queue = queue
        self._loop  = loop
        super().__init__()

    def _queue_event(self, event_type: str, src_path: str) -> None:
        try:
            self._loop.call_soon_threadsafe(
                self._queue.put_nowait,
                {"type": event_type, "path": src_path, "timestamp": time.time()}
            )
        except Exception:
            pass

    def on_created(self, event):
        if not event.is_directory:
            self._queue_event("created", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._queue_event("modified", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._queue_event("moved", event.dest_path)


class FileWatcherMonitor:

    def __init__(self):
        # Use Any annotation to avoid pyright/pylance type variable error
        self._observer: Any = Observer()
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._watched_dirs: List[Path] = []

    async def run(self) -> None:
        loop    = asyncio.get_event_loop()
        handler = SentinelFileHandler(self._queue, loop)

        for watch_dir in DOWNLOAD_WATCH_DIRS:
            if watch_dir.exists():
                try:
                    self._observer.schedule(handler, str(watch_dir), recursive=False)
                    self._watched_dirs.append(watch_dir)
                    log.info(f"Watching: {watch_dir}")
                except Exception as e:
                    log.warning(f"Cannot watch {watch_dir}: {e}")

        if not self._watched_dirs:
            log.warning("No directories to watch.")
            return

        self._observer.start()
        log.info("File watcher started.")

        try:
            while True:
                try:
                    event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                    await self._process_event(event)
                    self._queue.task_done()
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
        finally:
            self._observer.stop()
            self._observer.join()
            log.info("File watcher stopped.")

    async def _process_event(self, event: dict) -> None:
        path = Path(event["path"])
        await bus.publish("file.event", {
            "type":      event["type"],
            "path":      str(path),
            "timestamp": event["timestamp"],
        })
        if event["type"] in ("created", "moved") and path.exists():
            await self._scan_file(path)

    async def _scan_file(self, path: Path) -> None:
        try:
            loop   = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: check_file_threat(path))
            await bus.publish("file.scanned", result)
            if result["suspicious"]:
                log.warning(f"Suspicious file: {path.name} — {result['reasons']}")
                await bus.publish("file.threat", {
                    "path":    str(path),
                    "reasons": result["reasons"],
                    "entropy": result["entropy"],
                    "sha256":  result["sha256"],
                    "severity": "high",
                })
        except Exception as e:
            log.debug(f"File scan error for {path}: {e}")