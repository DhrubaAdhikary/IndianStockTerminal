import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  TrendingUp, Building2, BarChart3, Users, Newspaper,
  Activity, Target, AlertCircle, CheckCircle, ExternalLink,
  DollarSign, PieChart, FileText, TrendingDown
} from 'lucide-react'
import StockChart from '../components/StockChart'
import { API_BASE } from '../config'

function StockAnalysis({ symbol }) {
  const [stock, setStock] = useState(null)
  const [history, setHistory] = useState(null)
  const [strategies, setStrategies] = useState(null)
  const [backtest, setBacktest] = useState(null)
  const [news, setNews] = useState([])
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [period, setPeriod] = useState('1y')

  useEffect(() => {
    if (symbol) {
      fetchAllData()
    }
  }, [symbol])

  useEffect(() => {
    if (symbol) {
      fetchHistory()
    }
  }, [period, symbol])

  const fetchAllData = async () => {
    setLoading(true)
    try {
      const [stockRes, histRes, stratRes, backtestRes, newsRes] = await Promise.all([
        axios.get(`${API_BASE}/stock/${symbol}`),
        axios.get(`${API_BASE}/stock/${symbol}/history?period=${period}`),
        axios.get(`${API_BASE}/stock/${symbol}/strategies`),
        axios.get(`${API_BASE}/stock/${symbol}/backtest`),
        axios.get(`${API_BASE}/stock/${symbol}/news`)
      ])
      setStock(stockRes.data)
      setHistory(histRes.data)
      setStrategies(stratRes.data)
      setBacktest(backtestRes.data)
      setNews(newsRes.data)
    } catch (error) {
      console.error('Error fetching stock data:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/stock/${symbol}/history?period=${period}`)
      setHistory(res.data)
    } catch (error) {
      console.error('Error fetching history:', error)
    }
  }

  const formatValue = (value, type = 'number') => {
    if (value === undefined || value === null || value === 'N/A') return 'N/A'

    if (type === 'currency') {
      if (value >= 10000000) return `₹${(value / 10000000).toFixed(2)} Cr`
      if (value >= 100000) return `₹${(value / 100000).toFixed(2)} L`
      return `₹${value.toFixed(2)}`
    }

    if (type === 'percent') {
      const num = typeof value === 'string' ? parseFloat(value) : value
      return isNaN(num) ? value : `${(num * 100).toFixed(2)}%`
    }

    if (type === 'ratio') {
      return typeof value === 'number' ? value.toFixed(2) : value
    }

    return typeof value === 'number' ? value.toFixed(2) : value
  }

  const formatMarketCap = (value) => {
    if (!value) return 'N/A'
    if (value >= 10000000000000) return `₹${(value / 10000000000000).toFixed(2)} L Cr`
    if (value >= 10000000000) return `₹${(value / 10000000).toFixed(0)} Cr`
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(2)} Cr`
    return `₹${value.toFixed(0)}`
  }

  // Render a financial data table (for P&L, Balance Sheet, Cash Flow, etc.)
  const renderFinancialTable = (data, title) => {
    if (!data || data.length === 0) return null

    const headers = Object.keys(data[0] || {})

    return (
      <div className="card" style={{ marginBottom: '16px' }}>
        <div className="card-header">
          <span className="card-title">{title}</span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Figures in Rs. Crores
          </span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table financial-table">
            <thead>
              <tr>
                {headers.map((h, i) => (
                  <th key={i} style={{
                    textAlign: i === 0 ? 'left' : 'right',
                    minWidth: i === 0 ? '150px' : '80px'
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((row, idx) => (
                <tr key={idx} style={{
                  fontWeight: ['Sales', 'Net Profit', 'Operating Profit', 'Total Assets',
                    'Total Liabilities', 'Net Cash Flow', 'Profit before tax', 'ROCE %'].includes(row[headers[0]])
                    ? '600' : 'normal'
                }}>
                  {headers.map((h, hidx) => (
                    <td key={hidx} style={{
                      textAlign: hidx === 0 ? 'left' : 'right',
                      color: hidx === 0 ? 'var(--text-primary)' :
                        (row[h] && row[h].toString().startsWith('-') ? 'var(--accent-red)' : 'var(--text-secondary)')
                    }}>
                      {row[h]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  // Render growth metrics cards
  const renderGrowthMetrics = (metrics) => {
    if (!metrics || Object.keys(metrics).length === 0) return null

    return (
      <div className="card" style={{ marginBottom: '16px' }}>
        <div className="card-header">
          <span className="card-title">Growth Metrics</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {Object.entries(metrics).map(([title, values]) => (
            <div key={title} style={{
              background: 'var(--bg-secondary)',
              borderRadius: '8px',
              padding: '16px',
              border: '1px solid var(--border-subtle)'
            }}>
              <h4 style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                {title}
              </h4>
              {Object.entries(values).map(([period, value]) => (
                <div key={period} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '8px',
                  fontSize: '13px'
                }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{period}:</span>
                  <span style={{
                    fontFamily: 'var(--font-mono)',
                    fontWeight: '600',
                    color: value && !value.includes('-') ? 'var(--accent-green)' : 'var(--accent-red)'
                  }}>
                    {value || 'N/A'}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (!symbol) {
    return (
      <div className="empty-state">
        <BarChart3 size={64} />
        <h3>No Stock Selected</h3>
        <p>Search for a stock symbol or select one from the sidebar</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        Loading {symbol} data...
      </div>
    )
  }

  if (!stock || stock.error) {
    return (
      <div className="empty-state">
        <AlertCircle size={64} />
        <h3>Error Loading Stock</h3>
        <p>{stock?.error || 'Unable to fetch stock data'}</p>
      </div>
    )
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'chart', label: 'Chart & Entry', icon: Activity },
    { id: 'financials', label: 'Financials', icon: FileText },
    { id: 'peers', label: 'Peer Comparison', icon: Users },
    { id: 'shareholding', label: 'Shareholding', icon: PieChart },
    { id: 'strategies', label: 'Strategies', icon: Target },
    { id: 'news', label: 'News', icon: Newspaper },
  ]

  return (
    <div className="stock-analysis">
      {/* Stock Header */}
      <div className="stock-header">
        <div className="stock-title">
          <h1>{symbol}</h1>
          <div className="company-name">{stock.name}</div>
          <div className="sector">{stock.sector} | {stock.industry}</div>
        </div>
        <div className="stock-price">
          <div className="current">₹{stock.current_price?.toFixed(2)}</div>
          <div className={`change ${(stock.change_percent || 0) >= 0 ? 'positive' : 'negative'}`}>
            {(stock.change_percent || 0) >= 0 ? '+' : ''}₹{stock.change?.toFixed(2)}
            ({(stock.change_percent || 0) >= 0 ? '+' : ''}{stock.change_percent?.toFixed(2)}%)
          </div>
          {strategies?.recommendation && (
            <div className={`recommendation ${strategies.recommendation.toLowerCase().replace(' ', '-')}`} style={{ marginTop: '8px' }}>
              {strategies.recommendation}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={activeTab === tab.id ? 'active' : ''}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div>
          {/* Key Metrics */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Key Metrics</span>
            </div>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="label">Market Cap</div>
                <div className="value">{formatMarketCap(stock.market_cap)}</div>
              </div>
              <div className="metric-item">
                <div className="label">P/E Ratio</div>
                <div className="value">{formatValue(stock.pe_ratio, 'ratio')}</div>
              </div>
              <div className="metric-item">
                <div className="label">P/B Ratio</div>
                <div className="value">{formatValue(stock.price_to_book, 'ratio')}</div>
              </div>
              <div className="metric-item">
                <div className="label">EPS (TTM)</div>
                <div className="value">₹{formatValue(stock.eps, 'ratio')}</div>
              </div>
              <div className="metric-item">
                <div className="label">ROE</div>
                <div className="value" style={{ color: stock.return_on_equity > 0.15 ? 'var(--accent-green)' : 'inherit' }}>
                  {stock.roe || formatValue(stock.return_on_equity, 'percent')}
                </div>
              </div>
              <div className="metric-item">
                <div className="label">ROCE</div>
                <div className="value" style={{ color: stock.roce ? 'var(--accent-green)' : 'inherit' }}>
                  {stock.roce || 'N/A'}
                </div>
              </div>
              <div className="metric-item">
                <div className="label">Dividend Yield</div>
                <div className="value">{formatValue(stock.dividend_yield, 'percent')}</div>
              </div>
              <div className="metric-item">
                <div className="label">Beta</div>
                <div className="value">{formatValue(stock.beta, 'ratio')}</div>
              </div>
            </div>
          </div>

          {/* Price Range */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Price Range</span>
            </div>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="label">Day's Range</div>
                <div className="value">₹{stock.day_low?.toFixed(2)} - ₹{stock.day_high?.toFixed(2)}</div>
              </div>
              <div className="metric-item">
                <div className="label">52 Week Range</div>
                <div className="value">₹{stock['52_week_low']?.toFixed(2)} - ₹{stock['52_week_high']?.toFixed(2)}</div>
              </div>
              <div className="metric-item">
                <div className="label">52W High Distance</div>
                <div className="value" style={{ color: 'var(--accent-red)' }}>
                  -{stock.distance_from_52w_high?.toFixed(2)}%
                </div>
              </div>
              <div className="metric-item">
                <div className="label">52W Low Distance</div>
                <div className="value" style={{ color: 'var(--accent-green)' }}>
                  +{stock.distance_from_52w_low?.toFixed(2)}%
                </div>
              </div>
            </div>
          </div>

          {/* Pros and Cons */}
          {(stock.pros?.length > 0 || stock.cons?.length > 0) && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Pros & Cons</span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                  * Machine generated analysis
                </span>
              </div>
              <div className="pros-cons" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                <div className="pros-list" style={{
                  background: 'rgba(16, 185, 129, 0.05)',
                  borderRadius: '8px',
                  padding: '16px',
                  border: '1px solid rgba(16, 185, 129, 0.2)'
                }}>
                  <h4 style={{ color: 'var(--accent-green)', marginBottom: '12px', fontSize: '13px' }}>
                    <CheckCircle size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                    PROS
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '20px' }}>
                    {stock.pros?.map((pro, idx) => (
                      <li key={idx} style={{ marginBottom: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {pro}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="cons-list" style={{
                  background: 'rgba(239, 68, 68, 0.05)',
                  borderRadius: '8px',
                  padding: '16px',
                  border: '1px solid rgba(239, 68, 68, 0.2)'
                }}>
                  <h4 style={{ color: 'var(--accent-red)', marginBottom: '12px', fontSize: '13px' }}>
                    <AlertCircle size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                    CONS
                  </h4>
                  <ul style={{ margin: 0, paddingLeft: '20px' }}>
                    {stock.cons?.map((con, idx) => (
                      <li key={idx} style={{ marginBottom: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {con}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Quarterly Results Preview */}
          {renderFinancialTable(stock.quarterly_results?.slice(0, 8), 'Quarterly Results')}
        </div>
      )}

      {activeTab === 'chart' && (
        <div>
          {/* Period Selector */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Price Chart - {symbol}</span>
              <div style={{ display: 'flex', gap: '8px' }}>
                {['1mo', '3mo', '6mo', '1y', '2y', '5y'].map((p) => (
                  <button
                    key={p}
                    className={`btn ${period === p ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setPeriod(p)}
                    style={{ padding: '4px 8px', fontSize: '11px' }}
                  >
                    {p.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>
            <StockChart
              data={history?.data}
              indicators={history?.indicators}
              height={450}
            />
          </div>

          {/* Entry Points from Strategies */}
          {strategies?.strategies && Object.keys(strategies.strategies).length > 0 && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Entry Points & Targets</span>
              </div>
              <div className="grid-3">
                {Object.entries(strategies.strategies).slice(0, 6).map(([name, data]) => (
                  <div key={name} className="strategy-card">
                    <div className="header">
                      <span className="name">{name}</span>
                      <span className={`signal ${data.signal?.includes('BUY') ? 'buy' : data.signal?.includes('SELL') ? 'sell' : 'hold'}`}>
                        {data.signal}
                      </span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '8px', fontSize: '11px', marginTop: '8px' }}>
                      <div>
                        <div style={{ color: 'var(--text-muted)' }}>Entry</div>
                        <div style={{ color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)' }}>
                          ₹{data.entry_price?.toFixed(2)}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--text-muted)' }}>Stop Loss</div>
                        <div style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>
                          ₹{data.stop_loss?.toFixed(2)}
                        </div>
                      </div>
                      <div>
                        <div style={{ color: 'var(--text-muted)' }}>Target</div>
                        <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                          ₹{data.target?.toFixed(2)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'financials' && (
        <div>
          {/* Growth Metrics */}
          {renderGrowthMetrics(stock.growth_metrics)}

          {/* Quarterly Results */}
          {renderFinancialTable(stock.quarterly_results, 'Quarterly Results')}

          {/* Profit & Loss */}
          {renderFinancialTable(stock.profit_loss, 'Profit & Loss')}

          {/* Balance Sheet */}
          {renderFinancialTable(stock.balance_sheet, 'Balance Sheet')}

          {/* Cash Flows */}
          {renderFinancialTable(stock.cash_flows, 'Cash Flows')}

          {/* Ratios History */}
          {renderFinancialTable(stock.ratios_history, 'Key Ratios')}

          {/* Financial Health Summary */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">Financial Health Summary</span>
            </div>
            <div className="metrics-grid">
              <div className="metric-item">
                <div className="label">Debt to Equity</div>
                <div className="value" style={{ color: (stock.debt_to_equity || 0) < 1 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                  {stock.debt_to_equity_screener || formatValue(stock.debt_to_equity, 'ratio')}
                </div>
              </div>
              <div className="metric-item">
                <div className="label">Current Ratio</div>
                <div className="value" style={{ color: (stock.current_ratio || 0) > 1.5 ? 'var(--accent-green)' : 'inherit' }}>
                  {formatValue(stock.current_ratio, 'ratio')}
                </div>
              </div>
              <div className="metric-item">
                <div className="label">Operating Margin</div>
                <div className="value">{stock.operating_profit_margin || formatValue(stock.operating_margins, 'percent')}</div>
              </div>
              <div className="metric-item">
                <div className="label">Net Profit Margin</div>
                <div className="value">{stock.net_profit_margin || formatValue(stock.profit_margins, 'percent')}</div>
              </div>
              <div className="metric-item">
                <div className="label">Free Cash Flow</div>
                <div className="value">{formatMarketCap(stock.free_cashflow)}</div>
              </div>
              <div className="metric-item">
                <div className="label">Revenue</div>
                <div className="value">{formatMarketCap(stock.revenue)}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'peers' && (
        <div>
          {stock.peers?.length > 0 ? (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Peer Comparison</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {stock.sector} | {stock.industry}
                </span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table peer-table">
                  <thead>
                    <tr>
                      {Object.keys(stock.peers[0] || {}).map((key, i) => (
                        <th key={key} style={{
                          textAlign: i === 0 || key.toLowerCase().includes('name') ? 'left' : 'right',
                          whiteSpace: 'nowrap'
                        }}>
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {stock.peers.map((peer, idx) => (
                      <tr key={idx} style={{
                        background: peer.Name === stock.name || peer.S?.No === '1' ? 'rgba(59, 130, 246, 0.1)' : 'transparent'
                      }}>
                        {Object.entries(peer).map(([key, val], vidx) => (
                          <td key={vidx} style={{
                            textAlign: vidx === 0 || key.toLowerCase().includes('name') ? 'left' : 'right',
                            fontWeight: key.toLowerCase().includes('name') ? '600' : 'normal',
                            color: key.toLowerCase().includes('name') ? 'var(--accent-blue)' : 'var(--text-secondary)'
                          }}>
                            {val}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="empty-state">
                <Users size={48} />
                <h3>No Peer Data Available</h3>
                <p>Peer comparison data not available for this stock</p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'shareholding' && (
        <div>
          {stock.shareholding?.length > 0 ? (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Shareholding Pattern</span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Numbers in percentages
                </span>
              </div>
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      {Object.keys(stock.shareholding[0] || {}).map((key, i) => (
                        <th key={key} style={{ textAlign: i === 0 ? 'left' : 'right' }}>
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {stock.shareholding.map((row, idx) => {
                      const rowName = Object.values(row)[0]?.toString().toLowerCase() || ''
                      const isPromoter = rowName.includes('promoter')
                      const isFII = rowName.includes('fii')
                      const isDII = rowName.includes('dii')
                      const isPublic = rowName.includes('public')

                      return (
                        <tr key={idx} style={{
                          fontWeight: isPromoter || isFII || isDII || isPublic ? '600' : 'normal',
                          background: isPromoter ? 'rgba(59, 130, 246, 0.05)' : 'transparent'
                        }}>
                          {Object.values(row).map((val, vidx) => (
                            <td key={vidx} style={{ textAlign: vidx === 0 ? 'left' : 'right' }}>
                              {val}
                            </td>
                          ))}
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="card">
              <div className="empty-state">
                <PieChart size={48} />
                <h3>No Shareholding Data Available</h3>
                <p>Shareholding pattern not available for this stock</p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'strategies' && (
        <div>
          {/* Overall Recommendation */}
          {strategies && (
            <div className="card">
              <div className="card-header">
                <span className="card-title">Strategy Analysis Summary</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Overall Recommendation</div>
                  <div className={`recommendation ${strategies.recommendation?.toLowerCase().replace(' ', '-')}`}>
                    {strategies.recommendation}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '24px', textAlign: 'center' }}>
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--accent-blue)' }}>
                      {strategies.avg_score?.toFixed(0)}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Avg Score</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--accent-green)' }}>
                      {strategies.buy_signals}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Buy Signals</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--accent-red)' }}>
                      {strategies.sell_signals}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Sell Signals</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Individual Strategies */}
          {strategies?.strategies && Object.keys(strategies.strategies).length > 0 ? (
            <div className="grid-2">
              {Object.entries(strategies.strategies).map(([name, data]) => (
                <div key={name} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                    <h3 style={{ fontSize: '14px', fontWeight: 600 }}>{name}</h3>
                    <span className={`score ${data.score >= 70 ? 'high' : data.score >= 40 ? 'medium' : 'low'}`}
                      style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 'bold' }}>
                      {data.score}
                    </span>
                  </div>
                  <div style={{ marginBottom: '12px' }}>
                    <span className={`signal ${data.signal?.includes('BUY') ? 'buy' : data.signal?.includes('SELL') ? 'sell' : 'hold'}`}>
                      {data.signal}
                    </span>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                    <div>
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '2px' }}>Entry Price</div>
                      <div style={{ fontSize: '14px', color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)' }}>
                        ₹{data.entry_price?.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '2px' }}>Stop Loss</div>
                      <div style={{ fontSize: '14px', color: 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>
                        ₹{data.stop_loss?.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '2px' }}>Target</div>
                      <div style={{ fontSize: '14px', color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>
                        ₹{data.target?.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  {data.conditions && (
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                      {Object.entries(data.conditions).slice(0, 4).map(([key, val]) => (
                        <div key={key} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                          <span>{key}:</span>
                          <span style={{ color: val === true || val === 'Yes' ? 'var(--accent-green)' : 'var(--text-muted)' }}>
                            {typeof val === 'boolean' ? (val ? 'Yes' : 'No') : val}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="card">
              <div className="empty-state">
                <Target size={48} />
                <h3>No Strategy Data</h3>
                <p>Unable to run strategies on this stock</p>
              </div>
            </div>
          )}

          {/* Backtest Results */}
          {backtest && !backtest.error && (
            <div className="card" style={{ marginTop: '16px' }}>
              <div className="card-header">
                <span className="card-title">Backtest Results (3 Year)</span>
              </div>
              <div className="metrics-grid">
                <div className="metric-item">
                  <div className="label">Total Return</div>
                  <div className="value" style={{ color: backtest.total_return > 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                    {backtest.total_return?.toFixed(2)}%
                  </div>
                </div>
                <div className="metric-item">
                  <div className="label">CAGR</div>
                  <div className="value" style={{ color: backtest.cagr > 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                    {backtest.cagr?.toFixed(2)}%
                  </div>
                </div>
                <div className="metric-item">
                  <div className="label">Sharpe Ratio</div>
                  <div className="value" style={{ color: backtest.sharpe_ratio > 1 ? 'var(--accent-green)' : 'inherit' }}>
                    {backtest.sharpe_ratio?.toFixed(2)}
                  </div>
                </div>
                <div className="metric-item">
                  <div className="label">Sortino Ratio</div>
                  <div className="value">{backtest.sortino_ratio?.toFixed(2)}</div>
                </div>
                <div className="metric-item">
                  <div className="label">Max Drawdown</div>
                  <div className="value" style={{ color: 'var(--accent-red)' }}>
                    {backtest.max_drawdown?.toFixed(2)}%
                  </div>
                </div>
                <div className="metric-item">
                  <div className="label">Win Rate</div>
                  <div className="value" style={{ color: backtest.win_rate > 50 ? 'var(--accent-green)' : 'inherit' }}>
                    {backtest.win_rate?.toFixed(2)}%
                  </div>
                </div>
                <div className="metric-item">
                  <div className="label">Profit Factor</div>
                  <div className="value">{backtest.profit_factor?.toFixed(2)}</div>
                </div>
                <div className="metric-item">
                  <div className="label">Total Trades</div>
                  <div className="value">{backtest.total_trades}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'news' && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">Latest News for {symbol}</span>
          </div>
          {news.length > 0 ? (
            news.map((item, idx) => (
              <div key={idx} className="news-item">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="title"
                  style={{ display: 'flex', alignItems: 'flex-start', gap: '6px', textDecoration: 'none', color: 'var(--text-primary)' }}
                >
                  {item.title}
                  <ExternalLink size={12} style={{ flexShrink: 0, marginTop: '2px', color: 'var(--accent-blue)' }} />
                </a>
                <div className="meta">
                  <span>{item.source}</span>
                  <span className={`sentiment ${item.sentiment}`}>{item.sentiment}</span>
                  <span style={{ color: 'var(--text-muted)' }}>Score: {item.sentiment_score?.toFixed(2)}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="empty-state">
              <Newspaper size={48} />
              <h3>No News Available</h3>
              <p>No recent news found for {symbol}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default StockAnalysis
