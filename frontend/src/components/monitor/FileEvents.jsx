// components\monitor\FileEvents.jsx — full implementation in Phase 6
// frontend/src/components/monitor/FileEvents.jsx
import { useEffect, useState } from 'react'
import { wsClient } from '../../services/wsClient'
import { formatTimestamp, truncate } from '../../utils/formatters'
import { FileWarning, FileCheck } from 'lucide-react'

export function FileEvents() {
  const [events, setEvents] = useState([])

  useEffect(() => {
    const off = wsClient.on('file.scanned', (msg) => {
      const data = msg.data ?? msg
      setEvents(prev => [{ ...data, ts: Date.now() / 1000 }, ...prev].slice(0, 50))
    })
    return off
  }, [])

  return (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {events.length === 0 && (
        <p className="text-center text-sentinel-muted text-xs py-6">
          No file events yet — watching Downloads & Desktop
        </p>
      )}
      {events.map((e, i) => (
        <div
          key={`${e.path}-${i}`}
          className={`flex items-start gap-2 p-2 rounded border text-xs ${
            e.suspicious
              ? 'border-orange-500/30 bg-orange-500/5'
              : 'border-sentinel-border bg-sentinel-surface'
          }`}
        >
          {e.suspicious
            ? <FileWarning size={14} className="text-orange-400 mt-0.5 flex-shrink-0" />
            : <FileCheck   size={14} className="text-sentinel-green mt-0.5 flex-shrink-0" />}
          <div className="flex-1 min-w-0">
            <p className="font-mono text-sentinel-text">{truncate(e.path ?? '', 50)}</p>
            {e.suspicious && (
              <p className="text-orange-400 text-[11px]">{(e.reasons ?? []).join(', ')}</p>
            )}
            <p className="text-sentinel-muted text-[10px] mt-0.5">
              Entropy: {(e.entropy ?? 0).toFixed(2)} | {formatTimestamp(e.ts)}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}