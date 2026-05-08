// components\settings\SettingsPanel.jsx — full implementation in Phase 6
// frontend/src/components/settings/SettingsPanel.jsx
import { useEffect, useState } from 'react'
import { api } from '../../services/apiClient'
import { Card, CardHeader } from '../ui/Card'
import { Button } from '../ui/Button'
import { Toggle } from '../ui/Toggle'
import { Save } from 'lucide-react'

export function SettingsPanel() {
  const [settings, setSettings]   = useState(null)
  const [saving, setSaving]       = useState(false)
  const [msg, setMsg]             = useState('')
  const [customBlock, setCustomBlock] = useState('')
  const [customAllow, setCustomAllow] = useState('')

  useEffect(() => {
    api.getSettings().then(setSettings).catch(() => {})
  }, [])

  const patch = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  const save = async () => {
    if (!settings) return
    setSaving(true)
    setMsg('')
    try {
      await api.updateSettings(settings)
      setMsg('Settings saved.')
    } catch (err) {
      setMsg(`Error: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  const addDomain = async (action) => {
    const domain = action === 'block' ? customBlock : customAllow
    if (!domain.trim()) return
    try {
      await api.getSettings() // just re-fetch
      const res = await fetch(`${import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8765/api'}/domains/custom`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ domain: domain.trim(), action }),
      })
      if (res.ok) {
        if (action === 'block') setCustomBlock('')
        else setCustomAllow('')
        setMsg(`Domain ${domain} added to ${action} list.`)
        const updated = await api.getSettings()
        setSettings(updated)
      }
    } catch (err) {
      setMsg(`Error: ${err.message}`)
    }
  }

  if (!settings) {
    return <div className="text-sentinel-muted text-sm text-center py-10">Loading settings...</div>
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <Card>
        <CardHeader title="General" />
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-sentinel-text">AI Anomaly Detection</p>
              <p className="text-xs text-sentinel-muted">Isolation Forest model</p>
            </div>
            <Toggle checked={settings.ai_enabled} onChange={v => patch('ai_enabled', v)} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-sentinel-text">Background Mode</p>
              <p className="text-xs text-sentinel-muted">Run in system tray when window closed</p>
            </div>
            <Toggle checked={settings.background_mode} onChange={v => patch('background_mode', v)} />
          </div>
          <div className="space-y-1">
            <label className="text-sm text-sentinel-text">
              Anomaly Threshold: <span className="text-sentinel-accent font-mono">{settings.anomaly_threshold}</span>
            </label>
            <input
              type="range" min={0.3} max={0.95} step={0.05}
              value={settings.anomaly_threshold}
              onChange={e => patch('anomaly_threshold', parseFloat(e.target.value))}
              className="w-full accent-sentinel-accent"
            />
            <div className="flex justify-between text-[10px] text-sentinel-muted">
              <span>Sensitive (0.3)</span>
              <span>Conservative (0.95)</span>
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-sm text-sentinel-text">Log Level</label>
            <select
              value={settings.log_level}
              onChange={e => patch('log_level', e.target.value)}
              className="w-full px-3 py-1.5 bg-sentinel-bg border border-sentinel-border rounded text-sm text-sentinel-text focus:outline-none focus:border-sentinel-accent"
            >
              {['DEBUG', 'INFO', 'WARNING', 'ERROR'].map(l => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader title="Custom Domain Rules" subtitle="Override blocklist decisions" />
        <div className="space-y-3">
          <div className="flex gap-2">
            <input
              value={customBlock}
              onChange={e => setCustomBlock(e.target.value)}
              placeholder="domain.com"
              className="flex-1 px-3 py-1.5 bg-sentinel-bg border border-sentinel-border rounded text-sm text-sentinel-text placeholder:text-sentinel-muted focus:outline-none focus:border-red-500"
            />
            <Button variant="danger" onClick={() => addDomain('block')}>Block</Button>
          </div>
          <div className="flex gap-2">
            <input
              value={customAllow}
              onChange={e => setCustomAllow(e.target.value)}
              placeholder="domain.com"
              className="flex-1 px-3 py-1.5 bg-sentinel-bg border border-sentinel-border rounded text-sm text-sentinel-text placeholder:text-sentinel-muted focus:outline-none focus:border-sentinel-green"
            />
            <Button variant="success" onClick={() => addDomain('allow')}>Allow</Button>
          </div>
          {settings.custom_block_domains?.length > 0 && (
            <div>
              <p className="text-xs text-sentinel-muted mb-1">Blocked:</p>
              <div className="flex flex-wrap gap-1">
                {settings.custom_block_domains.map(d => (
                  <span key={d} className="px-2 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 text-[11px] font-mono">{d}</span>
                ))}
              </div>
            </div>
          )}
          {settings.custom_allow_domains?.length > 0 && (
            <div>
              <p className="text-xs text-sentinel-muted mb-1">Allowed:</p>
              <div className="flex flex-wrap gap-1">
                {settings.custom_allow_domains.map(d => (
                  <span key={d} className="px-2 py-0.5 rounded bg-green-500/10 border border-green-500/30 text-sentinel-green text-[11px] font-mono">{d}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </Card>

      <div className="flex items-center gap-3">
        <Button onClick={save} disabled={saving}>
          <Save size={14} />
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
        {msg && (
          <span className={`text-xs ${msg.startsWith('Error') ? 'text-red-400' : 'text-sentinel-green'}`}>
            {msg}
          </span>
        )}
      </div>
    </div>
  )
}