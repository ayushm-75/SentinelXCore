// components\ui\Toggle.jsx — full implementation in Phase 6
// frontend/src/components/ui/Toggle.jsx
import clsx from 'clsx'

export function Toggle({ checked, onChange, disabled, label }) {
  return (
    <label className={clsx(
      'inline-flex items-center gap-3 cursor-pointer select-none',
      disabled && 'opacity-40 cursor-not-allowed'
    )}>
      <div
        role="switch"
        aria-checked={checked}
        onClick={() => !disabled && onChange(!checked)}
        className={clsx(
          'relative w-11 h-6 rounded-full border transition-all duration-200',
          checked
            ? 'bg-sentinel-accent/30 border-sentinel-accent'
            : 'bg-sentinel-border border-sentinel-border',
        )}
      >
        <span className={clsx(
          'absolute top-0.5 left-0.5 w-5 h-5 rounded-full transition-all duration-200',
          checked
            ? 'translate-x-5 bg-sentinel-accent shadow-[0_0_8px_#00d4ff]'
            : 'translate-x-0 bg-sentinel-muted'
        )} />
      </div>
      {label && <span className="text-sm text-sentinel-text">{label}</span>}
    </label>
  )
}