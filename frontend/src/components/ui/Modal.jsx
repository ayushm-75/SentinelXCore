// components\ui\Modal.jsx — full implementation in Phase 6
// frontend/src/components/ui/Modal.jsx
import { useEffect } from 'react'
import { X } from 'lucide-react'
import clsx from 'clsx'

export function Modal({ open, onClose, title, children, width = 'max-w-lg' }) {
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    if (open) document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className={clsx(
        'relative z-10 w-full mx-4 rounded-xl border border-sentinel-border',
        'bg-sentinel-surface shadow-2xl',
        width
      )}>
        <div className="flex items-center justify-between p-4 border-b border-sentinel-border">
          <h2 className="text-sm font-semibold text-sentinel-text">{title}</h2>
          <button
            onClick={onClose}
            className="text-sentinel-muted hover:text-sentinel-text transition-colors"
          >
            <X size={16} />
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  )
}