// pages\Dashboard.jsx — full implementation in Phase 6
// frontend/src/pages/Dashboard.jsx
import { StatsCards } from '../components/dashboard/StatsCards'
import { CPURamChart, NetworkChart } from '../components/dashboard/LiveCharts'
import { ThreatTimeline } from '../components/dashboard/ThreatTimeline'
import { DomainList } from '../components/network/DomainList'
import { Card, CardHeader } from '../components/ui/Card'

export function Dashboard() {
  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-sentinel-text">Dashboard</h1>
        <p className="text-xs text-sentinel-muted font-mono">Real-time system overview</p>
      </div>

      <StatsCards />

      <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
        <CPURamChart />
        <NetworkChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <ThreatTimeline />
        </div>
        <Card>
          <CardHeader title="Active Domains" subtitle="Live connections" />
          <DomainList />
        </Card>
      </div>
    </div>
  )
}