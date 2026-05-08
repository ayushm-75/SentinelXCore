# Multi-format parser
# backend/vpn/blocklist_parser.py
"""
Multi-format blocklist parser.

Handles:
1. AdGuard / Hagezi format  → ||domain.com^
2. EasyList / AdBlock Plus  → ||domain.com^  (same anchor syntax but also URL patterns)
3. Hosts file format        → 0.0.0.0 domain.com  /  127.0.0.1 domain.com
4. Plain domain list        → domain.com (one per line)

Strategy:
- PRIMARY: Extract domains from ||domain.com^ patterns (all formats use this)
- SECONDARY: Extract from hosts-file patterns
- SKIP:  URL path patterns (/banner.jpg), element hiding (##+js), etc.
- Result: Pure set of blocked domain strings (lowercase, stripped)
"""
import re
from typing import Iterator, Set
from backend.core.logger import get_logger

log = get_logger("blocklist_parser")

# ── Compiled regexes ──────────────────────────────────────────
# Matches: ||domain.tld^  or  ||domain.tld^$options
_RE_ADGUARD_DOMAIN = re.compile(
    r"^\|\|([a-zA-Z0-9](?:[a-zA-Z0-9\-\.]*[a-zA-Z0-9])?)\^",
    re.ASCII
)

# Matches: ||*.domain.tld^ (wildcard prefix)
_RE_ADGUARD_WILDCARD = re.compile(
    r"^\|\|\*\.([a-zA-Z0-9](?:[a-zA-Z0-9\-\.]*[a-zA-Z0-9])?)\^",
    re.ASCII
)

# Matches hosts file: 0.0.0.0 domain.com or 127.0.0.1 domain.com
_RE_HOSTS = re.compile(
    r"^(?:0\.0\.0\.0|127\.0\.0\.1)\s+([a-zA-Z0-9](?:[a-zA-Z0-9\-\.]*[a-zA-Z0-9])?)\s*$",
    re.ASCII
)

# Plain domain (no spaces, no special chars, has a dot)
_RE_PLAIN_DOMAIN = re.compile(
    r"^([a-zA-Z0-9](?:[a-zA-Z0-9\-\.]*[a-zA-Z0-9])?)\s*$",
    re.ASCII
)

# Invalid TLDs / single labels to skip
_SKIP_DOMAINS = frozenset({"localhost", "local", "broadcasthost", "ip6-localhost"})


def _is_valid_domain(domain: str) -> bool:
    """Basic validation: must have at least one dot, valid chars, reasonable length."""
    if not domain or len(domain) > 253 or "." not in domain:
        return False
    if domain in _SKIP_DOMAINS:
        return False
    # Must not start/end with dot or hyphen
    if domain[0] in ".-" or domain[-1] in ".-":
        return False
    # All labels must be valid
    for label in domain.split("."):
        if not label or len(label) > 63:
            return False
        if label[0] == "-" or label[-1] == "-":
            return False
    return True


def parse_lines(lines: Iterator[str], list_format: str = "auto") -> Iterator[str]:
    """
    Parse lines from a blocklist file and yield valid domain strings.

    Args:
        lines:       Iterator of raw text lines
        list_format: "adguard" | "adblock" | "hosts" | "plain" | "auto"
    """
    for raw in lines:
        line = raw.strip()

        # ── Skip empty, comments, metadata ────────────────────
        if not line:
            continue
        if line.startswith("!") or line.startswith("#"):
            continue
        if line.startswith("[Adblock"):
            continue
        if line.startswith(";"):
            continue

        # ── Element hiding / script injection rules ────────────
        if "##" in line or "#?#" in line or "#@#" in line:
            continue

        # ── Exception rules (whitelist) — skip ────────────────
        if line.startswith("@@"):
            continue

        # ── Try AdGuard/AdBlock domain anchor: ||domain.com^ ──
        m = _RE_ADGUARD_DOMAIN.match(line)
        if m:
            domain = m.group(1).lower()
            if _is_valid_domain(domain):
                yield domain
            continue

        # ── Wildcard: ||*.domain.com^ ─────────────────────────
        m = _RE_ADGUARD_WILDCARD.match(line)
        if m:
            domain = m.group(1).lower()
            if _is_valid_domain(domain):
                yield domain
            continue

        # ── Hosts file: 0.0.0.0 domain.com ───────────────────
        m = _RE_HOSTS.match(line)
        if m:
            domain = m.group(1).lower()
            if _is_valid_domain(domain):
                yield domain
            continue

        # ── URL pattern rules — skip (not DNS-level) ──────────
        # These start with patterns like: -ad-, /banner, &rb=, etc.
        if (
            line.startswith("/") or
            line.startswith("&") or
            line.startswith("-") or
            line.startswith(".") or
            line.startswith("*") or
            "=" in line[:5] or
            "$" in line[:10]
        ):
            continue

        # ── Plain domain list (last resort) ───────────────────
        if list_format in ("plain", "auto") and "." in line and " " not in line:
            m = _RE_PLAIN_DOMAIN.match(line)
            if m:
                domain = m.group(1).lower()
                if _is_valid_domain(domain):
                    yield domain


def parse_file(filepath: str, list_format: str = "auto") -> Set[str]:
    """Parse an entire file and return set of domains."""
    domains: Set[str] = set()
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for domain in parse_lines(f, list_format):
                domains.add(domain)
        log.debug(f"Parsed {len(domains):,} domains from {filepath}")
    except FileNotFoundError:
        log.warning(f"Blocklist file not found: {filepath}")
    except Exception as e:
        log.error(f"Parse error on {filepath}: {e}")
    return domains