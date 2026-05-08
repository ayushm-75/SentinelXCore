// components\dashboard\ThreatTimeline.jsx — full implementation in Phase 6
// frontend/src/components/dashboard/ThreatTimeline.jsx
import { useAlerts } from '../../hooks/useAlerts'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { formatTimestamp, truncate } from '../../utils/formatters'
import { CATEGORY_ICONS } from '../../utils/constants'
import { Card, CardHeader } from '../ui/Card'
import { CheckCheck } from 'lucide-react'

export function ThreatTimeline() {
  const { alerts, acknowledge } = useAlerts()
  const recent = alerts.slice(0, 12)

  return (
    <Card>
      <CardHeader
        title="Threat Timeline"
        subtitle={`${alerts.length} total events`}
      />
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {recent.length === 0 && (
          <p className="text-center text-sentinel-muted text-sm py-6">
            No threats detected — system clean ✓
          </p>
        )}
        {recent.map(alert => (
          <div
            key={alert.alert_id}
            className={`flex items-start gap-3 p-2 rounded border transition-opacity ${
              alert.acknowledged ? 'opacity-40 border-transparent' : 'border-sentinel-border'
            }`}
          >
            <span className="text-base mt-0.5 flex-shrink-0">
              {CATEGORY_ICONS[alert.category] ?? '🔔'}
            </span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge severity={alert.severity}>{alert.severity}</Badge>
                <span className="text-xs text-sentinel-text font-medium truncate">
                  {truncate(alert.title, 45)}
                </span>
              </div>
              <p className="text-[11px] text-sentinel-muted mt-0.5 leading-relaxed">
                {truncate(alert.detail, 80)}
              </p>
              <p className="text-[10px] text-sentinel-muted/60 mt-0.5 font-mono">
                {formatTimestamp(alert.timestamp)}
              </p>
            </div>
            {!alert.acknowledged && (
              <button
                onClick={() => acknowledge(alert.alert_id)}
                className="flex-shrink-0 text-sentinel-muted hover:text-sentinel-green transition-colors"
                title="Acknowledge"
              >
                <CheckCheck size={14} />
              </button>
            )}
          </div>
        ))}
      </div>
    </Card>
  )
}