// frontend/src/App.jsx
import { useEffect, useRef } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
import { useAppStore } from './store/appStore'
import { Sidebar } from './components/layout/Sidebar'
import { TopBar } from './components/layout/TopBar'
import { StatusBar } from './components/layout/StatusBar'
import { OverlayWindow } from './components/overlay/OverlayWindow'
import { Dashboard } from './pages/Dashboard'
import { NetworkXRay } from './pages/NetworkXRay'
import { Threats } from './pages/Threats'
import { VPNAdBlock } from './pages/VPNAdBlock'
import { SystemMonitor } from './pages/SystemMonitor'
import { Settings } from './pages/Settings'

const PAGES = {
  dashboard: Dashboard,
  network:   NetworkXRay,
  threats:   Threats,
  vpn:       VPNAdBlock,
  monitor:   SystemMonitor,
  settings:  Settings,
}

function PageContent() {
  const activePage = useAppStore(s => s.activePage)
  const Component  = PAGES[activePage] ?? Dashboard
  return <Component />
}

export default function App() {
  useWebSocket()

  const toggleOverlay = useAppStore(s => s.toggleOverlay)
  const hotkeyRef     = useRef(toggleOverlay)

  useEffect(() => {
    hotkeyRef.current = toggleOverlay
  }, [toggleOverlay])

  useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'S') {
        e.preventDefault()
        hotkeyRef.current()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  return (
    <div className="flex h-screen bg-sentinel-bg overflow-hidden">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto">
          <PageContent />
        </main>
        <StatusBar />
      </div>
      <OverlayWindow />
    </div>
  )
}