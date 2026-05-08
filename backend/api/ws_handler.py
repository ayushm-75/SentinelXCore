# backend/api/ws_handler.py
# Full replacement

import asyncio
import json
import time
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from backend.core.logger import get_logger
from backend.core.state import state
from backend.core.event_bus import bus
import orjson

log = get_logger("ws_handler")


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)
        state.ws_clients.add(ws)
        log.info(f"WS client connected. Total: {len(self.active)}")
        # Send initial data burst
        await self.send_one(ws, {
            "type": "snapshot",
            "data": state.snapshot(),
            "timestamp": time.time(),
        })
        # Send initial connections
        conns = list(state.active_connections.values())[:100]
        await self.send_one(ws, {
            "type": "connections",
            "data": [_conn_to_dict(c) for c in conns],
            "timestamp": time.time(),
        })

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)
        state.ws_clients.discard(ws)
        log.info(f"WS client disconnected. Total: {len(self.active)}")

    async def broadcast(self, message: dict) -> None:
        if not self.active:
            return
        raw  = orjson.dumps(message)
        dead = set()
        for ws in list(self.active):
            try:
                await ws.send_bytes(raw)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)

    async def send_one(self, ws: WebSocket, message: dict) -> None:
        try:
            await ws.send_bytes(orjson.dumps(message))
        except Exception:
            self.disconnect(ws)


def _conn_to_dict(c) -> dict:
    return {
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


manager = ConnectionManager()


async def ws_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            try:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=120.0)
                try:
                    msg = json.loads(raw)
                    await handle_client_message(ws, msg)
                except json.JSONDecodeError:
                    pass
            except asyncio.TimeoutError:
                # Server-side ping to keep alive
                try:
                    await ws.send_bytes(orjson.dumps({
                        "type": "ping",
                        "timestamp": time.time(),
                    }))
                except Exception:
                    break
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        log.debug(f"WS error: {e}")
        manager.disconnect(ws)


async def handle_client_message(ws: WebSocket, msg: dict) -> None:
    msg_type = msg.get("type", "")

    if msg_type == "ping":
        await manager.send_one(ws, {"type": "pong", "timestamp": time.time()})

    elif msg_type == "pong":
        pass

    elif msg_type == "get_snapshot":
        await manager.send_one(ws, {
            "type": "snapshot",
            "data": state.snapshot(),
            "timestamp": time.time(),
        })

    elif msg_type == "get_alerts":
        alerts = await state.get_alerts(limit=100)
        await manager.send_one(ws, {
            "type": "alerts",
            "data": [
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
            ],
            "timestamp": time.time(),
        })

    elif msg_type == "get_connections":
        conns = list(state.active_connections.values())[:100]
        await manager.send_one(ws, {
            "type": "connections",
            "data": [_conn_to_dict(c) for c in conns],
            "timestamp": time.time(),
        })


async def broadcast_loop() -> None:
    """Broadcast snapshot every 3s + connections every 5s."""
    tick = 0
    while True:
        await asyncio.sleep(3.0)
        tick += 1

        if not manager.active:
            continue

        # Always broadcast snapshot
        await manager.broadcast({
            "type": "snapshot",
            "data": state.snapshot(),
            "timestamp": time.time(),
        })

        # Broadcast connections every ~15s (every 5 ticks)
        if tick % 5 == 0:
            conns = list(state.active_connections.values())[:100]
            await manager.broadcast({
                "type": "connections",
                "data": [_conn_to_dict(c) for c in conns],
                "timestamp": time.time(),
            })


def setup_event_forwarding() -> None:
    async def forward(event: dict) -> None:
        if not manager.active:
            return
        event_type = event.get("type", "")
        data       = event.get("data", {})

        # connections.update → reformat as "connections" for frontend
        if event_type == "connections.update":
            await manager.broadcast({
                "type": "connections",
                "data": data.get("connections", []),
                "timestamp": time.time(),
            })
        else:
            await manager.broadcast({
                "type":      event_type,
                "data":      data,
                "timestamp": time.time(),
            })

    forwarded_events = [
        "alert.new",
        "network.blocked",
        "process.suspicious",
        "file.threat",
        "ai.anomaly",
        "vpn.toggled",
        "blocklist.updated",
        "connections.update",
    ]

    for evt in forwarded_events:
        bus.subscribe(evt, forward)