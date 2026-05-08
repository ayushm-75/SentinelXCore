// frontend/src/components/SplashScreen.jsx
import { useEffect, useRef } from 'react'
import { wsClient } from '../services/wsClient'

const SPLASH_TIMEOUT_MS = 6000

export function SplashScreen({ children }) {
  const splashRef    = useRef(null)
  const dismissedRef = useRef(false)

  const dismiss = () => {
    if (dismissedRef.current) return
    dismissedRef.current = true
    const el = splashRef.current
    if (!el) return
    el.style.transition = 'opacity 0.35s ease'
    el.style.opacity    = '0'
    setTimeout(() => {
      if (splashRef.current) splashRef.current.style.display = 'none'
    }, 350)
  }

  useEffect(() => {
    // Check synchronously — WS may already be connected
    // because useWebSocket() in App runs before this effect
    if (wsClient.connected) {
      dismiss()
      return
    }

    // Subscribe to future connect events
    const unsub = wsClient.on('connected', (isConnected) => {
      if (isConnected) dismiss()
    })

    // Hard timeout fallback
    const timer = setTimeout(dismiss, SPLASH_TIMEOUT_MS)

    return () => {
      unsub()
      clearTimeout(timer)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <div
        ref={splashRef}
        style={{
          position:        'fixed',
          inset:           0,
          zIndex:          9999,
          display:         'flex',
          flexDirection:   'column',
          alignItems:      'center',
          justifyContent:  'center',
          backgroundColor: '#0a0e1a',
        }}
      >
        <div style={{
          display:       'flex',
          flexDirection: 'column',
          alignItems:    'center',
          gap:           '32px',
        }}>

          <svg width="96" height="96" viewBox="0 0 100 100">
            <polygon
              points="50,5 95,25 95,60 50,95 5,60 5,25"
              fill="rgba(0,212,255,0.08)"
              stroke="#00d4ff"
              strokeWidth="2"
            />
            <polygon
              points="50,15 85,32 85,58 50,85 15,58 15,32"
              fill="none"
              stroke="#00d4ff"
              strokeWidth="1.5"
              opacity="0.5"
            />
            <line x1="34" y1="34" x2="66" y2="66"
                  stroke="#00ff88" strokeWidth="5" strokeLinecap="round" />
            <line x1="66" y1="34" x2="34" y2="66"
                  stroke="#00ff88" strokeWidth="5" strokeLinecap="round" />
          </svg>

          <div style={{ textAlign: 'center' }}>
            <div style={{
              fontSize:      '2.25rem',
              fontWeight:    700,
              color:         '#ffffff',
              letterSpacing: '0.3em',
              fontFamily:    'system-ui, sans-serif',
            }}>
              SENTINEL<span style={{ color: '#00d4ff' }}>X</span>
            </div>
            <div style={{
              fontSize:      '0.7rem',
              color:         '#00d4ff',
              letterSpacing: '0.25em',
              marginTop:     '6px',
              opacity:       0.65,
              fontFamily:    'system-ui, sans-serif',
            }}>
              CORE SECURITY ENGINE
            </div>
          </div>

          <SpinnerInline />

          <div style={{
            color:         '#6b7280',
            fontSize:      '0.72rem',
            letterSpacing: '0.08em',
            fontFamily:    'system-ui, sans-serif',
          }}>
            Starting security engine...
          </div>

          <ScanBar />
        </div>
      </div>

      {children}
    </>
  )
}

function SpinnerInline() {
  const ref = useRef(null)
  useEffect(() => {
    if (!ref.current) return
    let angle = 0
    const id  = setInterval(() => {
      angle = (angle + 8) % 360
      if (ref.current) ref.current.style.transform = `rotate(${angle}deg)`
    }, 16)
    return () => clearInterval(id)
  }, [])
  return (
    <div ref={ref} style={{
      width:        '32px',
      height:       '32px',
      borderRadius: '50%',
      border:       '2px solid rgba(0,212,255,0.15)',
      borderTop:    '2px solid #00d4ff',
    }} />
  )
}

function ScanBar() {
  const ref = useRef(null)
  useEffect(() => {
    if (!ref.current) return
    let x    = -80
    const id = setInterval(() => {
      x += 2.5
      if (x > 260) x = -80
      if (ref.current) ref.current.style.transform = `translateX(${x}px)`
    }, 16)
    return () => clearInterval(id)
  }, [])
  return (
    <div style={{
      width:    '220px',
      height:   '1px',
      background: 'rgba(0,212,255,0.08)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <div ref={ref} style={{
        position:   'absolute',
        top:        0,
        left:       0,
        width:      '80px',
        height:     '100%',
        background: 'linear-gradient(90deg, transparent, #00d4ff, transparent)',
      }} />
    </div>
  )
}