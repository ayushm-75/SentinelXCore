// pages\SystemMonitor.jsx — full implementation in Phase 6
// frontend/src/pages/SystemMonitor.jsx
import { SystemCharts } from '../components/monitor/SystemCharts'
import { ProcessTable } from '../components/monitor/ProcessTable'
import { FileEvents } from '../components/monitor/FileEvents'
import { Card, CardHeader } from '../components/ui/Card'
import { useSystemStats } from '../hooks/useSystemStats'
import { formatBytes } from '../utils/formatters'

export function SystemMonitor() {
  const { ramMb, disk } = useSystemStats()

  return (
    <div className="space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold text-sentinel-text">System Monitor</h1>
        <div className="text-xs font-mono text-sentinel-muted">
          RAM: <span className="text-sentinel-accent">{formatBytes(ramMb * 1024 * 1024)}</span>
          &nbsp;&nbsp;Disk: <span className="text-sentinel-accent">{disk.toFixed(1)}%</span>
        </div>
      </div>

      <SystemCharts />

      <Card>
        <CardHeader title="Processes" subtitle="Sorted by CPU — click column to sort" />
        <ProcessTable />
      </Card>

      <Card>
        <CardHeader title="File Events" subtitle="Downloads & Desktop monitoring" />
        <FileEvents />
      </Card>
    </div>
  )
}