# backend/main.py
import asyncio
import sys
import os
import threading
import signal
import time
import queue
from pathlib import Path
from contextlib import asynccontextmanager

if getattr(sys, 'frozen', False):
    ROOT    = Path(sys._MEIPASS)
    EXE_DIR = Path(sys.executable).parent
else:
    ROOT    = Path(__file__).resolve().parent.parent
    EXE_DIR = ROOT

os.chdir(EXE_DIR)
sys.path.insert(0, str(ROOT))

import uvicorn
from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.core.engine import SentinelXEngine, is_admin
from backend.core.logger import setup_logger, get_logger
from backend.core.settings import get_settings
from backend.core.state import state
from backend.api.rest_router import router, record_stats_snapshot
from backend.api.ws_handler import (
    ws_endpoint, broadcast_loop,
    setup_event_forwarding,
)

log    = get_logger("main")
engine = SentinelXEngine()

_server_ready = threading.Event()

# Window ref + lock
_webview_window = None
_webview_lock   = threading.Lock()

# Commands the tray thread sends to the main thread
_main_queue = queue.Queue()
_CMD_OPEN   = "open"
_CMD_QUIT   = "quit"


# ── FastAPI ───────────────────────────────────────────────────

async def stats_recorder():
    while True:
        await asyncio.sleep(2.0)
        record_stats_snapshot()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_event_forwarding()
    asyncio.create_task(broadcast_loop())
    asyncio.create_task(stats_recorder())
    asyncio.create_task(engine.start())

    settings = get_settings()
    log.info("=" * 55)
    log.info("  SentinelX Core v1.0.0 — Server Ready")
    log.info("=" * 55)
    log.info(f"  URL : http://{settings.backend_host}:{settings.backend_port}")
    log.info(f"  WS  : ws://{settings.backend_host}:{settings.backend_port}/ws")
    log.info("=" * 55)

    _server_ready.set()
    yield
    await engine.stop()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="SentinelX Core API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_endpoint(websocket)

    frontend_dist = ROOT / "frontend" / "dist"
    log.info(f"Looking for frontend at: {frontend_dist}")

    if frontend_dist.exists():
        log.info("Frontend found — mounting static files")

        assets_dir = frontend_dist / "assets"
        if assets_dir.exists():
            app.mount(
                "/assets",
                StaticFiles(directory=str(assets_dir)),
                name="assets"
            )

        index_file = frontend_dist / "index.html"

        @app.get("/")
        async def serve_root():
            return FileResponse(str(index_file))

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            if (full_path.startswith("api") or
                    full_path.startswith("ws") or
                    full_path.startswith("docs")):
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            candidate = frontend_dist / full_path
            if candidate.exists() and candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(index_file))

    else:
        log.error(f"Frontend dist NOT FOUND at: {frontend_dist}")

        @app.get("/")
        async def no_frontend():
            return JSONResponse({
                "error": "Frontend not built",
                "dist_path": str(frontend_dist),
            })

    return app


app = create_app()


# ── Tray icon ─────────────────────────────────────────────────

def make_tray_icon():
    from PIL import Image, ImageDraw
    s    = 64
    img  = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, 62, 62], fill=(10, 14, 26, 255))
    shield = [(32,4),(60,18),(60,38),(32,60),(4,38),(4,18)]
    draw.polygon(shield, fill=(0, 212, 255, 255))
    inner = [(32,12),(52,24),(52,36),(32,52),(12,36),(12,24)]
    draw.polygon(inner, fill=(10, 14, 26, 255))
    lw = 4
    draw.line([(21,21),(43,43)], fill=(0,255,136,255), width=lw)
    draw.line([(43,21),(21,43)], fill=(0,255,136,255), width=lw)
    return img


def start_tray():
    try:
        import pystray

        def on_open(_icon, _item):
            with _webview_lock:
                win = _webview_window

            if win is not None:
                try:
                    win.show()
                    return
                except Exception:
                    pass

            # Ask the main thread to open a new window
            _main_queue.put(_CMD_OPEN)

        def on_quit(icon, _item):
            log.info("Quit from tray")
            _main_queue.put(_CMD_QUIT)
            icon.stop()

        menu = pystray.Menu(
            pystray.MenuItem("Open SentinelX", on_open, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit SentinelX", on_quit),
        )

        icon = pystray.Icon(
            "SentinelX Core",
            make_tray_icon(),
            "SentinelX Core — Running",
            menu,
        )

        log.info("System tray icon started")
        icon.run()

    except Exception as e:
        log.error(f"Tray error: {e}")


# ── HTTP health check ─────────────────────────────────────────

def wait_for_http(host: str, port: int, timeout: float = 30.0) -> bool:
    """
    Poll until the HTTP server actually responds with 200.
    Fixes the 'Can't reach this page' error that happens when
    pywebview opens before uvicorn is fully accepting connections.
    """
    import urllib.request

    url      = f"http://{host}:{port}/"
    deadline = time.time() + timeout

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.25)

    return False


# ── WebView window — MAIN THREAD ONLY ────────────────────────

def _open_webview_window():
    """
    Create and run a pywebview window.
    Must be called from the main thread — always.
    Blocks until the window is closed.
    """
    global _webview_window

    try:
        import webview
    except ImportError:
        log.error("pywebview not installed — falling back to browser")
        _open_browser_fallback()
        return

    settings = get_settings()
    host     = settings.backend_host
    port     = settings.backend_port
    url      = f"http://{host}:{port}"

    # Wait until HTTP is actually responding before loading the window.
    # This is what prevents 'Can't reach this page'.
    log.info("Confirming HTTP server is reachable...")
    if not wait_for_http(host, port):
        log.error("Server did not respond — falling back to browser")
        _open_browser_fallback()
        return

    log.info(f"Opening webview window → {url}")

    win = webview.create_window(
        title="SentinelX Core",
        url=url,
        width=1280,
        height=800,
        min_size=(900, 600),
        resizable=True,
        background_color="#0a0e1a",
        text_select=False,
        zoomable=True,
        easy_drag=False,
    )

    def on_closed():
        global _webview_window
        log.info("Window closed — continuing in system tray")
        with _webview_lock:
            _webview_window = None

    win.events.closed += on_closed

    with _webview_lock:
        _webview_window = win

    # Blocks here until the window is closed
    webview.start(
        debug=False,
        private_mode=False,
        storage_path=str(EXE_DIR / "data" / "webview_cache"),
    )

    # After start() returns, clear the ref so the queue loop
    # knows the window is gone
    with _webview_lock:
        _webview_window = None


def _open_browser_fallback():
    import webbrowser
    settings = get_settings()
    webbrowser.open(f"http://{settings.backend_host}:{settings.backend_port}")


# ── Uvicorn ───────────────────────────────────────────────────

# In backend/main.py — replace run_uvicorn() with this:

def run_uvicorn():
    """Run uvicorn in a dedicated background thread with its own event loop."""
    settings = get_settings()

    async def _serve():
        config = uvicorn.Config(
            app=app,
            host=settings.backend_host,
            port=settings.backend_port,
            # Disable uvicorn's own log config — we manage logging ourselves
            # This prevents "Unable to configure formatter 'default'" in frozen exe
            log_config=None,
            log_level="critical",   # suppress uvicorn's logger entirely
            access_log=False,
            loop="asyncio",
            workers=1,
        )
        server = uvicorn.Server(config)
        await server.serve()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_serve())
    except Exception as e:
        log.error(f"Uvicorn error: {e}")
    finally:
        loop.close()


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    setup_logger(level=get_settings().log_level)
    log.info("SentinelX Core starting...")

    if not is_admin():
        log.warning("Not running as Administrator — VPN/packet capture disabled")

    # 1. Uvicorn in background thread
    uvicorn_thread = threading.Thread(
        target=run_uvicorn,
        daemon=True,
        name="uvicorn",
    )
    uvicorn_thread.start()

    # 2. Wait for lifespan to fire
    log.info("Waiting for server...")
    if not _server_ready.wait(timeout=20.0):
        log.error("Server failed to start — check logs")
        sys.exit(1)
    log.info("Server is ready.")

    # 3. Tray in background thread
    tray_thread = threading.Thread(
        target=start_tray,
        daemon=True,
        name="tray",
    )
    tray_thread.start()

    # 4. Open the initial window on the main thread
    _open_webview_window()

    # 5. Main-thread command loop
    # The tray posts _CMD_OPEN or _CMD_QUIT here.
    # pywebview requires the main thread, so we handle it here.
    log.info("Window closed. Running in system tray.")
    log.info("Right-click tray icon → 'Open SentinelX' to reopen")

    while True:
        try:
            cmd = _main_queue.get(timeout=1.0)

            if cmd == _CMD_OPEN:
                log.info("Reopening window...")
                _open_webview_window()
                log.info("Window closed again. Back in tray.")

            elif cmd == _CMD_QUIT:
                log.info("Shutting down SentinelX Core...")
                break

        except queue.Empty:
            continue
        except (KeyboardInterrupt, SystemExit):
            log.info("Interrupted — shutting down...")
            break

    sys.exit(0)