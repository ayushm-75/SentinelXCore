# Static heuristic rules definitions
# backend/ai/rules.py
"""
Static heuristic rule definitions.
Each rule is a dict with:
  - id:         unique identifier
  - name:       human-readable name
  - severity:   critical | high | medium | low
  - category:   network | process | file
  - description: what it detects
  - enabled:    bool
"""

NETWORK_RULES = [
    {
        "id": "NET_001",
        "name": "High-Frequency Outbound Connections",
        "severity": "high",
        "category": "network",
        "description": "Process making more than 60 outbound connections per minute",
        "enabled": True,
    },
    {
        "id": "NET_002",
        "name": "Suspicious Port Usage",
        "severity": "high",
        "category": "network",
        "description": "Connection on known suspicious port (4444, 6666, 9001, etc.)",
        "enabled": True,
    },
    {
        "id": "NET_003",
        "name": "Unknown Domain Repeated Access",
        "severity": "medium",
        "category": "network",
        "description": "New unrecognized domain accessed >10 times in 60 seconds",
        "enabled": True,
    },
    {
        "id": "NET_004",
        "name": "High Outbound Data Volume",
        "severity": "high",
        "category": "network",
        "description": "Process sending >10MB/s outbound — possible data exfiltration",
        "enabled": True,
    },
    {
        "id": "NET_005",
        "name": "DNS over Non-Standard Port",
        "severity": "medium",
        "category": "network",
        "description": "DNS query not on port 53 — possible DNS tunneling",
        "enabled": True,
    },
    {
        "id": "NET_006",
        "name": "Tor / Anonymous Network",
        "severity": "critical",
        "category": "network",
        "description": "Connection to known Tor ports (9001, 9030) or Tor exit nodes",
        "enabled": True,
    },
    {
        "id": "NET_007",
        "name": "Excessive Unique Domain Queries",
        "severity": "medium",
        "category": "network",
        "description": "Process querying >50 unique domains — possible DGA activity",
        "enabled": True,
    },
]

PROCESS_RULES = [
    {
        "id": "PROC_001",
        "name": "Process from Temp Directory",
        "severity": "high",
        "category": "process",
        "description": "Executable running from TEMP, TMP, or AppData\\Local\\Temp",
        "enabled": True,
    },
    {
        "id": "PROC_002",
        "name": "Known Malicious Process Name",
        "severity": "critical",
        "category": "process",
        "description": "Process name matches known attack tool (mimikatz, netcat, etc.)",
        "enabled": True,
    },
    {
        "id": "PROC_003",
        "name": "PowerShell with Encoded Command",
        "severity": "high",
        "category": "process",
        "description": "PowerShell launched with -EncodedCommand or -enc flag",
        "enabled": True,
    },
    {
        "id": "PROC_004",
        "name": "Script Interpreter Spawned by Browser",
        "severity": "high",
        "category": "process",
        "description": "cmd.exe / powershell.exe spawned by browser process",
        "enabled": True,
    },
    {
        "id": "PROC_005",
        "name": "Abnormal Memory Usage",
        "severity": "medium",
        "category": "process",
        "description": "Process using >1GB RAM unexpectedly",
        "enabled": True,
    },
    {
        "id": "PROC_006",
        "name": "Hidden / No Window Process",
        "severity": "medium",
        "category": "process",
        "description": "Process with no window handle and high network activity",
        "enabled": True,
    },
    {
        "id": "PROC_007",
        "name": "Double Extension Executable",
        "severity": "high",
        "category": "process",
        "description": "Executable with double extension (e.g., invoice.pdf.exe)",
        "enabled": True,
    },
]

FILE_RULES = [
    {
        "id": "FILE_001",
        "name": "High Entropy File",
        "severity": "medium",
        "category": "file",
        "description": "File entropy >7.2 bits/byte — likely packed or encrypted",
        "enabled": True,
    },
    {
        "id": "FILE_002",
        "name": "Suspicious Extension in Download",
        "severity": "high",
        "category": "file",
        "description": "Executable extension found in Downloads folder",
        "enabled": True,
    },
    {
        "id": "FILE_003",
        "name": "PE Header in Non-Executable",
        "severity": "critical",
        "category": "file",
        "description": "MZ/PE header found in file with non-executable extension",
        "enabled": True,
    },
    {
        "id": "FILE_004",
        "name": "PowerShell Script in Download",
        "severity": "high",
        "category": "file",
        "description": ".ps1 file downloaded — review before executing",
        "enabled": True,
    },
]

ALL_RULES = NETWORK_RULES + PROCESS_RULES + FILE_RULES
RULES_BY_ID = {r["id"]: r for r in ALL_RULES}