# Entropy calculation etc.
# backend/utils/crypto.py
"""Crypto/entropy utilities for file scanning."""
import math
from collections import Counter
from pathlib import Path
from typing import Optional, Tuple


ENTROPY_BANDS = [
    (0.0, 1.0, "very_low",    "Likely all-zero or constant data"),
    (1.0, 3.5, "low",         "Plain text / source code"),
    (3.5, 6.0, "medium",      "Binary with strings"),
    (6.0, 7.2, "high",        "Compressed or compiled"),
    (7.2, 8.0, "very_high",   "Encrypted or packed — SUSPICIOUS"),
]


def classify_entropy(entropy: float) -> Tuple[str, str]:
    for lo, hi, label, desc in ENTROPY_BANDS:
        if lo <= entropy < hi:
            return label, desc
    return "very_high", "Encrypted or packed — SUSPICIOUS"


def check_file_threat(path: Path) -> dict:
    """
    Full file threat assessment:
    - Entropy score
    - Extension check
    - Embedded PE header
    - Script signatures
    """
    from backend.utils.constants import SUSPICIOUS_EXTENSIONS, HIGH_ENTROPY_THRESHOLD
    from backend.utils.helpers import file_entropy, sha256_file

    result = {
        "path": str(path),
        "suspicious": False,
        "reasons": [],
        "entropy": 0.0,
        "entropy_label": "",
        "sha256": None,
    }

    if not path.exists():
        return result

    # Extension check
    if path.suffix.lower() in SUSPICIOUS_EXTENSIONS:
        result["suspicious"] = True
        result["reasons"].append(f"Suspicious extension: {path.suffix}")

    # Entropy
    entropy = file_entropy(path)
    result["entropy"] = entropy
    label, _ = classify_entropy(entropy)
    result["entropy_label"] = label

    if entropy > HIGH_ENTROPY_THRESHOLD:
        result["suspicious"] = True
        result["reasons"].append(f"High entropy ({entropy:.2f}) — possible packing/encryption")

    # PE header check (MZ magic bytes)
    try:
        with open(path, "rb") as f:
            header = f.read(2)
        if header == b"MZ":
            result["reasons"].append("PE executable (MZ header)")
            if path.suffix.lower() not in {".exe", ".dll", ".sys", ".drv"}:
                result["suspicious"] = True
                result["reasons"].append("PE header in non-executable extension — VERY SUSPICIOUS")
    except Exception:
        pass

    # Script signatures
    try:
        if path.stat().st_size < 1024 * 1024:  # Only scan files < 1MB
            content = path.read_bytes()
            script_sigs = [
                (b"powershell", "PowerShell content"),
                (b"cmd.exe",    "CMD reference"),
                (b"WScript",    "WScript reference"),
                (b"eval(",      "eval() call — obfuscation risk"),
                (b"base64",     "Base64 encoding reference"),
            ]
            for sig, label in script_sigs:
                if sig.lower() in content.lower():
                    result["reasons"].append(label)
    except Exception:
        pass

    # Hash
    result["sha256"] = sha256_file(path)

    return result