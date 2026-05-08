// components\threats\ThreatCard.jsx — full implementation in Phase 6
// frontend/src/components/threats/ThreatCard.jsx
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { formatDatetime } from '../../utils/formatters'
import { CATEGORY_ICONS } from '../../utils/constants'
import { CheckCheck, Cpu } from 'lucide-react'
import { api } from '../../services/apiClient'
import { useState } from 'react'
import clsx from 'clsx'

export function ThreatCard({ alert, onAck }) {
  const [killing, setKilling] = useState(false)

  const killProcess = async () => {
    if (!alert.source_pid) return
    setKilling(true)
    try {
      await api.killProcess(alert.source_pid)
      onAck(alert.alert_id)
    } catch (err) {
      console.error('Kill failed:', err)
    } finally {
      setKilling(false)
    }
  }

  return (
    <div className={clsx(
      'p-3 rounded-lg border transition-all',
      alert.acknowledged
        ? 'opacity-50 border-sentinel-border bg-sentinel-surface/50'
        : alert.severity === 'critical'
        ? 'border-red-500/40 bg-red-500/5 shadow-[0_0_8px_#ff444422]'
        : alert.severity === 'high'
        ? 'border-orange-500/40 bg-orange-500/5'
        : 'border-sentinel-border bg-sentinel-surface'
    )}>
      <div className="flex items-start gap-3">
        <span className="text-xl flex-shrink-0 mt-0.5">
          {CATEGORY_ICONS[alert.category] ?? '🔔'}
        </span>
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Badge severity={alert.severity}>{alert.severity.toUpperCase()}</Badge>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 border border-sentinel-border text-sentinel-muted font-mono">
              {alert.category}
            </span>
            <span className="text-xs font-medium text-sentinel-text">{alert.title}</span>
          </div>
          <p className="text-xs text-sentinel-muted leading-relaxed">{alert.detail}</p>
          <div className="flex items-center gap-3 text-[10px] text-sentinel-muted/60 font-mono">
            <span>{formatDatetime(alert.timestamp)}</span>
            {alert.source_pid && <span>PID: {alert.source_pid}</span>}
            {alert.source_domain && <span>Domain: {alert.source_domain}</span>}
            <span>ID: {alert.alert_id}</span>
          </div>
        </div>
        <div className="flex gap-1 flex-shrink-0">
          {alert.source_pid && !alert.acknowledged && (
            <Button variant="danger" onClick={killProcess} disabled={killing}>
              <Cpu size={12} />
              {killing ? '...' : 'Kill'}
            </Button>
          )}
          {!alert.acknowledged && (
            <Button variant="ghost" onClick={() => onAck(alert.alert_id)}>
              <CheckCheck size={12} />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}