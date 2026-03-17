import { useState, useEffect } from 'react'
import axios from 'axios'
import { Filter, Search, BarChart3, Zap, Code, ChevronDown, ChevronUp } from 'lucide-react'
import { API_BASE } from '../config'

const ADVANCED_TEMPLATES = [
  {
    id: 'high_quality_multibagger',
    name: 'High Quality Multibagger',
    description: 'High ROE, low debt, good margins - like Asian Paints/Titan',
    query: 'Market Cap > 2000 Cr AND ROE > 15 AND Debt to equity < 0.5 AND Operating Margin > 10'
  },
  {
    id: 'early_multibagger',
    name: 'Early Multibagger',
    description: 'Small/Mid caps with strong fundamentals',
    query: 'Market Cap > 500 Cr AND Market Cap < 10000 Cr AND ROE > 12 AND Debt to equity < 0.8'
  },
  {
    id: 'value_stocks',
    name: 'Value Stocks',
    description: 'Low PE with decent fundamentals',
    query: 'PE < 20 AND ROE > 10 AND Market Cap > 1000 Cr'
  },
  {
    id: 'low_debt_quality',
    name: 'Low Debt Quality',
    description: 'Quality companies with minimal debt (IT, FMCG type)',
    query: 'Market Cap > 2000 Cr AND ROE > 12 AND Debt to equity < 0.3'
  },
  {
    id: 'high_margin_business',
    name: 'High Margin Business',
    description: 'Companies with strong operating margins',
    query: 'Operating Margin > 15 AND ROE > 12 AND Market Cap > 1000 Cr'
  },
  {
    id: 'momentum_stocks',
    name: 'Momentum Stocks',
    description: 'Stocks in uptrend near 52-week high',
    query: 'Price > 200 DMA AND Near 52 Week High AND Market Cap > 1000 Cr'
  },
  {
    id: 'large_cap_quality',
    name: 'Large Cap Quality',
    description: 'Blue chip stocks with strong fundamentals',
    query: 'Market Cap > 50000 Cr AND ROE > 12'
  },
  {
    id: 'growth_at_reasonable_price',
    name: 'Growth at Reasonable Price',
    description: 'PEG < 1.5 with good ROE',
    query: 'PEG < 1.5 AND ROE > 12'
  },
  {
    id: 'ultimate_multibagger',
    name: 'Ultimate Multibagger',
    description: 'Mid cap, high ROE, low debt, above 200 DMA',
    query: 'Market Cap > 1000 Cr AND Market Cap < 20000 Cr AND ROE > 15 AND Debt to equity < 0.5 AND Price > 200 DMA'
  },
  {
    id: 'dividend_yield',
    name: 'Dividend Stocks',
    description: 'Large caps with stable fundamentals',
    query: 'Market Cap > 5000 Cr AND ROE > 10 AND Debt to equity < 1'
  },
]

const CATEGORIES = [
  'Nifty 50',
  'Nifty Next 50',
  'Nifty Midcap 100',
  'Nifty Smallcap 100',
  'All Stocks',
]

function Screener({ onStockSelect }) {
  const [mode, setMode] = useState('templates') // 'templates' or 'query'
  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [customQuery, setCustomQuery] = useState('')
  const [category, setCategory] = useState('Nifty 50')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [showQueryHelp, setShowQueryHelp] = useState(false)

  const applyTemplate = (template) => {
    setSelectedTemplate(template)
    setCustomQuery(template.query)
    setMode('query')
  }

  const handleScreen = async () => {
    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/screener/advanced`, {
        template: selectedTemplate?.id,
        query: customQuery,
        category: category,
      })
      setResults(response.data.results || [])
    } catch (error) {
      console.error('Error running screener:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatMarketCap = (value) => {
    if (!value) return 'N/A'
    if (value >= 10000000000000) return `₹${(value / 10000000000000).toFixed(2)} L Cr`
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(0)} Cr`
    return `₹${value.toFixed(0)}`
  }

  const formatPercent = (value) => {
    if (value === undefined || value === null || value === 'N/A') return 'N/A'
    const num = typeof value === 'number' ? value * 100 : parseFloat(value)
    return isNaN(num) ? 'N/A' : `${num.toFixed(2)}%`
  }

  return (
    <div className="screener">
      {/* Header */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <Filter size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />
            Advanced Stock Screener
          </span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
          Filter stocks using predefined multibagger screens or write custom queries.
        </p>

        {/* Mode Selector */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
          <button
            className={`btn ${mode === 'templates' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('templates')}
          >
            <Zap size={14} style={{ marginRight: 4 }} />
            Templates
          </button>
          <button
            className={`btn ${mode === 'query' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('query')}
          >
            <Code size={14} style={{ marginRight: 4 }} />
            Custom Query
          </button>
        </div>

        {/* Templates Mode */}
        {mode === 'templates' && (
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '12px' }}>
              Select a Screener Template
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
              {ADVANCED_TEMPLATES.map((template) => (
                <div
                  key={template.id}
                  onClick={() => applyTemplate(template)}
                  style={{
                    padding: '12px',
                    background: selectedTemplate?.id === template.id ? 'var(--accent-orange)' : 'var(--bg-tertiary)',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    border: selectedTemplate?.id === template.id ? 'none' : '1px solid var(--border-color)',
                    transition: 'all 0.2s',
                  }}
                >
                  <div style={{
                    fontWeight: 600,
                    fontSize: '13px',
                    color: selectedTemplate?.id === template.id ? '#000' : 'var(--text-primary)',
                    marginBottom: '4px'
                  }}>
                    {template.name}
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: selectedTemplate?.id === template.id ? '#333' : 'var(--text-secondary)'
                  }}>
                    {template.description}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Query Mode */}
        {mode === 'query' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                <Code size={12} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                Screener Query
              </label>
              <button
                onClick={() => setShowQueryHelp(!showQueryHelp)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: 'var(--accent-blue)',
                  cursor: 'pointer',
                  fontSize: '11px',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                Query Syntax Help
                {showQueryHelp ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
            </div>

            {showQueryHelp && (
              <div style={{
                background: 'var(--bg-tertiary)',
                padding: '16px',
                borderRadius: '6px',
                marginBottom: '12px',
                fontSize: '11px',
                color: 'var(--text-secondary)',
                maxHeight: '400px',
                overflow: 'auto'
              }}>
                <div style={{ fontWeight: 600, marginBottom: '12px', color: 'var(--accent-orange)', fontSize: '12px' }}>Query Syntax Guide</div>

                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontWeight: 600, marginBottom: '6px', color: 'var(--accent-blue)' }}>All Supported Filters:</div>
                  <table style={{ width: '100%', fontSize: '10px', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <th style={{ textAlign: 'left', padding: '4px', color: 'var(--text-muted)' }}>Filter</th>
                        <th style={{ textAlign: 'left', padding: '4px', color: 'var(--text-muted)' }}>Operators</th>
                        <th style={{ textAlign: 'left', padding: '4px', color: 'var(--text-muted)' }}>Typical Range</th>
                        <th style={{ textAlign: 'left', padding: '4px', color: 'var(--text-muted)' }}>Example</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr style={{ background: 'var(--bg-secondary)' }}><td colSpan={4} style={{ padding: '6px', fontWeight: 600, color: 'var(--accent-orange)' }}>Valuation Metrics</td></tr>
                      <tr><td style={{ padding: '4px' }}>Market Cap</td><td>&gt; &lt;</td><td>500 Cr - 5L Cr</td><td><code>Market Cap &gt; 2000 Cr</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>CMP (Price)</td><td>&gt; &lt;</td><td>50 - 5000</td><td><code>CMP &gt; 100</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>PE / P/E</td><td>&gt; &lt;</td><td>10 - 40</td><td><code>PE &lt; 25</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>PEG</td><td>&gt; &lt;</td><td>0.5 - 2.0</td><td><code>PEG &lt; 1.5</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Price to Book (P/B, CMP/BV)</td><td>&gt; &lt;</td><td>1 - 10</td><td><code>P/B &lt; 3</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>EV/EBITDA</td><td>&gt; &lt;</td><td>5 - 20</td><td><code>EV/EBITDA &lt; 15</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Price to Sales (P/S)</td><td>&gt; &lt;</td><td>1 - 10</td><td><code>P/S &lt; 5</code></td></tr>

                      <tr style={{ background: 'var(--bg-secondary)' }}><td colSpan={4} style={{ padding: '6px', fontWeight: 600, color: 'var(--accent-green)' }}>Profitability Metrics</td></tr>
                      <tr><td style={{ padding: '4px' }}>ROE</td><td>&gt; &lt;</td><td>10% - 30%</td><td><code>ROE &gt; 15</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>ROCE</td><td>&gt; &lt;</td><td>12% - 25%</td><td><code>ROCE &gt; 18</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Operating Margin (OPM)</td><td>&gt; &lt;</td><td>10% - 30%</td><td><code>OPM &gt; 15</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Profit Margin (NPM)</td><td>&gt;</td><td>5% - 20%</td><td><code>NPM &gt; 10</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>EPS</td><td>&gt; &lt;</td><td>10 - 500</td><td><code>EPS &gt; 20</code></td></tr>

                      <tr style={{ background: 'var(--bg-secondary)' }}><td colSpan={4} style={{ padding: '6px', fontWeight: 600, color: 'var(--accent-blue)' }}>Balance Sheet</td></tr>
                      <tr><td style={{ padding: '4px' }}>Debt to Equity (D/E)</td><td>&gt; &lt;</td><td>0.3 - 1.0 (ratio)</td><td><code>Debt to equity &lt; 0.5</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Current Ratio</td><td>&gt;</td><td>1.0 - 3.0</td><td><code>Current Ratio &gt; 1.5</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Free Cash Flow</td><td>&gt; &lt;</td><td>100 Cr+</td><td><code>Free Cash Flow &gt; 500 Cr</code></td></tr>

                      <tr style={{ background: 'var(--bg-secondary)' }}><td colSpan={4} style={{ padding: '6px', fontWeight: 600, color: 'var(--accent-red)' }}>Growth Metrics</td></tr>
                      <tr><td style={{ padding: '4px' }}>Sales Growth</td><td>&gt;</td><td>10% - 30%</td><td><code>Sales Growth &gt; 15</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Earnings Growth</td><td>&gt;</td><td>10% - 30%</td><td><code>Earnings Growth &gt; 20</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Dividend Yield</td><td>&gt; &lt;</td><td>1% - 5%</td><td><code>Dividend Yield &gt; 2</code></td></tr>

                      <tr style={{ background: 'var(--bg-secondary)' }}><td colSpan={4} style={{ padding: '6px', fontWeight: 600, color: 'var(--text-muted)' }}>Ownership & Technical</td></tr>
                      <tr><td style={{ padding: '4px' }}>Promoter Holding</td><td>&gt; &lt;</td><td>40% - 75%</td><td><code>Promoter Holding &gt; 50</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Price vs 200 DMA</td><td>-</td><td>Boolean</td><td><code>Price &gt; 200 DMA</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Near 52 Week High</td><td>-</td><td>Boolean</td><td><code>Near 52 Week High</code></td></tr>
                      <tr><td style={{ padding: '4px' }}>Near 52 Week Low</td><td>-</td><td>Boolean</td><td><code>Near 52 Week Low</code></td></tr>
                    </tbody>
                  </table>
                </div>

                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontWeight: 600, marginBottom: '6px', color: 'var(--accent-green)' }}>Value Guide:</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px', fontSize: '10px' }}>
                    <div><span style={{ color: 'var(--text-muted)' }}>D/E &lt; 0.3</span> = Very low debt</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>D/E &lt; 0.5</span> = Low debt</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>D/E &lt; 1.0</span> = Moderate debt</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>ROE &gt; 15</span> = Good</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>ROE &gt; 20</span> = Excellent</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>PE &lt; 15</span> = Value</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>PE &lt; 25</span> = Fair</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>P/B &lt; 3</span> = Reasonable</div>
                    <div><span style={{ color: 'var(--text-muted)' }}>OPM &gt; 15</span> = Good margins</div>
                  </div>
                </div>

                <div style={{ background: 'var(--bg-secondary)', padding: '10px', borderRadius: '4px' }}>
                  <div style={{ fontWeight: 600, marginBottom: '6px', color: 'var(--accent-orange)' }}>Example Queries:</div>
                  <div style={{ marginBottom: '4px' }}><code style={{ color: 'var(--accent-green)' }}>Market Cap &gt; 2000 Cr AND ROE &gt; 15 AND Debt to equity &lt; 0.5</code></div>
                  <div style={{ marginBottom: '4px' }}><code style={{ color: 'var(--accent-green)' }}>PE &lt; 20 AND ROE &gt; 12 AND OPM &gt; 10</code></div>
                  <div style={{ marginBottom: '4px' }}><code style={{ color: 'var(--accent-green)' }}>P/B &lt; 3 AND EV/EBITDA &lt; 15 AND ROE &gt; 12</code></div>
                  <div><code style={{ color: 'var(--accent-green)' }}>Market Cap &gt; 1000 Cr AND Price &gt; 200 DMA AND Near 52 Week High</code></div>
                </div>
              </div>
            )}

            <textarea
              className="input-field"
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              placeholder="Example: Market Cap > 2000 Cr AND ROCE > 20 AND ROE > 20 AND Debt to equity < 0.3"
              style={{ height: '100px', fontFamily: 'var(--font-mono)', fontSize: '12px' }}
            />
          </div>
        )}

        {/* Stock Universe & Search */}
        <div style={{ display: 'flex', gap: '16px', marginTop: '20px', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
              Stock Universe
            </label>
            <select
              className="select-field"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{ width: '100%' }}
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          <button
            className="btn btn-primary"
            onClick={handleScreen}
            disabled={loading}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            {loading ? (
              <>
                <div className="loading-spinner" style={{ width: '14px', height: '14px', margin: 0 }}></div>
                Screening...
              </>
            ) : (
              <>
                <Search size={14} />
                Run Screener
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div className="card-header">
            <span className="card-title">Results ({results.length} stocks found)</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Company</th>
                <th style={{ textAlign: 'right' }}>Price</th>
                <th style={{ textAlign: 'right' }}>Market Cap</th>
                <th style={{ textAlign: 'right' }}>P/E</th>
                <th style={{ textAlign: 'right' }}>ROE</th>
                <th style={{ textAlign: 'right' }}>ROCE</th>
                <th style={{ textAlign: 'right' }}>D/E</th>
                <th style={{ textAlign: 'right' }}>OPM</th>
                <th style={{ textAlign: 'center' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {results.map((stock) => (
                <tr key={stock.symbol}>
                  <td
                    className="symbol"
                    onClick={() => onStockSelect(stock.symbol)}
                  >
                    {stock.symbol}
                  </td>
                  <td style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {stock.name}
                  </td>
                  <td className="value" style={{ textAlign: 'right' }}>
                    ₹{stock.current_price?.toFixed(2)}
                  </td>
                  <td className="value" style={{ textAlign: 'right' }}>
                    {formatMarketCap(stock.market_cap)}
                  </td>
                  <td className="value" style={{ textAlign: 'right' }}>
                    {stock.pe_ratio !== 'N/A' ? stock.pe_ratio?.toFixed(2) : 'N/A'}
                  </td>
                  <td className="value" style={{
                    textAlign: 'right',
                    color: stock.return_on_equity > 0.15 ? 'var(--accent-green)' : 'inherit'
                  }}>
                    {stock.roe || formatPercent(stock.return_on_equity)}
                  </td>
                  <td className="value" style={{
                    textAlign: 'right',
                    color: stock.roce ? 'var(--accent-green)' : 'inherit'
                  }}>
                    {stock.roce || 'N/A'}
                  </td>
                  <td className="value" style={{
                    textAlign: 'right',
                    color: (stock.debt_to_equity || 0) < 0.5 ? 'var(--accent-green)' : (stock.debt_to_equity || 0) > 1 ? 'var(--accent-red)' : 'inherit'
                  }}>
                    {stock.debt_to_equity_screener || (stock.debt_to_equity !== 'N/A' ? stock.debt_to_equity?.toFixed(2) : 'N/A')}
                  </td>
                  <td className="value" style={{ textAlign: 'right' }}>
                    {stock.operating_profit_margin || formatPercent(stock.operating_margins)}
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button
                      className="btn btn-secondary"
                      onClick={() => onStockSelect(stock.symbol)}
                      style={{ padding: '4px 8px', fontSize: '10px' }}
                    >
                      Analyze
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {!loading && results.length === 0 && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div className="empty-state">
            <BarChart3 size={64} />
            <h3>Ready to Screen</h3>
            <p>Select a template or write a custom query, then click "Run Screener"</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div className="loading">
            <div className="loading-spinner"></div>
            Screening stocks with advanced filters... This may take a moment.
          </div>
        </div>
      )}
    </div>
  )
}

export default Screener
