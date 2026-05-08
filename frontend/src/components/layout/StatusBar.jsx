// components\layout\StatusBar.jsx — full implementation in Phase 6
// frontend/src/components/layout/StatusBar.jsx
import { useSystemStats } from '../../hooks/useSystemStats'
import { formatNumber } from '../../utils/formatters'

export function StatusBar() {
  const { totalPackets, blocked, connections, blocklistDomains } = useSystemStats()

  return (
    <footer className="h-7 bg-sentinel-bg border-t border-sentinel-border flex items-center px-4 gap-6 text-[10px] font-mono text-sentinel-muted flex-shrink-0">
      <span>PACKETS: <span className="text-sentinel-accent">{formatNumber(totalPackets)}</span></span>
      <span>BLOCKED: <span className="text-red-400">{formatNumber(blocked)}</span></span>
      <span>CONNS: <span className="text-sentinel-text">{formatNumber(connections)}</span></span>
      <span>BLOCKLIST: <span className="text-sentinel-green">{formatNumber(blocklistDomains)} domains</span></span>
      <div className="flex-1" />
      <span className="text-sentinel-muted">SentinelX Core — Local AI Defense — OFFLINE</span>
    </footer>
  )
}