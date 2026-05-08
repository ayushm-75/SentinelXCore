# backend/api/rest_router.py
import asyncio
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.core.state import state
from backend.core.settings import get_settings, update_settings, reload_settings
from backend.api.models import (
    VPNToggleRequest, KillProcessRequest, AcknowledgeAlertRequest,
    AddCustomDomainRequest, SettingsUpdateRequest, BlocklistSelectionRequest
)
from backend.core.logger import get_logger
import psutil

log    = get_logger("rest_api")
router = APIRouter(prefix="/api", tags=["sentinelx"])

# In-memory stats history
_stats_history: list = []


# ── Health ────────────────────────────────────────────────────
@router.get("/health")
async def health():
    from backend.core.engine import is_admin
    return {
        "status":    "ok",
        "uptime":    round(state.get_uptime(), 1),
        "version":   "1.0.0",
        "is_admin":  is_admin(),
        "vpn_active": state.vpn_active,
    }


# ── Snapshot ──────────────────────────────────────────────────
@router.get("/snapshot")
async def get_snapshot():
    return state.snapshot()


# ── Alerts ────────────────────────────────────────────────────
@router.get("/alerts")
async def get_alerts(limit: int = 100):
    alerts = await state.get_alerts(limit=limit)
    return [
        {
            "alert_id":      a.alert_id,
            "severity":      a.severity,
            "category":      a.category,
            "title":         a.title,
            "detail":        a.detail,
            "timestamp":     a.timestamp,
            "acknowledged":  a.acknowledged,
            "source_pid":    a.source_pid,
            "source_domain": a.source_domain,
        }
        for a in alerts
    ]


@router.post("/alerts/acknowledge")
async def acknowledge_alert(req: AcknowledgeAlertRequest):
    ok = await state.acknowledge_alert(req.alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"success": True}


@router.post("/alerts/acknowledge_all")
async def acknowledge_all_alerts():
    alerts = await state.get_alerts(limit=1000)
    for a in alerts:
        a.acknowledged = True
    return {"success": True, "count": len(alerts)}


# ── Connections ───────────────────────────────────────────────
@router.get("/connections")
async def get_connections(limit: int = 100):
    conns = list(state.active_connections.values())[:limit]
    return [
        {
            "pid":          c.pid,
            "process_name": c.process_name,
            "local_addr":   c.local_addr,
            "local_port":   c.local_port,
            "remote_addr":  c.remote_addr,
            "remote_port":  c.remote_port,
            "domain":       c.domain,
            "protocol":     c.protocol,
            "flagged":      c.flagged,
            "threat_score": round(c.threat_score, 3),
            "bytes_sent":   c.bytes_sent,
            "bytes_recv":   c.bytes_recv,
        }
        for c in conns
    ]


# ── Processes ─────────────────────────────────────────────────
@router.get("/processes")
async def get_processes():
    procs = list(state.processes.values())
    procs.sort(key=lambda p: p.cpu_percent, reverse=True)
    return [
        {
            "pid":          p.pid,
            "name":         p.name,
            "exe":          p.exe,
            "cmdline":      p.cmdline,
            "cpu_percent":  round(p.cpu_percent, 2),
            "memory_mb":    round(p.memory_mb, 1),
            "status":       p.status,
            "username":     p.username,
            "connections":  p.connections,
            "threat_score": round(p.threat_score, 3),
            "flagged":      p.flagged,
        }
        for p in procs[:100]
    ]


@router.post("/processes/kill")
async def kill_process(req: KillProcessRequest):
    try:
        proc = psutil.Process(req.pid)
        name = proc.name()
        proc.terminate()
        log.warning(f"Process killed: PID {req.pid} ({name})")
        return {"success": True, "pid": req.pid, "name": name}
    except psutil.NoSuchProcess:
        raise HTTPException(status_code=404, detail="Process not found")
    except psutil.AccessDenied:
        raise HTTPException(status_code=403, detail="Access denied — run as Administrator")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── VPN / AdBlock ─────────────────────────────────────────────
@router.post("/vpn/toggle")
async def toggle_vpn(req: VPNToggleRequest, background_tasks: BackgroundTasks):
    from backend.core.engine import is_admin
    if not is_admin():
        raise HTTPException(
            status_code=403,
            detail="Administrator rights required for VPN/DNS interception"
        )
    update_settings({"vpn_enabled": req.enabled})
    state.vpn_active = req.enabled

    if req.enabled:
        background_tasks.add_task(_start_vpn_task)
    else:
        background_tasks.add_task(_stop_vpn_task)

    from backend.core.event_bus import bus
    await bus.publish("vpn.toggled", {"enabled": req.enabled})
    return {"success": True, "vpn_enabled": req.enabled}


async def _start_vpn_task():
    try:
        from backend.vpn.vpn_controller import VPNController
        vpn = VPNController()
        await vpn.start()
    except Exception as e:
        log.error(f"VPN start error: {e}")


async def _stop_vpn_task():
    try:
        from backend.vpn.vpn_controller import VPNController
        await VPNController.stop_global()
    except Exception as e:
        log.error(f"VPN stop error: {e}")


@router.get("/vpn/status")
async def vpn_status():
    settings = get_settings()
    return {
        "vpn_enabled":      state.vpn_active,
        "blocklist_loaded": state.blocklist_loaded,
        "domain_count":     state.blocklist_domain_count,
        "active_lists":     settings.active_filter_lists,
    }


@router.post("/vpn/blocklists/select")
async def select_blocklists(req: BlocklistSelectionRequest, background_tasks: BackgroundTasks):
    valid  = {"adguard", "easylist", "easyprivacy", "hagezi"}
    chosen = [l for l in req.active_lists if l in valid]
    update_settings({"active_filter_lists": chosen})
    reload_settings()
    log.info(f"Filter list preferences saved: {chosen}")
    background_tasks.add_task(_reload_blocklists_task, chosen)
    return {"success": True, "active_lists": chosen}


async def _reload_blocklists_task(active_lists: list):
    try:
        from backend.vpn.blocklist_manager import BlocklistManager
        mgr = BlocklistManager()
        await mgr.load_lists(active_lists)
    except Exception as e:
        log.error(f"Blocklist reload error: {e}")


@router.post("/vpn/blocklists/update")
async def update_blocklists(background_tasks: BackgroundTasks):
    background_tasks.add_task(_download_blocklists_task)
    return {"success": True, "message": "Download started in background"}


async def _download_blocklists_task():
    try:
        from backend.vpn.blocklist_manager import BlocklistManager
        mgr = BlocklistManager()
        await mgr.download_all()
    except Exception as e:
        log.error(f"Blocklist download error: {e}")


@router.get("/vpn/blocklists/meta")
async def blocklist_meta():
    import json
    meta_path = Path("config/filter_lists_meta.json")
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ── Custom domain rules ───────────────────────────────────────
@router.post("/domains/custom")
async def add_custom_domain(req: AddCustomDomainRequest):
    if req.action not in ("block", "allow"):
        raise HTTPException(status_code=400, detail="Action must be 'block' or 'allow'")
    settings = get_settings()
    if req.action == "block":
        if req.domain not in settings.custom_block_domains:
            settings.custom_block_domains.append(req.domain)
    else:
        if req.domain not in settings.custom_allow_domains:
            settings.custom_allow_domains.append(req.domain)
    from backend.core.settings import save_settings
    save_settings(settings)
    return {"success": True, "domain": req.domain, "action": req.action}


@router.get("/domains/check/{domain}")
async def check_domain(domain: str):
    try:
        from backend.vpn.blocklist_manager import BlocklistManager
        mgr     = BlocklistManager()
        blocked = mgr.is_blocked(domain)
        return {"domain": domain, "blocked": blocked}
    except Exception as e:
        return {"domain": domain, "blocked": False, "error": str(e)}


# ── Settings ──────────────────────────────────────────────────
@router.get("/settings")
async def get_all_settings():
    return get_settings().model_dump()


@router.post("/settings/update")
async def update_settings_endpoint(req: SettingsUpdateRequest):
    updated = update_settings(req.updates)
    reload_settings()
    return {"success": True, "settings": updated.model_dump()}


# ── File operations ───────────────────────────────────────────
@router.post("/files/scan")
async def scan_file(body: dict):
    path = body.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="path required")
    from backend.monitor.file_scanner import FileScanner
    scanner = FileScanner()
    result  = await scanner.scan_file(path)
    return result


@router.post("/files/quarantine")
async def quarantine_file(body: dict):
    path = body.get("path", "")
    if not path:
        raise HTTPException(status_code=400, detail="path required")
    from backend.protection.file_guard import FileGuard
    guard  = FileGuard()
    result = await guard.quarantine_file(path)
    return result


@router.get("/files/quarantine")
async def list_quarantine():
    from backend.protection.file_guard import FileGuard
    guard = FileGuard()
    return guard.list_quarantine()


# ── Stats history ─────────────────────────────────────────────
@router.get("/stats/history")
async def stats_history():
    return _stats_history[-60:]


def record_stats_snapshot():
    _stats_history.append({
        "timestamp":   time.time(),
        "cpu":         state.cpu_percent,
        "ram":         state.ram_percent,
        "bytes_in":    state.bytes_in,
        "bytes_out":   state.bytes_out,
        "connections": len(state.active_connections),
        "blocked":     state.blocked_count,
    })
    if len(_stats_history) > 300:
        _stats_history.pop(0)


# ── Threat score ──────────────────────────────────────────────
@router.get("/threat/level")
async def threat_level():
    from backend.ai.threat_scorer import get_system_threat_level
    return get_system_threat_level()