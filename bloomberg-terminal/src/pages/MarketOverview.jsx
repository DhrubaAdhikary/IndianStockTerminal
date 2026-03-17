import { useState, useEffect } from 'react'
import axios from 'axios'
import { TrendingUp, TrendingDown, Globe, Newspaper, ExternalLink } from 'lucide-react'
import { API_BASE } from '../config'

function MarketOverview({ onStockSelect }) {
  const [indices, setIndices] = useState({ indian: [], global: [], commodities: [] })
  const [news, setNews] = useState({ indian: [], global: [] })
  const [topGainers, setTopGainers] = useState([])
  const [topLosers, setTopLosers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 60000)
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      const [indicesRes, newsRes] = await Promise.all([
        axios.get(`${API_BASE}/indices`),
        axios.get(`${API_BASE}/news/market`)
      ])
      setIndices(indicesRes.data)
      setNews(newsRes.data)

      // Calculate top gainers/losers from indices
      const allIndices = [...(indicesRes.data.indian || []), ...(indicesRes.data.global || [])]
      const sorted = allIndices.sort((a, b) => b.change_percent - a.change_percent)
      setTopGainers(sorted.filter(i => i.change_percent > 0).slice(0, 5))
      setTopLosers(sorted.filter(i => i.change_percent < 0).slice(-5).reverse())
    } catch (error) {
      console.error('Error fetching market data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatValue = (value) => {
    if (!value) return 'N/A'
    if (value >= 1000000) return `${(value / 1000).toFixed(0)}`
    return value.toFixed(2)
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        Loading market data...
      </div>
    )
  }

  return (
    <div className="market-overview">
      {/* Market Summary Header */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ fontSize: '20px', marginBottom: '4px' }}>Market Overview</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
              Real-time Indian & Global Market Data
            </p>
          </div>
          <div style={{ display: 'flex', gap: '20px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>NIFTY 50</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 'bold' }}>
                {indices.indian.find(i => i.name === 'NIFTY 50')?.price?.toFixed(2) || 'N/A'}
              </div>
              <div style={{
                fontSize: '12px',
                color: (indices.indian.find(i => i.name === 'NIFTY 50')?.change_percent || 0) >= 0
                  ? 'var(--accent-green)' : 'var(--accent-red)'
              }}>
                {(indices.indian.find(i => i.name === 'NIFTY 50')?.change_percent || 0) >= 0 ? '+' : ''}
                {indices.indian.find(i => i.name === 'NIFTY 50')?.change_percent?.toFixed(2) || 0}%
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>NIFTY BANK</div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 'bold' }}>
                {indices.indian.find(i => i.name === 'NIFTY BANK')?.price?.toFixed(2) || 'N/A'}
              </div>
              <div style={{
                fontSize: '12px',
                color: (indices.indian.find(i => i.name === 'NIFTY BANK')?.change_percent || 0) >= 0
                  ? 'var(--accent-green)' : 'var(--accent-red)'
              }}>
                {(indices.indian.find(i => i.name === 'NIFTY BANK')?.change_percent || 0) >= 0 ? '+' : ''}
                {indices.indian.find(i => i.name === 'NIFTY BANK')?.change_percent?.toFixed(2) || 0}%
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Indian Indices */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Indian Indices</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Index</th>
                <th style={{ textAlign: 'right' }}>Value</th>
                <th style={{ textAlign: 'right' }}>Change</th>
                <th style={{ textAlign: 'right' }}>% Change</th>
              </tr>
            </thead>
            <tbody>
              {indices.indian.map((index) => (
                <tr key={index.symbol}>
                  <td style={{ fontWeight: 500 }}>{index.name}</td>
                  <td className="value" style={{ textAlign: 'right' }}>{formatValue(index.price)}</td>
                  <td className={index.change >= 0 ? 'positive' : 'negative'} style={{ textAlign: 'right' }}>
                    {index.change >= 0 ? '+' : ''}{index.change?.toFixed(2)}
                  </td>
                  <td className={index.change_percent >= 0 ? 'positive' : 'negative'} style={{ textAlign: 'right' }}>
                    {index.change_percent >= 0 ? '+' : ''}{index.change_percent?.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Global Indices */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Globe size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
              Global Markets
            </span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Index</th>
                <th style={{ textAlign: 'right' }}>Value</th>
                <th style={{ textAlign: 'right' }}>Change</th>
                <th style={{ textAlign: 'right' }}>% Change</th>
              </tr>
            </thead>
            <tbody>
              {indices.global.map((index) => (
                <tr key={index.symbol}>
                  <td style={{ fontWeight: 500 }}>{index.name}</td>
                  <td className="value" style={{ textAlign: 'right' }}>{formatValue(index.price)}</td>
                  <td className={index.change >= 0 ? 'positive' : 'negative'} style={{ textAlign: 'right' }}>
                    {index.change >= 0 ? '+' : ''}{index.change?.toFixed(2)}
                  </td>
                  <td className={index.change_percent >= 0 ? 'positive' : 'negative'} style={{ textAlign: 'right' }}>
                    {index.change_percent >= 0 ? '+' : ''}{index.change_percent?.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Commodities */}
      <div className="card" style={{ marginTop: '16px' }}>
        <div className="card-header">
          <span className="card-title">Commodities</span>
        </div>
        <div className="grid-4">
          {indices.commodities.map((commodity) => (
            <div key={commodity.symbol} className="metric-item">
              <div className="label">{commodity.name}</div>
              <div className="value">${formatValue(commodity.price)}</div>
              <div style={{
                fontSize: '11px',
                marginTop: '2px',
                color: commodity.change_percent >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'
              }}>
                {commodity.change_percent >= 0 ? '+' : ''}{commodity.change_percent?.toFixed(2)}%
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Gainers & Losers */}
      <div className="grid-2" style={{ marginTop: '16px' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title" style={{ color: 'var(--accent-green)' }}>
              <TrendingUp size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
              Top Gainers
            </span>
          </div>
          {topGainers.map((item) => (
            <div key={item.symbol} style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '8px 0',
              borderBottom: '1px solid var(--border-subtle)'
            }}>
              <span style={{ color: 'var(--text-secondary)' }}>{item.name}</span>
              <span style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                +{item.change_percent?.toFixed(2)}%
              </span>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title" style={{ color: 'var(--accent-red)' }}>
              <TrendingDown size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
              Top Losers
            </span>
          </div>
          {topLosers.map((item) => (
            <div key={item.symbol} style={{
              display: 'flex',
              justifyContent: 'space-between',
              padding: '8px 0',
              borderBottom: '1px solid var(--border-subtle)'
            }}>
              <span style={{ color: 'var(--text-secondary)' }}>{item.name}</span>
              <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>
                {item.change_percent?.toFixed(2)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* News Section */}
      <div className="grid-2" style={{ marginTop: '16px' }}>
        {/* Indian Market News */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Newspaper size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
              Indian Market News
            </span>
          </div>
          {news.indian.length > 0 ? (
            news.indian.map((item, idx) => (
              <div key={idx} className="news-item">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="title"
                  style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', textDecoration: 'none' }}
                >
                  {item.title}
                  <ExternalLink size={12} style={{ flexShrink: 0, marginTop: '2px' }} />
                </a>
                <div className="meta">
                  <span>{item.source}</span>
                  <span className={`sentiment ${item.sentiment}`}>{item.sentiment}</span>
                </div>
              </div>
            ))
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '12px', padding: '20px 0', textAlign: 'center' }}>
              No news available
            </div>
          )}
        </div>

        {/* Global Market News */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">
              <Globe size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
              Global Market News
            </span>
          </div>
          {news.global.length > 0 ? (
            news.global.map((item, idx) => (
              <div key={idx} className="news-item">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="title"
                  style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', textDecoration: 'none' }}
                >
                  {item.title}
                  <ExternalLink size={12} style={{ flexShrink: 0, marginTop: '2px' }} />
                </a>
                <div className="meta">
                  <span>{item.source}</span>
                  <span className={`sentiment ${item.sentiment}`}>{item.sentiment}</span>
                </div>
              </div>
            ))
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '12px', padding: '20px 0', textAlign: 'center' }}>
              No news available
            </div>
          )}
        </div>
      </div>

      {/* Quick Stock Search */}
      <div className="card" style={{ marginTop: '16px' }}>
        <div className="card-header">
          <span className="card-title">Quick Stock Lookup</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT', 'AXISBANK', 'HDFC'].map((symbol) => (
            <button
              key={symbol}
              className="btn btn-secondary"
              onClick={() => onStockSelect(symbol)}
              style={{ fontSize: '11px', padding: '6px 12px' }}
            >
              {symbol}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default MarketOverview
