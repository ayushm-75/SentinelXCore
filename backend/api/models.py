# backend/api/models.py  — add model_config to fix the warning
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any
import time


class AlertModel(BaseModel):
    alert_id: str
    severity: str
    category: str
    title: str
    detail: str
    timestamp: float
    acknowledged: bool
    source_pid: Optional[int] = None
    source_domain: Optional[str] = None


class ConnectionModel(BaseModel):
    pid: int
    process_name: str
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    domain: Optional[str] = None
    protocol: str
    timestamp: float
    bytes_sent: int
    bytes_recv: int
    flagged: bool
    threat_score: float


class ProcessModel(BaseModel):
    pid: int
    name: str
    exe: str
    cmdline: str
    cpu_percent: float
    memory_mb: float
    status: str
    username: str
    connections: int
    threat_score: float
    flagged: bool


class SystemSnapshotModel(BaseModel):
    model_config = ConfigDict(protected_namespaces=())  # ← fixes model_ warning

    cpu_percent: float
    ram_percent: float
    ram_used_mb: float
    disk_percent: float
    total_packets: int
    bytes_in: int
    bytes_out: int
    blocked_count: int
    vpn_active: bool
    model_trained: bool
    anomalies: int
    alert_count: Dict[str, int]
    connection_count: int
    uptime: float
    blocklist_domains: int


class VPNToggleRequest(BaseModel):
    enabled: bool


class BlocklistSelectionRequest(BaseModel):
    active_lists: List[str]


class KillProcessRequest(BaseModel):
    pid: int


class AcknowledgeAlertRequest(BaseModel):
    alert_id: str


class AddCustomDomainRequest(BaseModel):
    domain: str
    action: str


class SettingsUpdateRequest(BaseModel):
    updates: Dict[str, Any]


class WSMessage(BaseModel):
    type: str
    data: Any = None
    timestamp: float = Field(default_factory=time.time)