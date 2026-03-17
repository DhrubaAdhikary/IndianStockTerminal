import { useState, useEffect } from 'react'
import { LayoutDashboard, TrendingUp, Filter, Briefcase, LineChart, Globe, DollarSign } from 'lucide-react'
import axios from 'axios'
import { API_BASE } from '../config'

function Sidebar({ currentPage, setCurrentPage, onStockSelect }) {
  const [indices, setIndices] = useState({ indian: [], global: [], commodities: [] })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchIndices()
    const interval = setInterval(fetchIndices, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])

  const fetchIndices = async () => {
    try {
      const response = await axios.get(`${API_BASE}/indices`)
      setIndices(response.data)
    } catch (error) {
      console.error('Error fetching indices:', error)
    } finally {
      setLoading(false)
    }
  }

  const navItems = [
    { id: 'overview', label: 'Market Overview', icon: LayoutDashboard },
    { id: 'strategies', label: 'Trading Strategies', icon: TrendingUp },
    { id: 'screener', label: 'Stock Screener', icon: Filter },
    { id: 'watchlist', label: 'My Watchlist', icon: Briefcase },
  ]

  const formatValue = (value) => {
    if (value >= 1000000) {
      return (value / 1000).toFixed(0)
    }
    return value?.toFixed(2) || 'N/A'
  }

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <button
            key={item.id}
            className={currentPage === item.id ? 'active' : ''}
            onClick={() => setCurrentPage(item.id)}
          >
            <item.icon size={16} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-indices">
        {/* Indian Indices */}
        <div className="sidebar-section">
          <h3>
            <LineChart size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
            Indian Indices
          </h3>
          {loading ? (
            <div style={{ padding: '8px', color: 'var(--text-muted)', fontSize: '11px' }}>Loading...</div>
          ) : (
            indices.indian.slice(0, 12).map((index) => (
              <div key={index.symbol} className="index-item">
                <div>
                  <div className="name">{index.name}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="value">{formatValue(index.price)}</div>
                  <div className={`change ${index.change_percent >= 0 ? 'positive' : 'negative'}`}>
                    {index.change_percent >= 0 ? '+' : ''}{index.change_percent?.toFixed(2)}%
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Global Indices */}
        <div className="sidebar-section">
          <h3>
            <Globe size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
            Global Markets
          </h3>
          {indices.global.slice(0, 6).map((index) => (
            <div key={index.symbol} className="index-item">
              <div>
                <div className="name">{index.name}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className="value">{formatValue(index.price)}</div>
                <div className={`change ${index.change_percent >= 0 ? 'positive' : 'negative'}`}>
                  {index.change_percent >= 0 ? '+' : ''}{index.change_percent?.toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Commodities */}
        <div className="sidebar-section">
          <h3>
            <DollarSign size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
            Commodities
          </h3>
          {indices.commodities.map((commodity) => (
            <div key={commodity.symbol} className="index-item">
              <div>
                <div className="name">{commodity.name}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className="value">{formatValue(commodity.price)}</div>
                <div className={`change ${commodity.change_percent >= 0 ? 'positive' : 'negative'}`}>
                  {commodity.change_percent >= 0 ? '+' : ''}{commodity.change_percent?.toFixed(2)}%
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
