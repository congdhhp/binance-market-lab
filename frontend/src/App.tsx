import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [apiStatus, setApiStatus] = useState<string>('Checking...')
  const [apiData, setApiData] = useState<any>(null)

  useEffect(() => {
    // Check backend health
    fetch('http://localhost:8000/api/health/')
      .then(res => res.json())
      .then(data => {
        setApiStatus('✅ Connected')
        setApiData(data)
      })
      .catch(() => {
        setApiStatus('❌ Disconnected')
      })
  }, [])

  return (
    <div className="App">
      <div className="container">
        <h1>🚀 Binance Market Lab</h1>
        <p className="subtitle">Cryptocurrency Market Data Analysis Platform</p>
        
        <div className="status-card">
          <h2>Backend API Status</h2>
          <p className="status">{apiStatus}</p>
          {apiData && (
            <pre className="api-response">
              {JSON.stringify(apiData, null, 2)}
            </pre>
          )}
        </div>

        <div className="info-card">
          <h2>📊 Phase 1: Data Ingestion Pipeline ✅</h2>
          <ul>
            <li>PostgreSQL + TimescaleDB setup</li>
            <li>Binance API client with rate limiting</li>
            <li>Celery tasks for data ingestion</li>
            <li>REST API endpoints (DRF)</li>
            <li>Data quality validation</li>
          </ul>
        </div>

        <div className="info-card">
          <h2>🔗 Quick Links</h2>
          <ul>
            <li>
              <a href="http://localhost:8000/api/docs/" target="_blank" rel="noopener noreferrer">
                📖 API Documentation (Swagger)
              </a>
            </li>
            <li>
              <a href="http://localhost:8000/admin/" target="_blank" rel="noopener noreferrer">
                ⚙️ Django Admin
              </a>
            </li>
            <li>
              <a href="http://localhost:8000/api/v1/market-data/symbols/" target="_blank" rel="noopener noreferrer">
                📊 Symbols API
              </a>
            </li>
          </ul>
        </div>

        <div className="info-card">
          <h2>🚧 Coming Next</h2>
          <p>
            <strong>Phase 2:</strong> Technical Analysis & Indicators Engine
            <br />
            <small>Full dashboard with charts, heatmaps, and screener will be implemented in Phase 6</small>
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
