# backend/network/geo_lookup.py
"""
Offline IP geolocation using IP range classification.

Since we have NO external APIs and must run offline,
we implement a lightweight approach:
1. Classify IPs into known ranges (private, CDN, cloud, etc.)
2. Use ASN prefix tables embedded in code for major providers
3. For truly unknown IPs: return "Unknown"

This is intentionally minimal — real GeoIP DBs (MaxMind) require
external downloads. We provide a self-contained offline solution.

For production upgrade: drop in maxminddb library + GeoLite2-City.mmdb
"""
import ipaddress
from typing import Optional, Dict, Tuple
from backend.core.logger import get_logger

log = get_logger("geo_lookup")


# ── Known IP range → (org, country) ──────────────────────────
# Major CDN/Cloud providers — covers most common traffic
_KNOWN_RANGES: list = [
    # Format: (network_cidr, organization, country_code)
    # Cloudflare
    ("1.1.1.0/24",       "Cloudflare DNS",       "US"),
    ("1.0.0.0/24",       "Cloudflare DNS",       "AU"),
    ("104.16.0.0/12",    "Cloudflare CDN",        "US"),
    ("172.64.0.0/13",    "Cloudflare CDN",        "US"),
    ("198.41.128.0/17",  "Cloudflare CDN",        "US"),
    # Google
    ("8.8.8.0/24",       "Google DNS",            "US"),
    ("8.8.4.0/24",       "Google DNS",            "US"),
    ("142.250.0.0/15",   "Google Services",       "US"),
    ("172.217.0.0/16",   "Google Services",       "US"),
    ("216.58.0.0/16",    "Google Services",       "US"),
    ("74.125.0.0/16",    "Google Services",       "US"),
    # Amazon AWS
    ("52.0.0.0/8",       "Amazon AWS",            "US"),
    ("54.0.0.0/8",       "Amazon AWS",            "US"),
    ("18.0.0.0/8",       "Amazon AWS",            "US"),
    ("3.0.0.0/8",        "Amazon AWS",            "US"),
    # Microsoft Azure
    ("13.64.0.0/11",     "Microsoft Azure",       "US"),
    ("40.112.0.0/13",    "Microsoft Azure",       "US"),
    ("52.224.0.0/11",    "Microsoft Azure",       "US"),
    ("20.0.0.0/8",       "Microsoft Azure",       "US"),
    # Akamai
    ("23.32.0.0/11",     "Akamai CDN",            "US"),
    ("104.64.0.0/10",    "Akamai CDN",            "US"),
    # Fastly
    ("151.101.0.0/16",   "Fastly CDN",            "US"),
    ("199.232.0.0/16",   "Fastly CDN",            "US"),
    # Facebook/Meta
    ("157.240.0.0/16",   "Meta/Facebook",         "US"),
    ("31.13.24.0/21",    "Meta/Facebook",         "IE"),
    # Tor (known exit ranges — approximate)
    ("185.220.0.0/16",   "Tor Exit Node",         "DE"),
    ("199.87.154.0/24",  "Tor Exit Node",         "CA"),
]

# Pre-compiled network objects for fast lookup
_COMPILED_RANGES: list = []

def _build_ranges() -> None:
    global _COMPILED_RANGES
    _COMPILED_RANGES = []
    for cidr, org, country in _KNOWN_RANGES:
        try:
            net = ipaddress.IPv4Network(cidr, strict=False)
            _COMPILED_RANGES.append((net, org, country))
        except Exception:
            pass

_build_ranges()


def classify_ip(ip: str) -> Dict[str, str]:
    """
    Classify an IP address.
    Returns: {org, country, type, is_private, is_known}
    """
    result = {
        "ip":         ip,
        "org":        "Unknown",
        "country":    "??",
        "type":       "unknown",
        "is_private": False,
        "is_known":   False,
    }

    try:
        addr = ipaddress.IPv4Address(ip)
    except ValueError:
        try:
            addr = ipaddress.IPv6Address(ip)
            result["type"] = "ipv6"
            return result
        except ValueError:
            return result

    # Private / special ranges
    if addr.is_private:
        result["is_private"] = True
        result["type"]       = "private"
        result["org"]        = "Local Network"
        result["country"]    = "LAN"
        return result

    if addr.is_loopback:
        result["is_private"] = True
        result["type"]       = "loopback"
        result["org"]        = "Localhost"
        result["country"]    = "LAN"
        return result

    if addr.is_link_local:
        result["is_private"] = True
        result["type"]       = "link_local"
        return result

    # Check known ranges
    for net, org, country in _COMPILED_RANGES:
        if addr in net:
            result["org"]      = org
            result["country"]  = country
            result["type"]     = "known_provider"
            result["is_known"] = True

            # Flag Tor
            if "Tor" in org:
                result["type"] = "tor_exit"
            return result

    # Unknown public IP
    result["type"] = "public_unknown"
    return result


def is_tor_exit(ip: str) -> bool:
    return classify_ip(ip).get("type") == "tor_exit"


def get_ip_info(ip: str) -> Dict[str, str]:
    """Public API — returns geo/org info for display."""
    return classify_ip(ip)