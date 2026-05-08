// components\monitor\SystemCharts.jsx — full implementation in Phase 6
// frontend/src/components/monitor/SystemCharts.jsx
import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts'
import { useSystemStats } from '../../hooks/useSystemStats'
import { Card } from '../ui/Card'

function GaugeChart({ value, label, color, max = 100 }) {
  const pct  = Math.min((value / max) * 100, 100)
  const data = [{ value: pct, fill: color }]

  return (
    <Card className="flex flex-col items-center p-4">
      <div style={{ width: 120, height: 120 }}>
        <ResponsiveContainer>
          <RadialBarChart
            cx="50%" cy="50%"
            innerRadius="65%" outerRadius="90%"
            startAngle={210} endAngle={-30}
            data={data}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
            <RadialBar
              dataKey="value"
              cornerRadius={4}
              background={{ fill: '#1f2937' }}
            />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xl font-bold font-mono -mt-2" style={{ color }}>
        {value.toFixed(1)}%
      </p>
      <p className="text-xs text-sentinel-muted mt-1">{label}</p>
    </Card>
  )
}

export function SystemCharts() {
  const { cpu, ram, disk } = useSystemStats()

  return (
    <div className="grid grid-cols-3 gap-3">
      <GaugeChart value={cpu}  label="CPU"  color={cpu > 80  ? '#ff4444' : '#00d4ff'} />
      <GaugeChart value={ram}  label="RAM"  color={ram > 85  ? '#ff4444' : '#a855f7'} />
      <GaugeChart value={disk} label="Disk" color={disk > 90 ? '#ff4444' : '#00ff88'} />
    </div>
  )
}