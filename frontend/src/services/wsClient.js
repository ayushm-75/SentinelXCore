// frontend/src/services/wsClient.js
import { WS_URL } from '../utils/constants'

class WSClient {
  constructor() {
    this._ws          = null
    this._listeners   = {}
    this._reconnect   = true
    this._retryMs     = 2000
    this._maxRetry    = 15000
    this._pingTimer   = null
  }

  connect() {
    if (this._ws && this._ws.readyState === WebSocket.OPEN) return

    try {
      this._ws = new WebSocket(WS_URL)
      this._ws.binaryType = 'arraybuffer'

      this._ws.onopen = () => {
        this._retryMs = 2000
        this._emit('connected', true)
        this._ws.send(JSON.stringify({ type: 'get_snapshot' }))
        this._ws.send(JSON.stringify({ type: 'get_alerts' }))
        this._ws.send(JSON.stringify({ type: 'get_connections' }))
        this._startPing()
      }

      this._ws.onmessage = (evt) => {
        try {
          let data
          if (evt.data instanceof ArrayBuffer) {
            data = JSON.parse(new TextDecoder().decode(evt.data))
          } else {
            data = JSON.parse(evt.data)
          }
          // Respond to server pings
          if (data.type === 'ping') {
            this._ws.send(JSON.stringify({ type: 'pong' }))
            return
          }
          this._emit(data.type, data)
          this._emit('*', data)
        } catch (_err) {
          // ignore malformed frames
        }
      }

      this._ws.onclose = () => {
        this._stopPing()
        this._emit('connected', false)
        if (this._reconnect) {
          setTimeout(() => this.connect(), this._retryMs)
          this._retryMs = Math.min(this._retryMs * 1.5, this._maxRetry)
        }
      }

      this._ws.onerror = () => {
        this._ws.close()
      }
    } catch (_err) {
      setTimeout(() => this.connect(), this._retryMs)
    }
  }

  _startPing() {
    this._stopPing()
    // Send client ping every 15 seconds to keep WS alive
    this._pingTimer = setInterval(() => {
      if (this._ws && this._ws.readyState === WebSocket.OPEN) {
        this._ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 15000)
  }

  _stopPing() {
    if (this._pingTimer) {
      clearInterval(this._pingTimer)
      this._pingTimer = null
    }
  }

  disconnect() {
    this._reconnect = false
    this._stopPing()
    if (this._ws) this._ws.close()
  }

  send(type, data = null) {
    if (this._ws && this._ws.readyState === WebSocket.OPEN) {
      this._ws.send(JSON.stringify({ type, data }))
    }
  }

  on(event, cb) {
    if (!this._listeners[event]) this._listeners[event] = []
    this._listeners[event].push(cb)
    return () => this.off(event, cb)
  }

  off(event, cb) {
    if (!this._listeners[event]) return
    this._listeners[event] = this._listeners[event].filter(fn => fn !== cb)
  }

  _emit(event, payload) {
    ;(this._listeners[event] || []).forEach(cb => {
      try { cb(payload) } catch (_e) { /* silent */ }
    })
  }

  get connected() {
    return this._ws?.readyState === WebSocket.OPEN
  }
}

export const wsClient = new WSClient()