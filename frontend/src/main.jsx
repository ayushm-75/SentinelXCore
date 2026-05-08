// frontend/src/main.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { SplashScreen } from './components/SplashScreen.jsx'
import { wsClient } from './services/wsClient.js'
import './index.css'

// Connect WS immediately — before any component mounts
// so SplashScreen.useEffect can always see wsClient.connected
wsClient.connect()

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <SplashScreen>
      <App />
    </SplashScreen>
  </BrowserRouter>
)