// frontend/src/components/layout/Sidebar.jsx
import clsx from 'clsx'
import {
  LayoutDashboard, Network, Shield, Lock,
  Monitor, Settings, Activity
} from 'lucide-react'
import { useAppStore } from '../../store/appStore'
import { useAlerts } from '../../hooks/useAlerts'

const ICONS = { LayoutDashboard, Network, Shield, Lock, Monitor, Settings }

const NAV = [
  { id: 'dashboard', label: 'Dashboard',     icon: 'LayoutDashboard' },
  { id: 'network',   label: 'Network X-Ray', icon: 'Network' },
  { id: 'threats',   label: 'Threats',        icon: 'Shield' },
  { id: 'vpn',       label: 'VPN / AdBlock', icon: 'Lock' },
  { id: 'monitor',   label: 'System Monitor',icon: 'Monitor' },
  { id: 'settings',  label: 'Settings',       icon: 'Settings' },
]

export function Sidebar() {
  const activePage  = useAppStore(s => s.activePage)
  const setPage     = useAppStore(s => s.setActivePage)
  const { unread }  = useAlerts()

  return (
    <aside className="w-16 lg:w-56 h-screen bg-sentinel-surface border-r border-sentinel-border flex flex-col flex-shrink-0">
      {/* Logo */}
      <div className="h-14 flex items-center justify-center lg:justify-start px-4 border-b border-sentinel-border">
        <Activity className="text-sentinel-accent" size={22} />
        <span className="hidden lg:block ml-2 font-mono font-bold text-sentinel-accent tracking-widest text-sm">
          SENTINEL<span className="text-sentinel-green">X</span>
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {NAV.map(item => {
          const Icon    = ICONS[item.icon]
          const active  = activePage === item.id
          const hasAlert = item.id === 'threats' && unread > 0

          return (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              className={clsx(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-150 group relative',
                active
                  ? 'bg-sentinel-accent/10 text-sentinel-accent border border-sentinel-accent/30'
                  : 'text-sentinel-muted hover:text-sentinel-text hover:bg-white/5 border border-transparent'
              )}
            >
              <Icon size={18} className="flex-shrink-0" />
              <span className="hidden lg:block text-sm font-medium">{item.label}</span>
              {hasAlert && (
                <span className="absolute top-1.5 right-1.5 lg:relative lg:top-auto lg:right-auto lg:ml-auto">
                  <span className="flex h-4 w-4 lg:h-5 lg:w-5 items-center justify-center rounded-full bg-red-500 text-white text-[10px] font-bold">
                    {unread > 99 ? '99+' : unread}
                  </span>
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Version */}
      <div className="p-3 border-t border-sentinel-border">
        <p className="hidden lg:block text-[10px] text-sentinel-muted font-mono text-center">
          v1.0.0 — LOCAL ONLY
        </p>
      </div>
    </aside>
  )
}