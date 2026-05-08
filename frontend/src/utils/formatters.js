// frontend/src/utils/formatters.js

export function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

export function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
}

export function formatTimestamp(ts) {
  const d = new Date(ts * 1000)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export function formatDatetime(ts) {
  const d = new Date(ts * 1000)
  return d.toLocaleString()
}

export function formatPercent(val) {
  return `${Number(val).toFixed(1)}%`
}

export function formatNumber(n) {
  return Number(n).toLocaleString()
}

export function truncate(str, len = 40) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '…' : str
}

export function severityRank(sev) {
  return { critical: 4, high: 3, medium: 2, low: 1, info: 0 }[sev] ?? 0
}