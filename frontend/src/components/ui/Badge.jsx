// components\ui\Badge.jsx — full implementation in Phase 6
// frontend/src/components/ui/Badge.jsx
import { SEVERITY_BG } from '../../utils/constants'
import clsx from 'clsx'

export function Badge({ severity, children, className }) {
  const base = SEVERITY_BG[severity] ?? SEVERITY_BG.info
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded text-xs font-mono font-medium border',
      base, className
    )}>
      {children}
    </span>
  )
}

export function StatusDot({ active, className }) {
  return (
    <span className={clsx(
      'inline-block w-2 h-2 rounded-full',
      active ? 'bg-sentinel-green animate-pulse-slow' : 'bg-sentinel-muted',
      className
    )} />
  )
}