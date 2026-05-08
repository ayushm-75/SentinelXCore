# backend/core/logger.py
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Resolve log directory ──────────────────────────────────────
if getattr(sys, 'frozen', False):
    _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).resolve().parent.parent.parent

LOG_DIR = _BASE / "logs"
try:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    LOG_DIR = Path("logs")
    LOG_DIR.mkdir(exist_ok=True)

_IS_FROZEN = getattr(sys, 'frozen', False)

# Suppress uvicorn log config conflicts
logging.getLogger("uvicorn").propagate        = False
logging.getLogger("uvicorn.access").propagate = False
logging.getLogger("uvicorn.error").propagate  = False
logging.getLogger("uvicorn.asgi").propagate   = False


def setup_logger(name: str = "sentinelx", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # ── Console handler — skip in frozen exe (no stdout) ──────
    _stdout_ok = (
        not _IS_FROZEN and
        sys.stdout is not None and
        hasattr(sys.stdout, 'write')
    )

    if _stdout_ok:
        try:
            import colorlog
            ch = colorlog.StreamHandler(sys.stdout)
            ch.setFormatter(colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s [%(levelname)-8s] %(name)s: %(message)s%(reset)s",
                datefmt="%H:%M:%S",
                log_colors={
                    "DEBUG":    "cyan",
                    "INFO":     "green",
                    "WARNING":  "yellow",
                    "ERROR":    "red",
                    "CRITICAL": "bold_red",
                },
            ))
        except ImportError:
            ch = logging.StreamHandler(sys.stdout)
            ch.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            ))
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)

    # ── File handler — always active ──────────────────────────
    try:
        fh = RotatingFileHandler(
            LOG_DIR / "sentinelx.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)
    except Exception:
        pass

    logger.propagate = False
    return logger


def get_logger(module_name: str) -> logging.Logger:
    return setup_logger().getChild(module_name)