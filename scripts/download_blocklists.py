# Standalone blocklist downloader script
# scripts/download_blocklists.py
"""
Standalone script to download all blocklists.
Run: python scripts/download_blocklists.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.vpn.blocklist_manager import BlocklistManager
from backend.core.logger import setup_logger

setup_logger()


async def main():
    print("Downloading all blocklists...")
    mgr = BlocklistManager()
    await mgr.download_all()
    print(f"Done. Total domains loaded: {len(mgr.trie):,}")


if __name__ == "__main__":
    asyncio.run(main())