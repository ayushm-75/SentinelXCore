// components\vpn\VPNToggle.jsx — full implementation in Phase 6
// frontend/src/components/vpn/VPNToggle.jsx
import { useState } from 'react'
import { useSystemStats } from '../../hooks/useSystemStats'
import { api } from '../../services/apiClient'
import { Toggle } from '../ui/Toggle'
import { Shield, ShieldOff, ShieldCheck } from 'lucide-react'
import { formatNumber } from '../../utils/formatters'
import clsx from 'clsx'

export function VPNToggle() {
  const { vpnActive, blocked, blocklistDomains } = useSystemStats()
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')

  const handleToggle = async (enabled) => {
    setLoading(true)
    setError('')
    try {
      await api.vpnToggle(enabled)
    } catch (err) {
      setError(err.message ?? 'Toggle failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={clsx(
      'p-6 rounded-xl border-2 transition-all',
      vpnActive
        ? 'border-sentinel-green/50 bg-sentinel-green/5 shadow-[0_0_20px_#00ff8822]'
        : 'border-sentinel-border bg-sentinel-surface'
    )}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          {vpnActive
            ? <ShieldCheck size={32} className="text-sentinel-green animate-pulse-slow" />
            : <ShieldOff   size={32} className="text-sentinel-muted" />}
          <div>
            <h2 className="text-lg font-bold text-sentinel-text">Ad-Block VPN</h2>
            <p className="text-xs text-sentinel-muted">DNS-level domain blocking</p>
          </div>
        </div>
        <Toggle
          checked={vpnActive}
          onChange={handleToggle}
          disabled={loading}
        />
      </div>

      <div className="grid grid-cols-3 gap-4 text-center">
        <div className="p-3 rounded-lg bg-sentinel-bg border border-sentinel-border">
          <p className="text-2xl font-bold font-mono text-sentinel-accent">
            {formatNumber(blocklistDomains)}
          </p>
          <p className="text-[11px] text-sentinel-muted mt-1">Domains blocked</p>
        </div>
        <div className="p-3 rounded-lg bg-sentinel-bg border border-sentinel-border">
          <p className="text-2xl font-bold font-mono text-red-400">
            {formatNumber(blocked)}
          </p>
          <p className="text-[11px] text-sentinel-muted mt-1">Requests blocked</p>
        </div>
        <div className="p-3 rounded-lg bg-sentinel-bg border border-sentinel-border">
          <p className={`text-2xl font-bold font-mono ${vpnActive ? 'text-sentinel-green' : 'text-sentinel-muted'}`}>
            {vpnActive ? 'ON' : 'OFF'}
          </p>
          <p className="text-[11px] text-sentinel-muted mt-1">Protection status</p>
        </div>
      </div>

      {error && (
        <p className="mt-3 text-xs text-red-400 bg-red-500/10 border border-red-500/30 rounded p-2">
          ⚠ {error}
        </p>
      )}

      {!vpnActive && (
        <p className="mt-3 text-xs text-sentinel-muted text-center">
          Requires Administrator rights. Real-time protection still active.
        </p>
      )}

      {loading && (
        <p className="mt-3 text-xs text-sentinel-accent text-center animate-pulse">
          {vpnActive ? 'Disabling...' : 'Enabling VPN — loading blocklists...'}
        </p>
      )}
    </div>
  )
}