// pages\Threats.jsx — full implementation in Phase 6
// frontend/src/pages/Threats.jsx
import { AlertPanel } from '../components/threats/AlertPanel'
import { useAlerts } from '../hooks/useAlerts'
import { useSystemStats } from '../hooks/useSystemStats'
import { Badge } from '../components/ui/Badge'

export function Threats() {
  const { alerts, unread } = useAlerts()
  const { alertCount }     = useSystemStats()

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-sentinel-text">
          Threats
          {unread > 0 && (
            <span className="ml-2 px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 text-xs font-mono">
              {unread} new
            </span>
          )}
        </h1>
        <div className="flex gap-2">
          {Object.entries(alertCount).map(([sev, count]) =>
            count > 0 ? (
              <Badge key={sev} severity={sev}>{count} {sev}</Badge>
            ) : null
          )}
        </div>
      </div>
      <AlertPanel />
    </div>
  )
}