// frontend/src/services/apiClient.js
import { API_BASE } from '../utils/constants'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  // Health
  health:      ()             => request('/health'),
  snapshot:    ()             => request('/snapshot'),

  // Alerts
  getAlerts:   (limit = 100) => request(`/alerts?limit=${limit}`),
  ackAlert:    (id)           => request('/alerts/acknowledge', {
    method: 'POST', body: JSON.stringify({ alert_id: id }),
  }),

  // Connections
  getConnections: (limit = 100) => request(`/connections?limit=${limit}`),

  // Processes
  getProcesses:   ()            => request('/processes'),
  killProcess:    (pid)         => request('/processes/kill', {
    method: 'POST', body: JSON.stringify({ pid }),
  }),

  // VPN
  vpnStatus:      ()            => request('/vpn/status'),
  vpnToggle:      (enabled)     => request('/vpn/toggle', {
    method: 'POST', body: JSON.stringify({ enabled }),
  }),
  selectLists:    (lists)       => request('/vpn/blocklists/select', {
    method: 'POST', body: JSON.stringify({ active_lists: lists }),
  }),
  updateLists:    ()            => request('/vpn/blocklists/update', { method: 'POST' }),
  getListsMeta:   ()            => request('/vpn/blocklists/meta'),
  checkDomain:    (domain)      => request(`/domains/check/${encodeURIComponent(domain)}`),

  // Settings
  getSettings:    ()            => request('/settings'),
  updateSettings: (updates)     => request('/settings/update', {
    method: 'POST', body: JSON.stringify({ updates }),
  }),

  // Stats
  statsHistory:   ()            => request('/stats/history'),
}