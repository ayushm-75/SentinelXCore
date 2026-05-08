// components\dashboard\StatsCards.jsx — full implementation in Phase 6
// frontend/src/components/dashboard/StatsCards.jsx
import { useSystemStats } from '../../hooks/useSystemStats'
import { useAlerts } from '../../hooks/useAlerts'
import { formatBytes, formatNumber } from '../../utils/formatters'
import {
  Cpu, MemoryStick, Network, ShieldAlert,
  Bot, PackageX
} from 'lucide-react'
import clsx from 'clsx'

function StatCard({ icon: Icon, label, value, sub, color, glow }) {
  return (
    <div className={clsx(
      'flex flex-col gap-2 p-4 rounded-lg border bg-sentinel-surface transition-all',
      glow ? `border-${color}-500/40 shadow-[0_0_12px_${color}22]` : 'border-sentinel-border',
    )}>
      <div className="flex items-center justify-between">
        <span className="text-xs text-sentinel-muted font-medium uppercase tracking-wide">{label}</span>
        <Icon size={16} className={`text-${color}-400`} />
      </div>
      <div className="text-2xl font-bold font-mono text-sentinel-text">{value}</div>
      {sub && <div className="text-[11px] text-sentinel-muted">{sub}</div>}
    </div>
  )
}

export function StatsCards() {
  const s = useSystemStats()
  const { unread } = useAlerts()

  const cards = [
    {
      icon:  Cpu,
      label: 'CPU Usage',
      value: `${s.cpu.toFixed(1)}%`,
      sub:   s.cpu > 80 ? '⚠ High CPU' : 'Normal',
      color: s.cpu > 80 ? 'red' : 'blue',
      glow:  s.cpu > 80,
    },
    {
      icon:  MemoryStick,
      label: 'RAM Usage',
      value: `${s.ram.toFixed(1)}%`,
      sub:   `${s.ramMb.toFixed(0)} MB used`,
      color: s.ram > 85 ? 'red' : 'purple',
      glow:  s.ram > 85,
    },
    {
      icon:  Network,
      label: 'Connections',
      value: formatNumber(s.connections),
      sub:   `↑ ${formatBytes(s.bytesOut)} ↓ ${formatBytes(s.bytesIn)}`,
      color: 'cyan',
      glow:  false,
    },
    {
      icon:  PackageX,
      label: 'Blocked',
      value: formatNumber(s.blocked),
      sub:   `${formatNumber(s.blocklistDomains)} domains in blocklist`,
      color: 'orange',
      glow:  s.blocked > 0,
    },
    {
      icon:  ShieldAlert,
      label: 'Active Alerts',
      value: formatNumber(unread),
      sub:   `${s.alertCount.critical ?? 0} critical`,
      color: unread > 0 ? 'red' : 'green',
      glow:  unread > 0,
    },
    {
      icon:  Bot,
      label: 'AI Anomalies',
      value: formatNumber(s.anomalies),
      sub:   s.modelTrained ? 'Model trained' : 'Collecting samples...',
      color: s.anomalies > 0 ? 'orange' : 'green',
      glow:  s.anomalies > 0,
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
      {cards.map(c => <StatCard key={c.label} {...c} />)}
    </div>
  )
}