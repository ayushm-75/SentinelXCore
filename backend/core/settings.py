# backend/core/settings.py
import json
import sys
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

# ── Resolve paths relative to exe or source root ──────────────
if getattr(sys, 'frozen', False):
    # Frozen exe — use directory next to the .exe
    _BASE = Path(sys.executable).parent
else:
    # Dev — use project root
    _BASE = Path(__file__).resolve().parent.parent.parent

CONFIG_PATH  = _BASE / "config" / "app_config.json"
_SETTINGS_BASE = _BASE  # expose for other modules that need the base path


class AppSettings(BaseModel):
    model_config = {"protected_namespaces": ()}

    app_name:             str        = "SentinelX Core"
    version:              str        = "1.0.0"
    backend_host:         str        = "127.0.0.1"
    backend_port:         int        = 8765
    ws_port:              int        = 8766
    log_level:            str        = "INFO"
    ai_enabled:           bool       = True
    anomaly_threshold:    float      = 0.65
    vpn_enabled:          bool       = False
    active_filter_lists:  List[str]  = ["adguard", "easylist", "easyprivacy", "hagezi"]
    ignored_alerts:       List[str]  = []
    custom_block_domains: List[str]  = []
    custom_allow_domains: List[str]  = []
    background_mode:      bool       = False
    overlay_hotkey:       str        = "ctrl+shift+s"
    theme:                str        = "dark"


def load_settings() -> AppSettings:
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
            return AppSettings(**data)
        except Exception as e:
            from backend.core.logger import get_logger
            get_logger("settings").warning(
                f"Failed to load config from {CONFIG_PATH}: {e}. Using defaults."
            )
    return AppSettings()


def save_settings(settings: AppSettings) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(), f, indent=2)


def update_settings(updates: dict) -> AppSettings:
    current = load_settings()
    data    = current.model_dump()
    data.update(updates)
    updated = AppSettings(**data)
    save_settings(updated)
    return updated


_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reload_settings() -> AppSettings:
    global _settings
    _settings = load_settings()
    return _settings