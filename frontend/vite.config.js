// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    dedupe: ['react', 'react-dom', 'reselect'],
  },
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
    chunkSizeWarningLimit: 2000,
    rollupOptions: {
      output: {
        manualChunks(id) {
          // React core — must be alone and first
          if (
            id.includes('/node_modules/react/') ||
            id.includes('/node_modules/react-dom/') ||
            id.includes('/node_modules/scheduler/')
          ) {
            return 'vendor-react'
          }

          // recharts + ALL its deps together in one chunk
          // reselect MUST be in this same chunk
          if (
            id.includes('/node_modules/recharts/') ||
            id.includes('/node_modules/reselect/') ||
            id.includes('/node_modules/victory-vendor/')
          ) {
            return 'vendor-charts'
          }

          // d3 separately — no reselect dependency
          if (id.includes('/node_modules/d3')) {
            return 'vendor-d3'
          }

          // xyflow
          if (id.includes('/node_modules/@xyflow/')) {
            return 'vendor-flow'
          }

          // framer-motion
          if (id.includes('/node_modules/framer-motion/')) {
            return 'vendor-motion'
          }

          // zustand + react-router
          if (
            id.includes('/node_modules/zustand/') ||
            id.includes('/node_modules/react-router')
          ) {
            return 'vendor-state'
          }

          // everything else in node_modules
          if (id.includes('/node_modules/')) {
            return 'vendor-misc'
          }
        },
      },
    },
  },
})