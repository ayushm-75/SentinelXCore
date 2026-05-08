// frontend/src/store/threatStore.js
import { create } from 'zustand'

export const useThreatStore = create((set) => ({
  alerts:    [],
  processes: [],

  setAlerts:    (a) => set({ alerts: a }),
  setProcesses: (p) => set({ processes: p }),

  addAlert: (alert) => set((s) => ({
    alerts: [alert, ...s.alerts].slice(0, 500),
  })),

  ackAlert: (id) => set((s) => ({
    alerts: s.alerts.map(a => a.alert_id === id ? { ...a, acknowledged: true } : a),
  })),
}))