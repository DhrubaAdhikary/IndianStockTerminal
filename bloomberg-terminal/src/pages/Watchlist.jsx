import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Briefcase, Upload, Plus, Trash2, RefreshCw, TrendingUp, TrendingDown,
  Newspaper, AlertTriangle, Target, PieChart, FileText, X, Edit2, Save
} from 'lucide-react'
import { API_BASE } from '../config'

function Watchlist({ onStockSelect }) {
  const [holdings, setHoldings] = useState([])
  const [portfolioData, setPortfolioData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newHolding, setNewHolding] = useState({ symbol: '', quantity: '', avg_price: '' })
  const [editingIndex, setEditingIndex] = useState(null)
  const [activeTab, setActiveTab] = useState('holdings')

  // Load holdings from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('watchlist_holdings')
    if (saved) {
      const parsed = JSON.parse(saved)
      setHoldings(parsed)
      if (parsed.length > 0) {
        analyzePortfolio(parsed)
      }
    }
  }, [])

  // Save holdings to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('watchlist_holdings', JSON.stringify(holdings))
  }, [holdings])

  const analyzePortfolio = async (holdingsList = holdings) => {
    if (holdingsList.length === 0) return

    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/watchlist/analyze`, {
        holdings: holdingsList
      })
      setPortfolioData(response.data)
    } catch (error) {
      console.error('Error analyzing portfolio:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAddHolding = () => {
    if (!newHolding.symbol || !newHolding.quantity || !newHolding.avg_price) return

    const holding = {
      symbol: newHolding.symbol.toUpperCase(),
      quantity: parseFloat(newHolding.quantity),
      avg_price: parseFloat(newHolding.avg_price),
    }

    const updated = [...holdings, holding]
    setHoldings(updated)
    setNewHolding({ symbol: '', quantity: '', avg_price: '' })
    setShowAddForm(false)
    analyzePortfolio(updated)
  }

  const handleRemoveHolding = (index) => {
    const updated = holdings.filter((_, i) => i !== index)
    setHoldings(updated)
    if (updated.length > 0) {
      analyzePortfolio(updated)
    } else {
      setPortfolioData(null)
    }
  }

  const handleEditHolding = (index) => {
    setEditingIndex(index)
    setNewHolding({
      symbol: holdings[index].symbol,
      quantity: holdings[index].quantity.toString(),
      avg_price: holdings[index].avg_price.toString(),
    })
  }

  const handleSaveEdit = () => {
    if (editingIndex === null) return

    const updated = [...holdings]
    updated[editingIndex] = {
      symbol: newHolding.symbol.toUpperCase(),
      quantity: parseFloat(newHolding.quantity),
      avg_price: parseFloat(newHolding.avg_price),
    }
    setHoldings(updated)
    setEditingIndex(null)
    setNewHolding({ symbol: '', quantity: '', avg_price: '' })
    analyzePortfolio(updated)
  }

  const handleCSVUpload = (event) => {
    const file = event.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target.result
      const lines = text.split('\n')
      const newHoldings = []

      // Skip header row if present
      const startIndex = lines[0].toLowerCase().includes('symbol') ? 1 : 0

      for (let i = startIndex; i < lines.length; i++) {
        const line = lines[i].trim()
        if (!line) continue

        // Try to parse CSV (symbol, quantity, avg_price)
        const parts = line.split(',').map(p => p.trim())
        if (parts.length >= 3) {
          const symbol = parts[0].replace(/"/g, '').toUpperCase()
          const quantity = parseFloat(parts[1])
          const avg_price = parseFloat(parts[2])

          if (symbol && !isNaN(quantity) && !isNaN(avg_price)) {
            newHoldings.push({ symbol, quantity, avg_price })
          }
        }
      }

      if (newHoldings.length > 0) {
        setHoldings(newHoldings)
        analyzePortfolio(newHoldings)
      }
    }
    reader.readAsText(file)
  }

  const formatCurrency = (value) => {
    if (!value && value !== 0) return 'N/A'
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(2)} Cr`
    if (value >= 100000) return `₹${(value / 100000).toFixed(2)} L`
    return `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`
  }

  const formatPct = (value) => {
    if (!value && value !== 0) return 'N/A'
    const prefix = value > 0 ? '+' : ''
    return `${prefix}${value.toFixed(2)}%`
  }

  return (
    <div className="watchlist-page">
      {/* Header */}
      <div className="card">
        <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="card-title">
            <Briefcase size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />
            My Watchlist / Portfolio
          </span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <label className="btn btn-secondary" style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Upload size={14} />
              Upload CSV
              <input type="file" accept=".csv" onChange={handleCSVUpload} style={{ display: 'none' }} />
            </label>
            <button className="btn btn-secondary" onClick={() => setShowAddForm(true)}>
              <Plus size={14} /> Add Stock
            </button>
            <button className="btn btn-primary" onClick={() => analyzePortfolio()} disabled={loading || holdings.length === 0}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
            </button>
          </div>
        </div>

        {/* CSV Format Help */}
        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '12px' }}>
          CSV Format: <code>Symbol, Quantity, Average Price</code> (e.g., <code>RELIANCE, 10, 2500</code>)
        </div>

        {/* Add/Edit Form */}
        {(showAddForm || editingIndex !== null) && (
          <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: '8px', marginBottom: '16px' }}>
            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Symbol</label>
                <input
                  type="text"
                  value={newHolding.symbol}
                  onChange={(e) => setNewHolding({ ...newHolding, symbol: e.target.value })}
                  placeholder="RELIANCE"
                  className="input-field"
                  style={{ width: '120px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Quantity</label>
                <input
                  type="number"
                  value={newHolding.quantity}
                  onChange={(e) => setNewHolding({ ...newHolding, quantity: e.target.value })}
                  placeholder="10"
                  className="input-field"
                  style={{ width: '100px' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Avg Price (₹)</label>
                <input
                  type="number"
                  value={newHolding.avg_price}
                  onChange={(e) => setNewHolding({ ...newHolding, avg_price: e.target.value })}
                  placeholder="2500"
                  className="input-field"
                  style={{ width: '120px' }}
                />
              </div>
              <button
                className="btn btn-primary"
                onClick={editingIndex !== null ? handleSaveEdit : handleAddHolding}
              >
                <Save size={14} /> {editingIndex !== null ? 'Save' : 'Add'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => { setShowAddForm(false); setEditingIndex(null); setNewHolding({ symbol: '', quantity: '', avg_price: '' }) }}
              >
                <X size={14} /> Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Portfolio Summary */}
      {portfolioData?.portfolio_summary && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div className="card-header">
            <span className="card-title">
              <PieChart size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />
              Portfolio Summary
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '16px' }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Total Invested</div>
              <div style={{ fontSize: '18px', fontWeight: '600' }}>{formatCurrency(portfolioData.portfolio_summary.total_invested)}</div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Current Value</div>
              <div style={{ fontSize: '18px', fontWeight: '600' }}>{formatCurrency(portfolioData.portfolio_summary.current_value)}</div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Total P&L</div>
              <div style={{
                fontSize: '18px',
                fontWeight: '600',
                color: portfolioData.portfolio_summary.total_pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'
              }}>
                {formatCurrency(portfolioData.portfolio_summary.total_pnl)}
              </div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Returns</div>
              <div style={{
                fontSize: '18px',
                fontWeight: '600',
                color: portfolioData.portfolio_summary.total_pnl_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'
              }}>
                {formatPct(portfolioData.portfolio_summary.total_pnl_pct)}
              </div>
            </div>
            <div style={{ background: 'var(--bg-tertiary)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Holdings</div>
              <div style={{ fontSize: '18px', fontWeight: '600' }}>{portfolioData.portfolio_summary.holdings_count}</div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      {portfolioData && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            {[
              { id: 'holdings', label: 'Holdings', icon: Briefcase },
              { id: 'news', label: 'News', icon: Newspaper, badge: portfolioData.news?.length },
              { id: 'alerts', label: 'Strategy Alerts', icon: Target, badge: portfolioData.strategy_alerts?.length },
            ].map(tab => (
              <button
                key={tab.id}
                className={`btn ${activeTab === tab.id ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setActiveTab(tab.id)}
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <tab.icon size={14} />
                {tab.label}
                {tab.badge > 0 && (
                  <span style={{
                    background: 'var(--accent-orange)',
                    color: '#fff',
                    borderRadius: '10px',
                    padding: '2px 6px',
                    fontSize: '10px',
                    fontWeight: '600'
                  }}>{tab.badge}</span>
                )}
              </button>
            ))}
          </div>

          {/* Holdings Tab */}
          {activeTab === 'holdings' && portfolioData.holdings && (
            <div style={{ overflow: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Stock</th>
                    <th style={{ textAlign: 'right' }}>Qty</th>
                    <th style={{ textAlign: 'right' }}>Avg Price</th>
                    <th style={{ textAlign: 'right' }}>CMP</th>
                    <th style={{ textAlign: 'right' }}>Invested</th>
                    <th style={{ textAlign: 'right' }}>Current</th>
                    <th style={{ textAlign: 'right' }}>P&L</th>
                    <th style={{ textAlign: 'right' }}>Day Chg</th>
                    <th style={{ textAlign: 'center' }}>Support</th>
                    <th style={{ textAlign: 'center' }}>Resistance</th>
                    <th style={{ textAlign: 'center' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolioData.holdings.map((h, i) => (
                    <tr key={h.symbol}>
                      <td>
                        <div style={{ cursor: 'pointer' }} onClick={() => onStockSelect && onStockSelect(h.symbol)}>
                          <div style={{ fontWeight: '600', color: 'var(--accent-blue)' }}>{h.symbol}</div>
                          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{h.sector}</div>
                        </div>
                      </td>
                      <td style={{ textAlign: 'right' }}>{h.quantity}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>₹{h.avg_price}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>₹{h.current_price}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{formatCurrency(h.invested_value)}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{formatCurrency(h.current_value)}</td>
                      <td style={{ textAlign: 'right' }}>
                        <div style={{ color: h.pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: '600' }}>
                          {formatCurrency(h.pnl)}
                        </div>
                        <div style={{ fontSize: '10px', color: h.pnl_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                          {formatPct(h.pnl_pct)}
                        </div>
                      </td>
                      <td style={{ textAlign: 'right', color: h.day_change >= 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                        {formatPct(h.day_change_pct)}
                      </td>
                      <td style={{ textAlign: 'center', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                        ₹{h.support?.toFixed(0)}
                      </td>
                      <td style={{ textAlign: 'center', color: 'var(--accent-red)', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
                        ₹{h.resistance?.toFixed(0)}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => handleEditHolding(i)}
                          style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer', marginRight: '8px' }}
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          onClick={() => handleRemoveHolding(i)}
                          style={{ background: 'none', border: 'none', color: 'var(--accent-red)', cursor: 'pointer' }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* News Tab */}
          {activeTab === 'news' && portfolioData.news && (
            <div style={{ display: 'grid', gap: '12px' }}>
              {portfolioData.news.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>No recent news</div>
              ) : (
                portfolioData.news.map((item, i) => (
                  <a
                    key={i}
                    href={item.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'block',
                      background: 'var(--bg-tertiary)',
                      padding: '12px',
                      borderRadius: '6px',
                      textDecoration: 'none',
                      color: 'inherit',
                      borderLeft: '3px solid var(--accent-blue)',
                    }}
                  >
                    <div style={{ fontWeight: '500', marginBottom: '4px', color: 'var(--text-primary)' }}>{item.title}</div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                      {item.source} • {item.published}
                    </div>
                  </a>
                ))
              )}
            </div>
          )}

          {/* Strategy Alerts Tab */}
          {activeTab === 'alerts' && portfolioData.strategy_alerts && (
            <div style={{ display: 'grid', gap: '12px' }}>
              {portfolioData.strategy_alerts.length === 0 ? (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '20px' }}>No active strategy signals</div>
              ) : (
                portfolioData.strategy_alerts.map((alert, i) => (
                  <div
                    key={i}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      background: 'var(--bg-tertiary)',
                      padding: '12px 16px',
                      borderRadius: '6px',
                      borderLeft: '3px solid var(--accent-green)',
                    }}
                  >
                    <div>
                      <span
                        style={{ fontWeight: '600', color: 'var(--accent-blue)', cursor: 'pointer' }}
                        onClick={() => onStockSelect && onStockSelect(alert.symbol)}
                      >
                        {alert.symbol}
                      </span>
                      <span style={{ color: 'var(--text-muted)', marginLeft: '12px' }}>{alert.strategy}</span>
                    </div>
                    <span style={{
                      background: 'var(--accent-green)',
                      color: '#fff',
                      padding: '4px 12px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '600'
                    }}>
                      {alert.signal}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {holdings.length === 0 && !loading && (
        <div className="card" style={{ marginTop: '16px', textAlign: 'center', padding: '40px' }}>
          <Briefcase size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
          <h3 style={{ marginBottom: '8px', color: 'var(--text-primary)' }}>No Holdings Yet</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: '16px' }}>
            Add stocks manually or upload a CSV file with your holdings.
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
            <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
              <Upload size={14} /> Upload CSV
              <input type="file" accept=".csv" onChange={handleCSVUpload} style={{ display: 'none' }} />
            </label>
            <button className="btn btn-secondary" onClick={() => setShowAddForm(true)}>
              <Plus size={14} /> Add Manually
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="card" style={{ marginTop: '16px', textAlign: 'center', padding: '40px' }}>
          <div className="loading-spinner" style={{ margin: '0 auto 16px' }}></div>
          <p style={{ color: 'var(--text-muted)' }}>Analyzing your portfolio...</p>
        </div>
      )}

      <style>{`
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export default Watchlist
