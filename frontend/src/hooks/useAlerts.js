// frontend/src/hooks/useAlerts.js
import { useThreatStore } from '../store/threatStore'
import { api } from '../services/apiClient'

export function useAlerts() {
  const alerts      = useThreatStore(s => s.alerts)
  const ackAlertFn  = useThreatStore(s => s.ackAlert)

  const acknowledge = async (id) => {
    try {
      await api.ackAlert(id)
      ackAlertFn(id)
    } catch {
      // silent — optimistic UI
      ackAlertFn(id)
    }
  }

  const unread = alerts.filter(a => !a.acknowledged).length

  return { alerts, acknowledge, unread }
}