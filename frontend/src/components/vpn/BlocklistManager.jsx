// components\vpn\BlocklistManager.jsx — full implementation in Phase 6
// frontend/src/components/vpn/BlocklistManager.jsx
import { useEffect, useState } from 'react'
import { api } from '../../services/apiClient'
import { Card, CardHeader } from '../ui/Card'
import { Button } from '../ui/Button'
import { Toggle } from '../ui/Toggle'
import { formatNumber } from '../../utils/formatters'
import { RefreshCw, Download } from 'lucide-react'

const LIST_INFO = {
  adguard:    { name: 'AdGuard DNS Filter',         desc: 'Ads, tracking, malware — DNS optimized' },
  easylist:   { name: 'EasyList',                   desc: 'Primary ad blocking list' },
  easyprivacy:{ name: 'EasyPrivacy',                desc: 'Anti-tracking & privacy' },
  hagezi:     { name: 'HaGeZi Pro++ Blocklist',     desc: 'Aggressive: ads, phishing, scam, malware' },
}

export function BlocklistManager() {
  const [meta, setMeta]           = useState({})
  const [active, setActive]       = useState([])
  const [saving, setSaving]       = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [msg, setMsg]             = useState('')

  useEffect(() => {
    api.getListsMeta().then(setMeta).catch(() => {})
    api.vpnStatus().then(s => setActive(s.active_lists ?? [])).catch(() => {})
  }, [])

  const toggleList = (id) => {
    setActive(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const save = async () => {
    setSaving(true)
    setMsg('')
    try {
      await api.selectLists(active)
      setMsg('Preferences saved.')
    } catch (err) {
      setMsg(`Error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const download = async () => {
    setDownloading(true)
    setMsg('')
    try {
      await api.updateLists()
      setMsg('Download started in background. Check back in a minute.')
    } catch (err) {
      setMsg(`Error: ${err.message}`)
    } finally {
      setDownloading(false)
    }
  }

  return (
    <Card>
      <CardHeader
        title="Filter Lists"
        subtitle="Select active blocklists"
        action={
          <div className="flex gap-2">
            <Button variant="ghost" onClick={download} disabled={downloading}>
              <Download size={13} />
              {downloading ? 'Starting...' : 'Update'}
            </Button>
            <Button onClick={save} disabled={saving}>
              <RefreshCw size={13} className={saving ? 'animate-spin' : ''} />
              {saving ? 'Saving...' : 'Apply'}
            </Button>
          </div>
        }
      />

      <div className="space-y-3">
        {Object.entries(LIST_INFO).map(([id, info]) => {
          const m = meta[id] ?? {}
          return (
            <div key={id} className="flex items-start gap-3 p-3 rounded-lg border border-sentinel-border hover:border-sentinel-muted/30 transition-colors">
              <Toggle
                checked={active.includes(id)}
                onChange={() => toggleList(id)}
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-sentinel-text">{info.name}</p>
                <p className="text-xs text-sentinel-muted">{info.desc}</p>
                <div className="flex gap-4 mt-1 text-[11px] font-mono text-sentinel-muted">
                  {m.entry_count > 0 && (
                    <span className="text-sentinel-accent">{formatNumber(m.entry_count)} domains</span>
                  )}
                  {m.last_updated && <span>Updated: {m.last_updated.slice(0, 10)}</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {msg && (
        <p className={`mt-3 text-xs rounded p-2 border ${
          msg.startsWith('Error')
            ? 'text-red-400 bg-red-500/10 border-red-500/30'
            : 'text-sentinel-green bg-green-500/10 border-green-500/30'
        }`}>
          {msg}
        </p>
      )}
    </Card>
  )
}