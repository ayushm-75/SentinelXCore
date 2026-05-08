// frontend/src/hooks/useWebSocket.js
import { useEffect, useRef } from 'react'
import { wsClient } from '../services/wsClient'
import { useAppStore } from '../store/appStore'
import { useNetworkStore } from '../store/networkStore'
import { useThreatStore } from '../store/threatStore'

export function useWebSocket() {
  const setConnected   = useAppStore(s => s.setConnected)
  const setSnapshot    = useNetworkStore(s => s.setSnapshot)
  const pushStats      = useNetworkStore(s => s.pushStats)
  const setConnections = useNetworkStore(s => s.setConnections)
  const setAlerts      = useThreatStore(s => s.setAlerts)
  const addAlert       = useThreatStore(s => s.addAlert)

  const refs = useRef({
    setConnected, setSnapshot, pushStats,
    setConnections, setAlerts, addAlert,
  })

  useEffect(() => {
    refs.current = {
      setConnected, setSnapshot, pushStats,
      setConnections, setAlerts, addAlert,
    }
  })

  useEffect(() => {
    // DO NOT call wsClient.connect() here — called in main.jsx
    const unsubs = [
      wsClient.on('connected', (v) => {
        refs.current.setConnected(v)
        if (v) {
          setTimeout(() => {
            wsClient.send('get_snapshot')
            wsClient.send('get_alerts')
            wsClient.send('get_connections')
          }, 300)
        }
      }),
      wsClient.on('snapshot', (msg) => {
        const data = msg.data ?? {}
        refs.current.setSnapshot(data)
        refs.current.pushStats(data)
      }),
      wsClient.on('alerts', (msg) => {
        refs.current.setAlerts(msg.data ?? [])
      }),
      wsClient.on('alert.new', (msg) => {
        refs.current.addAlert(msg.data ?? msg)
      }),
      wsClient.on('connections', (msg) => {
        refs.current.setConnections(msg.data ?? [])
      }),
    ]

    const connInterval = setInterval(() => {
      if (wsClient.connected) wsClient.send('get_connections')
    }, 10000)

    return () => {
      unsubs.forEach(off => off())
      clearInterval(connInterval)
    }
  }, [])
}