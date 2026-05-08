// components\overlay\OverlayWindow.jsx — full implementation in Phase 6
// frontend/src/components/overlay/OverlayWindow.jsx
import { useSystemStats } from '../../hooks/useSystemStats'
import { useAlerts } from '../../hooks/useAlerts'
import { useAppStore } from '../../store/appStore'
import { formatBytes, formatNumber } from '../../utils/formatters'
import { X, ShieldCheck, ShieldOff } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export function OverlayWindow() {
  const overlayMode  = useAppStore(s => s.overlayMode)
  const toggleOverlay = useAppStore(s => s.toggleOverlay)
  const { cpu, ram, vpnActive, blocked, connections } = useSystemStats()
  const { unread } = useAlerts()

  return (
    <AnimatePresence>
      {overlayMode && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: -20 }}
          animate={{ opacity: 1, scale: 1,   y: 0 }}
          exit={{   opacity: 0, scale: 0.9,   y: -20 }}
          transition={{ duration: 0.15 }}
          className="fixed top-4 right-4 z-50 w-56 rounded-xl border border-sentinel-accent/30 bg-sentinel-bg/95 backdrop-blur-md shadow-2xl"
          style={{ boxShadow: '0 0 20px #00d4ff22' }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 border-b border-sentinel-border">
            <span className="font-mono text-xs font-bold text-sentinel-accent tracking-widest">
              SENTINEL<span className="text-sentinel-green">X</span>
            </span>
            <button onClick={toggleOverlay} className="text-sentinel-muted hover:text-sentinel-text">
              <X size={13} />
            </button>
          </div>

          {/* Stats */}
          <div className="p-3 space-y-2 font-mono text-xs">
            <div className="flex justify-between">
              <span className="text-sentinel-muted">CPU</span>
              <span className={cpu > 80 ? 'text-red-400' : 'text-sentinel-text'}>{cpu.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sentinel-muted">RAM</span>
              <span className={ram > 85 ? 'text-red-400' : 'text-sentinel-text'}>{ram.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sentinel-muted">CONNS</span>
              <span className="text-sentinel-accent">{formatNumber(connections)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sentinel-muted">BLOCKED</span>
              <span className="text-red-400">{formatNumber(blocked)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sentinel-muted">ALERTS</span>
              <span className={unread > 0 ? 'text-orange-400 font-bold' : 'text-sentinel-green'}>
                {unread > 0 ? `${unread} UNREAD` : 'CLEAN'}
              </span>
            </div>
            <div className="flex justify-between items-center pt-1 border-t border-sentinel-border">
              <span className="text-sentinel-muted">VPN</span>
              <span className={`flex items-center gap-1 ${vpnActive ? 'text-sentinel-green' : 'text-sentinel-muted'}`}>
                {vpnActive ? <ShieldCheck size={11} /> : <ShieldOff size={11} />}
                {vpnActive ? 'ON' : 'OFF'}
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}