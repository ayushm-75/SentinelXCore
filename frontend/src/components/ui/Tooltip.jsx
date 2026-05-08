// components\ui\Tooltip.jsx — full implementation in Phase 6
// frontend/src/components/ui/Tooltip.jsx
import { useState } from 'react'
import clsx from 'clsx'

export function Tooltip({ text, children, position = 'top' }) {
  const [visible, setVisible] = useState(false)

  const posClass = {
    top:    'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left:   'right-full top-1/2 -translate-y-1/2 mr-2',
    right:  'left-full top-1/2 -translate-y-1/2 ml-2',
  }[position] ?? 'bottom-full left-1/2 -translate-x-1/2 mb-2'

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div className={clsx(
          'absolute z-50 whitespace-nowrap pointer-events-none',
          'px-2 py-1 text-xs rounded bg-gray-900 text-sentinel-text border border-sentinel-border',
          posClass
        )}>
          {text}
        </div>
      )}
    </div>
  )
}