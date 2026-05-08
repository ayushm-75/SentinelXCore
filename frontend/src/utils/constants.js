// frontend/src/utils/constants.js
export const WS_URL = 'ws://127.0.0.1:8765/ws'
export const API_BASE = 'http://127.0.0.1:8765/api'

export const SEVERITY_COLORS = {
  critical: '#ff4444',
  high:     '#ff8c00',
  medium:   '#ffd700',
  low:      '#00d4ff',
  info:     '#6b7280',
}

export const SEVERITY_BG = {
  critical: 'bg-red-500/20 border-red-500/40 text-red-400',
  high:     'bg-orange-500/20 border-orange-500/40 text-orange-400',
  medium:   'bg-yellow-500/20 border-yellow-500/40 text-yellow-400',
  low:      'bg-blue-500/20 border-blue-500/40 text-blue-400',
  info:     'bg-gray-500/20 border-gray-500/40 text-gray-400',
}

export const CATEGORY_ICONS = {
  network: '🌐',
  process: '⚙️',
  file:    '📄',
  ai:      '🤖',
}

export const NAV_ITEMS = [
  { id: 'dashboard',  label: 'Dashboard',       icon: 'LayoutDashboard' },
  { id: 'network',    label: 'Network X-Ray',   icon: 'Network' },
  { id: 'threats',    label: 'Threats',          icon: 'Shield' },
  { id: 'vpn',        label: 'VPN / AdBlock',   icon: 'Lock' },
  { id: 'monitor',    label: 'System Monitor',  icon: 'Monitor' },
  { id: 'settings',  label: 'Settings',         icon: 'Settings' },
]