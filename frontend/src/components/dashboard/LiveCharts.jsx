// components\dashboard\LiveCharts.jsx — full implementation in Phase 6
// frontend/src/components/dashboard/LiveCharts.jsx
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { useNetworkStore } from '../../store/networkStore'
import { Card, CardHeader } from '../ui/Card'

const GRID_STYLE  = { stroke: '#1f2937', strokeDasharray: '3 3' }
const AXIS_STYLE  = { fill: '#6b7280', fontSize: 10 }
const TIP_STYLE   = {
  backgroundColor: '#111827',
  border:          '1px solid #1f2937',
  borderRadius:    6,
  fontSize:        11,
  color:           '#e5e7eb',
}

export function CPURamChart() {
  const history = useNetworkStore(s => s.statsHistory)

  return (
    <Card className="col-span-2">
      <CardHeader title="CPU & RAM (%)" subtitle="Live — last 2 minutes" />
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={history} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="gradCPU" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#00d4ff" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradRAM" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#a855f7" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid {...GRID_STYLE} />
          <XAxis dataKey="time" tick={AXIS_STYLE} interval="preserveStartEnd" />
          <YAxis domain={[0, 100]} tick={AXIS_STYLE} unit="%" />
          <Tooltip contentStyle={TIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Area type="monotone" dataKey="cpu" name="CPU" stroke="#00d4ff" fill="url(#gradCPU)" strokeWidth={2} dot={false} isAnimationActive={false} />
          <Area type="monotone" dataKey="ram" name="RAM" stroke="#a855f7" fill="url(#gradRAM)" strokeWidth={2} dot={false} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  )
}

export function NetworkChart() {
  const history = useNetworkStore(s => s.statsHistory)

  const formatted = history.map(h => ({
    ...h,
    bytesIn:  Math.round((h.bytesIn  ?? 0) / 1024),
    bytesOut: Math.round((h.bytesOut ?? 0) / 1024),
  }))

  return (
    <Card className="col-span-2">
      <CardHeader title="Network I/O (KB)" subtitle="Cumulative bytes" />
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={formatted} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="gradIn" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#00ff88" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00ff88" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradOut" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#ff8c00" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ff8c00" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid {...GRID_STYLE} />
          <XAxis dataKey="time" tick={AXIS_STYLE} interval="preserveStartEnd" />
          <YAxis tick={AXIS_STYLE} unit=" KB" />
          <Tooltip contentStyle={TIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Area type="monotone" dataKey="bytesIn"  name="In"  stroke="#00ff88" fill="url(#gradIn)"  strokeWidth={2} dot={false} isAnimationActive={false} />
          <Area type="monotone" dataKey="bytesOut" name="Out" stroke="#ff8c00" fill="url(#gradOut)" strokeWidth={2} dot={false} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  )
}