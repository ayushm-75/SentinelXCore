// components\layout\TopBar.jsx — full implementation in Phase 6
// frontend/src/components/layout/TopBar.jsx
import { useAppStore } from '../../store/appStore'
import { useSystemStats } from '../../hooks/useSystemStats'
import { StatusDot } from '../ui/Badge'
import { formatUptime } from '../../utils/formatters'
import { Wifi, WifiOff, ShieldCheck, ShieldOff } from 'lucide-react'

export function TopBar() {
  const connected  = useAppStore(s => s.connected)
  const { uptime, vpnActive, cpu, ram } = useSystemStats()

  return (
    <header className="h-14 bg-sentinel-surface border-b border-sentinel-border flex items-center px-4 gap-4 flex-shrink-0">
      {/* Page title placeholder — filled by pages */}
      <div className="flex-1" />

      {/* Status pills */}
      <div className="flex items-center gap-3 text-xs font-mono">
        <div className="flex items-center gap-1.5 text-sentinel-muted">
          <span className="text-sentinel-accent">CPU</span>
          <span className={cpu > 80 ? 'text-red-400' : 'text-sentinel-text'}>{cpu.toFixed(1)}%</span>
        </div>
        <div className="flex items-center gap-1.5 text-sentinel-muted">
          <span className="text-sentinel-accent">RAM</span>
          <span className={ram > 85 ? 'text-red-400' : 'text-sentinel-text'}>{ram.toFixed(1)}%</span>
        </div>

        <div className="w-px h-4 bg-sentinel-border" />

        {/* VPN status */}
        <div className="flex items-center gap-1.5">
          {vpnActive
            ? <ShieldCheck size={14} className="text-sentinel-green" />
            : <ShieldOff   size={14} className="text-sentinel-muted" />}
          <span className={vpnActive ? 'text-sentinel-green' : 'text-sentinel-muted'}>
            {vpnActive ? 'VPN ON' : 'VPN OFF'}
          </span>
        </div>

        <div className="w-px h-4 bg-sentinel-border" />

        {/* WS connection */}
        <div className="flex items-center gap-1.5">
          <StatusDot active={connected} />
          <span className={connected ? 'text-sentinel-green' : 'text-red-400'}>
            {connected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>

        <div className="w-px h-4 bg-sentinel-border" />
        <span className="text-sentinel-muted">UP {formatUptime(uptime)}</span>
      </div>
    </header>
  )
}