// components\monitor\ProcessTable.jsx — full implementation in Phase 6
// frontend/src/components/monitor/ProcessTable.jsx
import { useEffect, useState, useCallback } from 'react'
import { api } from '../../services/apiClient'
import { Button } from '../ui/Button'
import { truncate } from '../../utils/formatters'
import { RefreshCw, Skull, ShieldCheck } from 'lucide-react'
import clsx from 'clsx'

export function ProcessTable() {
  const [processes, setProcesses]   = useState([])
  const [loading, setLoading]       = useState(false)
  const [filter, setFilter]         = useState('')
  const [sortBy, setSortBy]         = useState('cpu_percent')
  const [killing, setKilling]       = useState(null)

  const fetchProcesses = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api.getProcesses()
      setProcesses(data)
    } catch (_err) {
      // silent
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProcesses()
    const t = setInterval(fetchProcesses, 5000)
    return () => clearInterval(t)
  }, [fetchProcesses])

  const kill = async (pid) => {
    setKilling(pid)
    try {
      await api.killProcess(pid)
      setProcesses(prev => prev.filter(p => p.pid !== pid))
    } catch (err) {
      console.error('Kill failed:', err)
    } finally {
      setKilling(null)
    }
  }

  const sorted = [...processes]
    .filter(p => p.name.toLowerCase().includes(filter.toLowerCase()))
    .sort((a, b) => (b[sortBy] ?? 0) - (a[sortBy] ?? 0))
    .slice(0, 100)

  const COLS = [
    { key: 'name',        label: 'Process' },
    { key: 'pid',         label: 'PID' },
    { key: 'cpu_percent', label: 'CPU%' },
    { key: 'memory_mb',   label: 'RAM MB' },
    { key: 'connections', label: 'Conns' },
    { key: 'threat_score',label: 'Risk' },
  ]

  return (
    <div className="space-y-3">
      <div className="flex gap-2 items-center">
        <input
          value={filter}
          onChange={e => setFilter(e.target.value)}
          placeholder="Filter processes..."
          className="flex-1 px-3 py-1.5 bg-sentinel-bg border border-sentinel-border rounded text-sm text-sentinel-text placeholder:text-sentinel-muted focus:outline-none focus:border-sentinel-accent"
        />
        <Button variant="ghost" onClick={fetchProcesses} disabled={loading}>
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
        </Button>
        <span className="text-xs text-sentinel-muted font-mono">{sorted.length} procs</span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-sentinel-border">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="bg-sentinel-surface border-b border-sentinel-border text-sentinel-muted">
              {COLS.map(col => (
                <th
                  key={col.key}
                  className="text-left px-3 py-2 cursor-pointer hover:text-sentinel-text transition-colors select-none"
                  onClick={() => setSortBy(col.key)}
                >
                  {col.label}
                  {sortBy === col.key && <span className="ml-1 text-sentinel-accent">↓</span>}
                </th>
              ))}
              <th className="text-left px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map(p => (
              <tr
                key={p.pid}
                className={clsx(
                  'border-b border-sentinel-border/40 hover:bg-white/5 transition-colors',
                  p.flagged && 'bg-red-500/5 border-red-500/20'
                )}
              >
                <td className="px-3 py-1.5">
                  <span className={p.flagged ? 'text-red-400 font-bold' : 'text-sentinel-text'}>
                    {truncate(p.name, 25)}
                  </span>
                </td>
                <td className="px-3 py-1.5 text-sentinel-muted">{p.pid}</td>
                <td className="px-3 py-1.5">
                  <span className={p.cpu_percent > 50 ? 'text-orange-400' : 'text-sentinel-text'}>
                    {p.cpu_percent.toFixed(1)}%
                  </span>
                </td>
                <td className="px-3 py-1.5 text-sentinel-text">{p.memory_mb.toFixed(0)}</td>
                <td className="px-3 py-1.5 text-sentinel-muted">{p.connections}</td>
                <td className="px-3 py-1.5">
                  <span className={clsx(
                    'px-1.5 py-0.5 rounded text-[10px] font-bold',
                    p.threat_score > 0.6 ? 'bg-red-500/20 text-red-400' :
                    p.threat_score > 0.3 ? 'bg-orange-500/20 text-orange-400' :
                    'bg-green-500/10 text-sentinel-green'
                  )}>
                    {p.flagged ? 'FLAGGED' : p.threat_score > 0 ? p.threat_score.toFixed(2) : 'CLEAN'}
                  </span>
                </td>
                <td className="px-3 py-1.5">
                  {p.flagged ? (
                    <Button
                      variant="danger"
                      onClick={() => kill(p.pid)}
                      disabled={killing === p.pid}
                    >
                      <Skull size={11} />
                      {killing === p.pid ? '...' : 'Kill'}
                    </Button>
                  ) : (
                    <span className="text-sentinel-green">
                      <ShieldCheck size={14} />
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}