# Entropy + extension checks
# backend/monitor/file_scanner.py
"""
On-demand file scanner (complements watchdog monitoring).
Can scan arbitrary files or directories.
"""
import asyncio
from pathlib import Path
from typing import List, Dict
from backend.core.logger import get_logger
from backend.utils.crypto import check_file_threat

log = get_logger("file_scanner")


class FileScanner:

    async def scan_file(self, path: str) -> dict:
        p = Path(path)
        if not p.exists():
            return {"error": "File not found", "path": path}
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: check_file_threat(p))
        return result

    async def scan_directory(self, directory: str, max_files: int = 100) -> List[dict]:
        d = Path(directory)
        if not d.is_dir():
            return [{"error": "Not a directory"}]

        files = list(d.iterdir())[:max_files]
        tasks = [self.scan_file(str(f)) for f in files if f.is_file()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        output = []
        for r in results:
            if isinstance(r, Exception):
                output.append({"error": str(r)})
            else:
                output.append(r)
        return output