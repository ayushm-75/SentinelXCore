# backend/vpn/blocklist_manager.py
import asyncio
import json
import time
from pathlib import Path
from typing import List, Optional, Set
import aiofiles
import requests

from backend.vpn.domain_trie import DomainTrie
from backend.vpn.blocklist_parser import parse_file
from backend.vpn.filter_lists import FILTER_LISTS
from backend.core.logger import get_logger
from backend.core.state import state
from backend.core.settings import get_settings
from backend.utils.constants import BLOCKLIST_DIR

log = get_logger("blocklist_manager")

META_PATH = Path("config/filter_lists_meta.json")

# ── Module-level shared state ─────────────────────────────────
_trie: Optional[DomainTrie] = None
_custom_block: Set[str] = set()
_custom_allow: Set[str] = set()

# ── SYSTEM WHITELIST ──────────────────────────────────────────
# These domains must NEVER be blocked — they are essential for
# Windows, browsers, fonts, and the app itself to function.
SYSTEM_WHITELIST: Set[str] = {
    # Google Fonts & APIs (used by our own frontend)
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "ajax.googleapis.com",

    # Windows Update & core services
    "windowsupdate.com",
    "update.microsoft.com",
    "download.microsoft.com",
    "microsoft.com",
    "microsoftonline.com",
    "live.com",
    "outlook.com",
    "office.com",
    "office365.com",

    # Windows telemetry — we allow basic ones to not break Windows
    # (user can add to custom_block if they want)
    "ctldl.windowsupdate.com",
    "time.windows.com",
    "login.microsoftonline.com",

    # Browser update / safe browsing (keeps browser secure)
    "safebrowsing.googleapis.com",
    "clients1.google.com",
    "clients2.google.com",
    "clients3.google.com",
    "clients4.google.com",
    "beacons.gvt2.com",          # Chrome update beacon — unblock
    "update.googleapis.com",
    "accounts.google.com",

    # DNS-over-HTTPS / system DNS
    "dns.google",
    "cloudflare-dns.com",
    "one.one.one.one",

    # Certificate validation (OCSP) — breaking this breaks HTTPS
    "ocsp.digicert.com",
    "ocsp.pki.goog",
    "crl.microsoft.com",
    "status.geotrust.com",
    "ocsp.godaddy.com",
    "ocsp.sectigo.com",
    "ocsp.usertrust.com",
    "ocsp.comodoca.com",

    # NTP
    "pool.ntp.org",
    "time.cloudflare.com",

    # Our own backend (never block ourselves)
    "localhost",
    "127.0.0.1",
}


def get_trie() -> DomainTrie:
    global _trie
    if _trie is None:
        _trie = DomainTrie(wildcard_root=True)
    return _trie


class BlocklistManager:

    def __init__(self):
        self.trie = get_trie()

    # ── Public API ────────────────────────────────────────────

    def is_blocked(self, domain: str) -> bool:
        """
        Check if domain should be blocked.
        Priority order:
        1. System whitelist (never block)
        2. Custom allow list (user whitelist)
        3. Custom block list (user blacklist)
        4. Main blocklist trie
        """
        if not domain:
            return False

        domain = domain.lower().strip().rstrip(".")

        # 1. System whitelist — ALWAYS allow
        if self._is_whitelisted(domain):
            return False

        # 2. Custom allow list
        if domain in _custom_allow:
            return False

        # 3. Custom block list
        if domain in _custom_block:
            return True

        # 4. Main trie
        return self.trie.contains(domain)

    def _is_whitelisted(self, domain: str) -> bool:
        """Check domain against system whitelist (exact + suffix match)."""
        if domain in SYSTEM_WHITELIST:
            return True
        # Check if domain is a subdomain of a whitelisted domain
        for white in SYSTEM_WHITELIST:
            if domain.endswith("." + white) or domain == white:
                return True
        return False

    async def load_lists(self, active_lists: Optional[List[str]] = None) -> None:
        """Load specified lists into trie (rebuild trie from scratch)."""
        settings = get_settings()

        # CRITICAL FIX: Use passed active_lists OR load from saved settings
        # Never fall back to all lists
        if active_lists is not None:
            lists_to_load = active_lists
        else:
            lists_to_load = settings.active_filter_lists

        log.info(f"Loading blocklists: {lists_to_load}")
        start = time.time()

        # Rebuild trie
        global _trie
        _trie = DomainTrie(wildcard_root=True)
        self.trie = _trie

        total = 0
        for list_id in lists_to_load:
            if list_id not in FILTER_LISTS:
                log.warning(f"Unknown list id: {list_id}")
                continue

            file_path = BLOCKLIST_DIR / f"{list_id}.txt"
            if not file_path.exists():
                log.warning(f"List not downloaded yet: {list_id}. Run download first.")
                continue

            fmt = FILTER_LISTS[list_id]["format"]
            domains = parse_file(str(file_path), fmt)
            count = self.trie.bulk_insert(iter(domains))
            total += count
            log.info(f"  [{list_id}] loaded {count:,} domains")

        self._load_custom_domains()

        elapsed = time.time() - start
        state.blocklist_loaded       = True
        state.blocklist_domain_count = len(self.trie)

        log.info(f"Blocklist ready: {len(self.trie):,} unique domains in {elapsed:.2f}s")

    def _load_custom_domains(self) -> None:
        global _custom_block, _custom_allow
        settings = get_settings()
        _custom_block = set(d.lower() for d in settings.custom_block_domains)
        _custom_allow = set(d.lower() for d in settings.custom_allow_domains)
        for d in _custom_block:
            self.trie.insert(d)
        log.debug(f"Custom rules: {len(_custom_block)} block, {len(_custom_allow)} allow")

    async def download_all(self) -> None:
        settings = get_settings()
        tasks = [self._download_one(list_id, meta) for list_id, meta in FILTER_LISTS.items()]
        await asyncio.gather(*tasks, return_exceptions=True)
        await self.load_lists(settings.active_filter_lists)

    async def download_active(self) -> None:
        settings = get_settings()
        tasks = [
            self._download_one(list_id, FILTER_LISTS[list_id])
            for list_id in settings.active_filter_lists
            if list_id in FILTER_LISTS
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _download_one(self, list_id: str, meta: dict) -> None:
        url      = meta["url"]
        out_path = BLOCKLIST_DIR / f"{list_id}.txt"

        log.info(f"Downloading [{list_id}]: {url}")
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(
                    url, timeout=60,
                    headers={"User-Agent": "SentinelX/1.0"},
                )
            )
            response.raise_for_status()

            async with aiofiles.open(out_path, "w", encoding="utf-8", errors="replace") as f:
                await f.write(response.text)

            fmt          = meta["format"]
            domain_count = len(parse_file(str(out_path), fmt))
            await self._update_meta(list_id, domain_count)
            log.info(f"  [{list_id}] downloaded {domain_count:,} domains → {out_path.name}")

        except Exception as e:
            log.error(f"  [{list_id}] download failed: {e}")

    async def _update_meta(self, list_id: str, count: int) -> None:
        meta = {}
        if META_PATH.exists():
            try:
                with open(META_PATH, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except Exception:
                pass

        if list_id not in meta:
            meta[list_id] = {}

        meta[list_id]["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        meta[list_id]["entry_count"]  = count

        META_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    async def auto_update_loop(self, interval_hours: int = 24) -> None:
        while True:
            await asyncio.sleep(interval_hours * 3600)
            log.info("Auto-updating blocklists...")
            await self.download_active()