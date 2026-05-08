// components\threats\AlertPanel.jsx — full implementation in Phase 6
// frontend/src/components/threats/AlertPanel.jsx
import { useState } from 'react'
import { useAlerts } from '../../hooks/useAlerts'
import { ThreatCard } from './ThreatCard'
import { Button } from '../ui/Button'
import { CheckCheck, Filter } from 'lucide-react'

const SEVERITIES = ['all', 'critical', 'high', 'medium', 'low', 'info']
const CATEGORIES = ['all', 'network', 'process', 'file', 'ai']

export function AlertPanel() {
  const { alerts, acknowledge } = useAlerts()
  const [sevFilter, setSevFilter]  = useState('all')
  const [catFilter, setCatFilter]  = useState('all')
  const [showAcked, setShowAcked]  = useState(false)

  const filtered = alerts.filter(a => {
    if (!showAcked && a.acknowledged) return false
    if (sevFilter !== 'all' && a.severity !== sevFilter) return false
    if (catFilter !== 'all' && a.category !== catFilter) return false
    return true
  })

  const ackAll = () => {
    alerts.filter(a => !a.acknowledged).forEach(a => acknowledge(a.alert_id))
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-center">
        <Filter size={14} className="text-sentinel-muted" />
        <div className="flex gap-1 flex-wrap">
          {SEVERITIES.map(s => (
            <button
              key={s}
              onClick={() => setSevFilter(s)}
              className={`px-2 py-0.5 rounded text-xs font-mono border transition-colors ${
                sevFilter === s
                  ? 'bg-sentinel-accent/20 border-sentinel-accent/50 text-sentinel-accent'
                  : 'border-sentinel-border text-sentinel-muted hover:text-sentinel-text'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        <div className="w-px h-4 bg-sentinel-border mx-1" />
        <div className="flex gap-1 flex-wrap">
          {CATEGORIES.map(c => (
            <button
              key={c}
              onClick={() => setCatFilter(c)}
              className={`px-2 py-0.5 rounded text-xs font-mono border transition-colors ${
                catFilter === c
                  ? 'bg-purple-500/20 border-purple-500/50 text-purple-400'
                  : 'border-sentinel-border text-sentinel-muted hover:text-sentinel-text'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
        <div className="flex-1" />
        <label className="flex items-center gap-2 text-xs text-sentinel-muted cursor-pointer">
          <input
            type="checkbox"
            checked={showAcked}
            onChange={e => setShowAcked(e.target.checked)}
            className="accent-sentinel-accent"
          />
          Show acknowledged
        </label>
        <Button variant="ghost" onClick={ackAll}>
          <CheckCheck size={14} /> Ack All
        </Button>
      </div>

      {/* Alert count */}
      <p className="text-xs text-sentinel-muted">
        Showing <span className="text-sentinel-text">{filtered.length}</span> of{' '}
        <span className="text-sentinel-text">{alerts.length}</span> alerts
      </p>

      {/* Alerts */}
      <div className="space-y-2 max-h-[calc(100vh-280px)] overflow-y-auto pr-1">
        {filtered.length === 0 && (
          <div className="text-center py-16 text-sentinel-muted">
            <p className="text-4xl mb-2">🛡️</p>
            <p>No alerts match current filters</p>
          </div>
        )}
        {filtered.map(alert => (
          <ThreatCard key={alert.alert_id} alert={alert} onAck={acknowledge} />
        ))}
      </div>
    </div>
  )
}