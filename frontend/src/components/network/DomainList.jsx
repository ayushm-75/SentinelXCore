// frontend/src/components/network/DomainList.jsx
import { useState } from 'react'
import { useNetworkStore } from '../../store/networkStore'
import { api } from '../../services/apiClient'
import { Button } from '../ui/Button'
import { Search, ShieldX, ShieldCheck } from 'lucide-react'
import clsx from 'clsx'

export function DomainList() {
  const connections    = useNetworkStore(s => s.connections)
  const [filter, setFilter]       = useState('')
  const [checkResult, setCheckResult] = useState(null)
  const [checking, setChecking]   = useState(false)

  // Build unique domain list from active connections
  const domainEntries = [...new Map(
    connections
      .filter(c => c.domain && c.domain.trim())
      .map(c => [c.domain, c])
  ).values()]
    .filter(c => c.domain.toLowerCase().includes(filter.toLowerCase()))
    .slice(0, 100)

  const checkDomain = async () => {
    const target = filter.trim()
    if (!target) return
    setChecking(true)
    try {
      const res = await api.checkDomain(target)
      setCheckResult(res)
    } catch (_err) {
      setCheckResult({ error: 'Check failed' })
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="space-y-3">
      {/* Search + check */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search size={13} className="absolute left-2.5 top-2 text-sentinel-muted" />
          <input
            value={filter}
            onChange={e => { setFilter(e.target.value); setCheckResult(null) }}
            onKeyDown={e => e.key === 'Enter' && checkDomain()}
            placeholder="Filter or check domain..."
            className="w-full pl-8 pr-3 py-1.5 bg-sentinel-bg border border-sentinel-border rounded text-xs text-sentinel-text placeholder:text-sentinel-muted focus:outline-none focus:border-sentinel-accent font-mono"
          />
        </div>
        <Button onClick={checkDomain} disabled={checking || !filter.trim()}>
          Check
        </Button>
      </div>

      {/* Check result */}
      {checkResult && !checkResult.error && (
        <div className={clsx(
          'flex items-center gap-2 p-2 rounded border text-xs font-mono',
          checkResult.blocked
            ? 'bg-red-500/10 border-red-500/30 text-red-400'
            : 'bg-green-500/10 border-green-500/30 text-sentinel-green'
        )}>
          {checkResult.blocked
            ? <ShieldX size={13} />
            : <ShieldCheck size={13} />}
          <span>
            <strong>{checkResult.domain}</strong>:{' '}
            {checkResult.blocked ? '🚫 BLOCKED by VPN' : '✅ ALLOWED'}
          </span>
        </div>
      )}
      {checkResult?.error && (
        <p className="text-xs text-red-400">{checkResult.error}</p>
      )}

      {/* Stats */}
      <p className="text-[11px] text-sentinel-muted font-mono">
        {domainEntries.length} unique domains from {connections.length} connections
      </p>

      {/* Domain list */}
      <div className="max-h-64 overflow-y-auto space-y-0.5">
        {domainEntries.length === 0 && (
          <p className="text-center text-sentinel-muted text-xs py-6">
            {connections.length === 0
              ? 'No connections yet — browse a website'
              : 'No domains match filter'}
          </p>
        )}
        {domainEntries.map(c => (
          <div
            key={c.domain}
            className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 group transition-colors"
          >
            <span className={clsx(
              'w-1.5 h-1.5 rounded-full flex-shrink-0',
              c.flagged ? 'bg-red-400' : 'bg-sentinel-accent'
            )} />
            <span className="text-xs font-mono text-sentinel-text flex-1 truncate">
              {c.domain}
            </span>
            <span className="text-[10px] text-sentinel-muted opacity-0 group-hover:opacity-100 transition-opacity">
              {c.remote_addr}:{c.remote_port}
            </span>
            <span className={clsx(
              'text-[10px] font-mono',
              c.flagged ? 'text-red-400' : 'text-sentinel-muted'
            )}>
              {c.process_name || '—'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}