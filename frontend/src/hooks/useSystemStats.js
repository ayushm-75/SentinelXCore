// frontend/src/hooks/useSystemStats.js
import { useNetworkStore } from '../store/networkStore'

export function useSystemStats() {
  const snapshot     = useNetworkStore(s => s.snapshot)
  const statsHistory = useNetworkStore(s => s.statsHistory)

  return {
    cpu:         snapshot.cpu_percent      ?? 0,
    ram:         snapshot.ram_percent      ?? 0,
    ramMb:       snapshot.ram_used_mb      ?? 0,
    disk:        snapshot.disk_percent     ?? 0,
    totalPackets:snapshot.total_packets    ?? 0,
    bytesIn:     snapshot.bytes_in         ?? 0,
    bytesOut:    snapshot.bytes_out        ?? 0,
    blocked:     snapshot.blocked_count    ?? 0,
    vpnActive:   snapshot.vpn_active       ?? false,
    modelTrained:snapshot.model_trained    ?? false,
    anomalies:   snapshot.anomalies        ?? 0,
    alertCount:  snapshot.alert_count      ?? {},
    connections: snapshot.connection_count ?? 0,
    uptime:      snapshot.uptime           ?? 0,
    blocklistDomains: snapshot.blocklist_domains ?? 0,
    history:     statsHistory,
  }
}