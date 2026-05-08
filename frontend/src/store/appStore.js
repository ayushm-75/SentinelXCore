// frontend/src/store/appStore.js
import { create } from 'zustand'

export const useAppStore = create((set) => ({
  connected:   false,
  activePage:  'dashboard',
  overlayMode: false,
  theme:       'dark',

  setConnected:  (v)    => set({ connected: v }),
  setActivePage: (page) => set({ activePage: page }),
  toggleOverlay: ()     => set((s) => ({ overlayMode: !s.overlayMode })),
}))