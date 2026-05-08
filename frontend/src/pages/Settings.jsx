// pages\Settings.jsx — full implementation in Phase 6
// frontend/src/pages/Settings.jsx
import { SettingsPanel } from '../components/settings/SettingsPanel'

export function Settings() {
  return (
    <div className="space-y-4 p-4">
      <h1 className="text-lg font-bold text-sentinel-text">Settings</h1>
      <SettingsPanel />
    </div>
  )
}