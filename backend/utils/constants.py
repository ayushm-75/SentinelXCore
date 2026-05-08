# App-wide constants
# backend/utils/constants.py
from pathlib import Path

# ── Directories ───────────────────────────────────────────────
ROOT_DIR         = Path(__file__).resolve().parent.parent.parent
DATA_DIR         = ROOT_DIR / "data"
CONFIG_DIR       = ROOT_DIR / "config"
LOG_DIR          = ROOT_DIR / "logs"
BLOCKLIST_DIR    = DATA_DIR / "blocklists"
MODELS_DIR       = DATA_DIR / "models"
CAPTURES_DIR     = DATA_DIR / "captures"
SHARED_DIR       = ROOT_DIR / "shared"
RULES_DIR        = SHARED_DIR / "rules"

# Ensure dirs exist
for _d in [DATA_DIR, CONFIG_DIR, LOG_DIR, BLOCKLIST_DIR, MODELS_DIR, CAPTURES_DIR, RULES_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# ── Ports ─────────────────────────────────────────────────────
BACKEND_PORT     = 8765
WS_PORT          = 8766

# ── Timing ────────────────────────────────────────────────────
STATS_INTERVAL_SEC        = 2.0
PROCESS_SCAN_INTERVAL_SEC = 3.0
ALERT_CLEANUP_INTERVAL_SEC = 300.0
MODEL_RETRAIN_INTERVAL_SEC = 3600.0

# ── Network heuristic thresholds ──────────────────────────────
HIGH_FREQ_CONN_PER_MIN    = 60
HIGH_BYTES_OUT_PER_SEC    = 10 * 1024 * 1024   # 10 MB/s
SUSPICIOUS_PORT_LIST      = {
    23, 135, 137, 138, 139, 445, 1433, 3389,
    4444, 5900, 6666, 6667, 8080, 9001, 9030
}

# ── File heuristics ───────────────────────────────────────────
SUSPICIOUS_EXTENSIONS     = {
    ".exe", ".bat", ".cmd", ".vbs", ".ps1", ".js",
    ".jar", ".scr", ".pif", ".com", ".hta", ".msi",
    ".dll", ".sys", ".drv"
}
HIGH_ENTROPY_THRESHOLD    = 7.2   # bits per byte (packed/encrypted)
DOWNLOAD_WATCH_DIRS       = [
    Path.home() / "Downloads",
    Path.home() / "Desktop",
]

# ── Process heuristics ────────────────────────────────────────
TEMP_PATHS                = {"temp", "tmp", "appdata\\local\\temp"}
SUSPICIOUS_PROCESS_NAMES  = {
    "mimikatz", "pwdump", "netcat", "nc.exe",
    "meterpreter", "psexec", "wce.exe"
}

# ── AI ────────────────────────────────────────────────────────
MODEL_PATH                = MODELS_DIR / "isolation_forest.pkl"
SCALER_PATH               = MODELS_DIR / "scaler.pkl"
FEATURE_WINDOW_SIZE       = 100   # samples before first train
MIN_TRAIN_SAMPLES         = 50

# ── WinDivert ─────────────────────────────────────────────────
WINDIVERT_DIR             = ROOT_DIR / "windivert"
WINDIVERT_DLL_64          = WINDIVERT_DIR / "WinDivert64.sys"

# ── Severity levels ───────────────────────────────────────────
SEV_CRITICAL = "critical"
SEV_HIGH     = "high"
SEV_MEDIUM   = "medium"
SEV_LOW      = "low"
SEV_INFO     = "info"