# Filter list URLs + metadata
# backend/vpn/filter_lists.py
"""Filter list metadata and URL definitions."""

FILTER_LISTS = {
    "adguard": {
        "name":        "AdGuard DNS Filter",
        "url":         "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
        "format":      "adguard",
        "description": "Composed filter optimized for DNS-level ad blocking",
        "enabled":     True,
    },
    "easylist": {
        "name":        "EasyList",
        "url":         "https://easylist.to/easylist/easylist.txt",
        "format":      "adblock",
        "description": "Primary ad blocking filter list",
        "enabled":     True,
    },
    "easyprivacy": {
        "name":        "EasyPrivacy",
        "url":         "https://easylist.to/easylist/easyprivacy.txt",
        "format":      "adblock",
        "description": "Anti-tracking and privacy protection",
        "enabled":     True,
    },
    "hagezi": {
        "name":        "HaGeZi Pro++ DNS Blocklist",
        "url":         "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/adblock/pro.plus.txt",
        "format":      "adguard",
        "description": "Aggressive: Ads, tracking, phishing, malware, scam",
        "enabled":     True,
    },
}