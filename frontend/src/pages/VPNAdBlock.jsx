// pages\VPNAdBlock.jsx — full implementation in Phase 6
// frontend/src/pages/VPNAdBlock.jsx
import { VPNToggle } from '../components/vpn/VPNToggle'
import { BlocklistManager } from '../components/vpn/BlocklistManager'
import { useState } from 'react'
import { api } from '../services/apiClient'
import { Button } from '../components/ui/Button'
import { Card, CardHeader } from '../components/ui/Card'
import { Search } from 'lucide-react'

export function VPNAdBlock() {
  const [domain, setDomain]       = useState('')
  const [result, setResult]       = useState(null)
  const [checking, setChecking]   = useState(false)

  const check = async () => {
    if (!domain.trim()) return
    setChecking(true)
    try {
      const r = await api.checkDomain(domain.trim())
      setResult(r)
    } catch (_err) {
      setResult({ error: 'Check failed' })
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="space-y-4 p-4 max-w-3xl">
      <h1 className="text-lg font-bold text-sentinel-text">VPN / Ad-Block</h1>

      <VPNToggle />

      <Card>
        <CardHeader title="Domain Lookup" subtitle="Check if a domain is blocked" />
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-2.5 top-2.5 text-sentinel-muted" />
            <input
              value={domain}
              onChange={e => { setDomain(e.target.value); setResult(null) }}
              onKeyDown={e => e.key === 'Enter' && check()}
              placeholder="ads.example.com"
              className="w-full pl-8 pr-3 py-2 bg-sentinel-bg border border-sentinel-border rounded text-sm text-sentinel-text placeholder:text-sentinel-muted focus:outline-none focus:border-sentinel-accent"
            />
          </div>
          <Button onClick={check} disabled={checking || !domain.trim()}>
            {checking ? 'Checking...' : 'Check'}
          </Button>
        </div>
        {result && !result.error && (
          <div className={`mt-3 p-3 rounded border text-sm font-mono ${
            result.blocked
              ? 'bg-red-500/10 border-red-500/30 text-red-400'
              : 'bg-green-500/10 border-green-500/30 text-sentinel-green'
          }`}>
            <strong>{result.domain}</strong> → {result.blocked ? '🚫 BLOCKED' : '✅ ALLOWED'}
          </div>
        )}
        {result?.error && (
          <p className="mt-2 text-xs text-red-400">{result.error}</p>
        )}
      </Card>

      <BlocklistManager />
    </div>
  )
}