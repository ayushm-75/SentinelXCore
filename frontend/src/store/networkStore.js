// frontend/src/store/networkStore.js
import { create } from 'zustand'

export const useNetworkStore = create((set) => ({
  snapshot:     {},
  connections:  [],
  statsHistory: [],

  setSnapshot:    (s) => set({ snapshot: s }),
  setConnections: (c) => set({ connections: c }),

  pushStats: (snap) => set((prev) => {
    const entry = {
      time:     new Date().toLocaleTimeString([], {
        hour:   '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
      cpu:      snap.cpu_percent  ?? 0,
      ram:      snap.ram_percent  ?? 0,
      bytesIn:  snap.bytes_in     ?? 0,
      bytesOut: snap.bytes_out    ?? 0,
    }
    // Keep only last 40 points (was 60) — ~2 min at 3s interval
    const next = [...prev.statsHistory, entry].slice(-40)
    return { statsHistory: next }
  }),
}))