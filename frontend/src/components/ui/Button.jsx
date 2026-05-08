// components\ui\Button.jsx — full implementation in Phase 6
// frontend/src/components/ui/Button.jsx
import clsx from 'clsx'

const VARIANTS = {
  primary:  'bg-sentinel-accent/20 border-sentinel-accent/50 text-sentinel-accent hover:bg-sentinel-accent/30',
  danger:   'bg-red-500/20 border-red-500/50 text-red-400 hover:bg-red-500/30',
  success:  'bg-green-500/20 border-green-500/50 text-sentinel-green hover:bg-green-500/30',
  ghost:    'bg-transparent border-sentinel-border text-sentinel-muted hover:text-sentinel-text hover:border-sentinel-muted',
  warning:  'bg-orange-500/20 border-orange-500/50 text-orange-400 hover:bg-orange-500/30',
}

export function Button({ variant = 'primary', className, disabled, children, onClick, type = 'button' }) {
  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={clsx(
        'inline-flex items-center gap-2 px-3 py-1.5 rounded border text-sm font-medium',
        'transition-all duration-150 cursor-pointer',
        'disabled:opacity-40 disabled:cursor-not-allowed',
        VARIANTS[variant] ?? VARIANTS.primary,
        className
      )}
    >
      {children}
    </button>
  )
}