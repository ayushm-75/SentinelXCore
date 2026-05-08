// frontend/src/components/network/PacketTable.jsx
import { useState } from 'react'
import { useNetworkStore } from '../../store/networkStore'
import { truncate, formatBytes } from '../../utils/formatters'
import { RefreshCw } from 'lucide-react'
import { wsClient } from '../../services/wsClient'
import clsx from 'clsx'

export function PacketTable() {
  const connections = useNetworkStore(s => s.connections)
  const [filter, setFilter] = useState('')

  const refresh = () => wsClient.send('get_connections')

  const filtered = connections.filter(c => {
    if (!filter) return true
    const q = filter.toLowerCase()
    return (
      c.process_name?.toLowerCase().includes(q) ||
      c.remote_addr?.includes(q) ||
      c.domain?.toLowerCase().includes(q) ||
      String(c.remote_port).includes(q)
    )
  })

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex gap-2 items-center">
        <input
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter by process, IP, domain, port..."
          className="flex-1 px-3 py-1.5 bg-sentinel-bg border border-sentinel-border rounded text-sm text-sentinel-text placeholder:text-sentinel-muted focus:outline-none focus:border-sentinel-accent font-mono"
        />
        <button
          onClick={refresh}
          className="p-1.5 rounded border border-sentinel-border text-sentinel-muted hover:text-sentinel-accent hover:border-sentinel-accent transition-colors"
          title="Refresh connections"
        >
          <RefreshCw size={14} />
        </button>
        <span className="text-xs font-mono text-sentinel-muted whitespace-nowrap">
          {filtered.length} / {connections.length}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-sentinel-border">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="bg-sentinel-surface border-b border-sentinel-border text-sentinel-muted text-left">
              <th className="px-3 py-2">Process</th>
              <th className="px-3 py-2">PID</th>
              <th className="px-3 py-2">Remote IP</th>
              <th className="px-3 py-2">Port</th>
              <th className="px-3 py-2">Domain / Hostname</th>
              <th className="px-3 py-2">Proto</th>
              <th className="px-3 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="text-center py-12 text-sentinel-muted">
                  <div className="space-y-2">
                    <p className="text-2xl">🌐</p>
                    <p>No connections yet</p>
                    <p className="text-[11px]">
                      Browse any website — connections appear automatically every 10s
                    </p>
                    <button
                      onClick={refresh}
                      className="mt-2 px-3 py-1 rounded border border-sentinel-border text-sentinel-accent hover:bg-sentinel-accent/10 transition-colors text-xs"
                    >
                      Refresh Now
                    </button>
                  </div>
                </td>
              </tr>
            )}
            {filtered.map((c, i) => (
              <tr
                key={`${c.pid}-${c.remote_addr}-${c.remote_port}-${i}`}
                className={clsx(
                  'border-b border-sentinel-border/40 hover:bg-white/5 transition-colors',
                  c.flagged && 'bg-red-500/5 border-l-2 border-l-red-500'
                )}
              >
                <td className="px-3 py-1.5">
                  <span className={c.flagged ? 'text-red-400 font-bold' : 'text-sentinel-text'}>
                    {truncate(c.process_name || 'unknown', 22)}
                  </span>
                </td>
                <td className="px-3 py-1.5 text-sentinel-muted">{c.pid || '—'}</td>
                <td className="px-3 py-1.5 text-sentinel-accent">{c.remote_addr}</td>
                <td className="px-3 py-1.5 text-sentinel-muted">{c.remote_port}</td>
                <td className="px-3 py-1.5 text-sentinel-text max-w-xs">
                  {truncate(c.domain || '—', 35)}
                </td>
                <td className="px-3 py-1.5">
                  <span className={clsx(
                    'px-1.5 py-0.5 rounded text-[10px] border',
                    c.protocol === 'TCP'
                      ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                      : 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                  )}>
                    {c.protocol}
                  </span>
                </td>
                <td className="px-3 py-1.5">
                  {c.flagged
                    ? <span className="text-red-400 font-bold animate-pulse">⚠ FLAGGED</span>
                    : <span className="text-sentinel-green">✓ OK</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}