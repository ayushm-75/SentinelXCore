// components\ui\Card.jsx — full implementation in Phase 6
// frontend/src/components/ui/Card.jsx
import clsx from 'clsx'

export function Card({ children, className, glow }) {
  return (
    <div className={clsx(
      'rounded-lg border border-sentinel-border bg-sentinel-surface p-4',
      glow && 'glow-accent',
      className
    )}>
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-sm font-semibold text-sentinel-text tracking-wide">{title}</h3>
        {subtitle && <p className="text-xs text-sentinel-muted mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}