// frontend/src/pages/NetworkXRay.jsx
import { useState, useEffect } from 'react'
import { ConnectionGraph } from '../components/network/ConnectionGraph'
import { PacketTable } from '../components/network/PacketTable'
import { DomainList } from '../components/network/DomainList'
import { Card, CardHeader } from '../components/ui/Card'
import { useSystemStats } from '../hooks/useSystemStats'
import { useNetworkStore } from '../store/networkStore'
import { formatNumber, formatBytes } from '../utils/formatters'
import { wsClient } from '../services/wsClient'
import { RefreshCw, Wifi } from 'lucide-react'

export function NetworkXRay() {
  const [tab, setTab]   = useState('table')
  const { totalPackets, bytesIn, bytesOut } = useSystemStats()
  const connections     = useNetworkStore(s => s.connections)
  const [lastRefresh, setLastRefresh] = useState(Date.now())

  // Auto-request connections when tab is opened
  useEffect(() => {
    wsClient.send('get_connections')
  }, [])

  const refresh = () => {
    wsClient.send('get_connections')
    setLastRefresh(Date.now())
  }

  const tabs = [
    { id: 'table',   label: `Connections (${connections.length})` },
    { id: 'graph',   label: 'Process Graph' },
    { id: 'domains', label: `Domains (${[...new Set(connections.map(c => c.domain).filter(Boolean))].length})` },
  ]

  return (
    <div className="space-y-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-sentinel-text">Network X-Ray</h1>
          <div className="flex items-center gap-1.5 text-xs text-sentinel-green">
            <Wifi size={12} className="animate-pulse" />
            <span className="font-mono">LIVE</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex gap-3 text-xs font-mono text-sentinel-muted">
            <span>PKT <span className="text-sentinel-accent">{formatNumber(totalPackets)}</span></span>
            <span>↓ <span className="text-sentinel-green">{formatBytes(bytesIn)}</span></span>
            <span>↑ <span className="text-orange-400">{formatBytes(bytesOut)}</span></span>
          </div>
          <button
            onClick={refresh}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded border border-sentinel-border text-sentinel-muted hover:text-sentinel-accent hover:border-sentinel-accent transition-colors text-xs"
          >
            <RefreshCw size={12} />
            Refresh
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 border-b border-sentinel-border">
        {tabs.map(t => (
          <button
            key={t.id}
            onClick={() => { setTab(t.id); if (t.id === 'table') refresh() }}
            className={`px-5 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id
                ? 'border-sentinel-accent text-sentinel-accent'
                : 'border-transparent text-sentinel-muted hover:text-sentinel-text'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {tab === 'table' && (
        <Card>
          <CardHeader
            title="Live Connections"
            subtitle="All tracked network connections — updates every 10s"
          />
          <PacketTable />
        </Card>
      )}

      {tab === 'graph' && (
        <Card>
          <CardHeader
            title="Process ↔ Domain Graph"
            subtitle="Drag nodes to rearrange — top 40 connections shown"
          />
          <ConnectionGraph />
        </Card>
      )}

      {tab === 'domains' && (
        <Card>
          <CardHeader
            title="Resolved Domains"
            subtitle="Unique domains from active connections"
          />
          <DomainList />
        </Card>
      )}
    </div>
  )
}