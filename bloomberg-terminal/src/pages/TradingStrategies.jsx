import { useState } from 'react'
import axios from 'axios'
import { TrendingUp, Play, Target, ChevronDown, ChevronUp, Eye, Info, BookOpen, BarChart2 } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { API_BASE } from '../config'

// Strategy definitions with full documentation
const STRATEGY_DOCS = {
  'ATH Breakout': {
    name: 'ATH Breakout (200-DMA + All-Time High)',
    description: '200-Day Trend Filter + All-Time High Breakout (Minervini/O\'Neil Style)',
    rules: [
      'Price previously corrected below 200 EMA',
      'Price crosses above 200 EMA',
      'Breaks all-time high on volume expansion',
      'Volume should be 50%+ above average',
    ],
    configuration: {
      'EMA Period': '200 days',
      'Volume Confirmation': '1.5x average volume',
      'ATH Lookback': 'All available history',
      'Stop Loss': '8% below entry',
      'Target': '15-20% from entry',
    },
    stats: 'Win Rate: 55-65%, Annual Return: 25-60%',
    diagram: `Price
  ▲     ★ ATH Breakout (BUY)
  │    ╱
  │   ╱  ← New All-Time High
  ├─────────── ATH Level
  │ ╱    ← Price above 200 EMA
══╪════════════ 200 EMA
  │╲     ← Previous correction
  └──────────────────────► Time`,
  },
  '52-Week Momentum': {
    name: '52-Week High Momentum',
    description: 'Stocks near 52-week high with strong volume and momentum',
    rules: [
      'Price within 10% of 52-week high',
      'RSI between 50-70 (not overbought)',
      'Volume above 20-day average',
      'Price above all major EMAs',
    ],
    configuration: {
      '52W High Distance': 'Within 10%',
      'RSI Range': '50-70',
      'Volume Filter': 'Above 20-day SMA',
      'Stop Loss': 'Below recent swing low',
      'Target': 'New 52-week high + 10%',
    },
    stats: 'Win Rate: 50-60%, Risk/Reward: 1:2',
    diagram: `Price
  ▲
────┼──────────── 52-Week High
  │  ★ Entry Zone (within 10%)
  │ ╱│
  │╱ │ ← Consolidation
  │  │
  │ ╱
  └──────────────────────► Time`,
  },
  'VCP Pattern': {
    name: 'Volatility Contraction Pattern (VCP)',
    description: 'Mark Minervini\'s signature pattern - decreasing volatility before breakout',
    rules: [
      'Series of price contractions (T1 > T2 > T3)',
      'Each contraction is tighter than previous',
      'Volume dries up during contraction',
      'Breakout on high volume',
    ],
    configuration: {
      'Contractions': '2-4 contractions',
      'Contraction Ratio': 'Each 50-75% of previous',
      'Volume Dry-up': 'Below 50-day average',
      'Breakout Volume': '2x average',
      'Stop Loss': 'Below pivot point',
    },
    stats: 'Win Rate: 60-70%, Typical Gain: 20-50%',
    diagram: `Price  T1=15%  T2=8%  T3=4%
  ▲      ╱╲
  │     ╱  ╲    ╱╲   ★ Breakout
  │    ╱    ╲  ╱  ╲ ╱
  │   ╱      ╲╱    ╲
  │  ╱  Tighter contractions
  └──────────────────────► Time`,
  },
  'Cup & Handle': {
    name: 'Cup and Handle Pattern',
    description: "William O'Neil's classic bullish continuation pattern",
    rules: [
      'U-shaped cup formation (7-65 weeks)',
      'Cup depth: 12-33% correction',
      'Handle: 1-4 weeks, drift down on low volume',
      'Breakout above handle high on volume',
    ],
    configuration: {
      'Cup Duration': '7-65 weeks',
      'Cup Depth': '12-33% from high',
      'Handle Duration': '1-4 weeks',
      'Handle Drift': '5-15% from cup high',
      'Breakout Target': 'Cup depth added to breakout',
    },
    stats: 'Win Rate: 65-75%, Average Gain: 25-40%',
    diagram: `Price
  ▲  ╲                 ╱ ★ Breakout
  │   ╲       Handle ╱
  │    ╲        ──  ╱
  │     ╲      ╱  ╲╱
  │      ╲    ╱
  │       ╲╱  ← Cup
  └──────────────────────► Time`,
  },
  'Donchian Breakout': {
    name: 'Donchian Channel Breakout (Turtle Trading)',
    description: 'Classic trend-following system used by Turtle Traders',
    rules: [
      'Buy on 20-day high breakout',
      'Sell on 10-day low breakdown',
      'Use ATR for position sizing',
      'Add to position on new breakouts',
    ],
    configuration: {
      'Entry Channel': '20-day high',
      'Exit Channel': '10-day low',
      'ATR Period': '20 days',
      'Position Size': '2% risk per trade',
      'Max Units': '4 units per market',
    },
    stats: 'Win Rate: 35-40%, Risk/Reward: 1:3+',
    diagram: `Price
  ▲
════╪════════ 20-Day High (Buy)
  │   ╱╲   ╱╲★ Breakout
  │  ╱  ╲ ╱  ╲
  │ ╱    ╳
────┼──────── 10-Day Low (Exit)
  └──────────────────────► Time`,
  },
  'MA Stack': {
    name: 'Moving Average Stack',
    description: 'Perfect EMA alignment indicating strong trend',
    rules: [
      'Price > EMA 20 > EMA 50 > EMA 200',
      'All EMAs sloping upward',
      'Price pullback to EMA 20 for entry',
      'Exit when EMA 20 crosses below EMA 50',
    ],
    configuration: {
      'Fast EMA': '20 days',
      'Medium EMA': '50 days',
      'Slow EMA': '200 days',
      'Entry': 'Pullback to EMA 20',
      'Exit': 'EMA 20 < EMA 50',
    },
    stats: 'Win Rate: 55-65%, Trend Capture: High',
    diagram: `Price
  ▲       ★ Price
  │      ╱ ── EMA 20
  │     ╱  ─── EMA 50
  │    ╱   ──── EMA 200
  │   ╱  Perfect Stack ↑
  └──────────────────────► Time`,
  },
  'Relative Strength': {
    name: 'Relative Strength Breakout',
    description: 'Stocks outperforming the index with momentum',
    rules: ['RS Rating > 80 (top 20%)', 'Price making new highs vs index', 'Volume confirmation', 'Sector strength'],
    configuration: { 'RS Minimum': '80', 'Index': 'Nifty 50', 'Lookback': '52 weeks' },
    stats: 'Win Rate: 55-65%, Outperformance: 15-30%',
    diagram: `Stock ↑↑↑   vs   Index ↑
Strong outperformance = Buy`,
  },
  'Bollinger Squeeze': {
    name: 'Bollinger Band Squeeze',
    description: 'Low volatility squeeze before explosive breakout',
    rules: ['BB narrowing (squeeze)', 'Keltner inside BB', 'Volume decreasing', 'Breakout direction by momentum'],
    configuration: { 'BB Period': '20', 'BB StdDev': '2.0', 'Keltner ATR': '1.5' },
    stats: 'Win Rate: 60-70%, Volatility Expansion: 2-3x',
    diagram: `BB Squeeze → Expansion
  ╲    ┌──┐    ╱★
   ╲   │  │  ╱
    ╲──┴──┴──╱`,
  },
  'Base Breakout': {
    name: 'Consolidation Base Breakout',
    description: 'Flat base consolidation followed by breakout',
    rules: ['5-15 weeks consolidation', 'Price range within 15%', 'Volume contracting', 'Breakout on volume'],
    configuration: { 'Base Duration': '5-15 weeks', 'Range': '15%', 'Volume': 'Contracting' },
    stats: 'Win Rate: 60-70%, Gain: 20-35%',
    diagram: `  ┌─────────┬╱★
  │  Base   │
  └─────────┘`,
  },
  'Stage Analysis': {
    name: 'Weinstein Stage Analysis',
    description: 'Stan Weinstein\'s Stage 2 accumulation breakout',
    rules: ['Stage 1: Base (30-week MA flat)', 'Stage 2: Advancing (buy here)', 'Stage 3: Distribution', 'Stage 4: Decline'],
    configuration: { 'MA Period': '30 weeks', 'Buy': 'Early Stage 2', 'Exit': 'Stage 3' },
    stats: 'Win Rate: 60-65%, Multi-bagger potential',
    diagram: `Stage 1→2→3→4
  │  ╱╲★  ╱╲
  │ ╱    ╲╱  ╲
══╪════════════
Buy at Stage 2 breakout`,
  },
}

const STRATEGIES = Object.keys(STRATEGY_DOCS).map(id => ({
  id,
  name: STRATEGY_DOCS[id].name,
  description: STRATEGY_DOCS[id].description,
}))

const STOCK_CATEGORIES = [
  { value: 'Nifty 50', label: 'Nifty 50 (50 stocks)' },
  { value: 'Nifty Next 50', label: 'Nifty Next 50' },
  { value: 'Nifty Midcap 100', label: 'Nifty Midcap 100' },
  { value: 'All Stocks', label: 'All Stocks (~500)' },
]

// Price Chart with Support/Resistance
function PriceChartWithSR({ data, supportResistance, currentAnalysis }) {
  if (!data || !data.dates || data.dates.length === 0) {
    return <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>No data</div>
  }

  const chartData = data.dates.map((date, i) => ({
    date: date.slice(5),
    Price: data.prices?.[i],
    'EMA 200': data.ema_200?.[i],
    ATH: data.ath?.[i],
  }))

  const supports = supportResistance?.supports || []
  const resistances = supportResistance?.resistances || []

  return (
    <div style={{ width: '100%', height: 350 }}>
      <ResponsiveContainer>
        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} interval={Math.floor(chartData.length / 10)} />
          <YAxis domain={['auto', 'auto']} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickFormatter={(v) => `₹${v}`} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px' }}
            formatter={(value, name) => [`₹${value?.toFixed(2)}`, name]}
          />
          <Legend wrapperStyle={{ fontSize: '11px' }} />
          {/* Support lines */}
          {supports.slice(-3).map((s, i) => (
            <ReferenceLine key={`s${i}`} y={s} stroke="#22c55e" strokeDasharray="5 5" strokeWidth={1} />
          ))}
          {/* Resistance lines */}
          {resistances.slice(-3).map((r, i) => (
            <ReferenceLine key={`r${i}`} y={r} stroke="#ef4444" strokeDasharray="5 5" strokeWidth={1} />
          ))}
          {/* Nearest S/R */}
          {currentAnalysis?.nearest_support && (
            <ReferenceLine y={currentAnalysis.nearest_support} stroke="#22c55e" strokeWidth={2} label={{ value: `S: ₹${currentAnalysis.nearest_support}`, fill: '#22c55e', fontSize: 10 }} />
          )}
          {currentAnalysis?.nearest_resistance && (
            <ReferenceLine y={currentAnalysis.nearest_resistance} stroke="#ef4444" strokeWidth={2} label={{ value: `R: ₹${currentAnalysis.nearest_resistance}`, fill: '#ef4444', fontSize: 10 }} />
          )}
          <Line type="monotone" dataKey="Price" stroke="var(--accent-orange)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="EMA 200" stroke="var(--accent-blue)" strokeWidth={1} dot={false} strokeDasharray="3 3" />
          <Line type="monotone" dataKey="ATH" stroke="var(--text-muted)" strokeWidth={1} dot={false} strokeDasharray="2 2" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// Equity Curve Chart
function EquityCurveChart({ data }) {
  if (!data || !data.dates || data.dates.length === 0) {
    return <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)' }}>No backtest data</div>
  }

  const chartData = data.dates.map((date, i) => ({
    date: date.slice(5),
    Strategy: data.equity[i],
    'Buy & Hold': data.benchmark[i],
  }))

  return (
    <div style={{ width: '100%', height: 250 }}>
      <ResponsiveContainer>
        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} interval={Math.floor(chartData.length / 8)} />
          <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', borderRadius: '6px' }}
            formatter={(value) => [`${value?.toFixed(2)}%`]}
          />
          <Legend wrapperStyle={{ fontSize: '11px' }} />
          <ReferenceLine y={0} stroke="var(--text-muted)" strokeDasharray="3 3" />
          <Line type="monotone" dataKey="Strategy" stroke="var(--accent-green)" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="Buy & Hold" stroke="var(--accent-blue)" strokeWidth={1} dot={false} strokeDasharray="5 5" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// Band Analysis Component
function BandAnalysis({ symbol, currentPrice, onAnalyze }) {
  const [lowerBand, setLowerBand] = useState('')
  const [upperBand, setUpperBand] = useState('')
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)

  const runAnalysis = async () => {
    if (!lowerBand || !upperBand) return
    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/stock/${symbol}/band-analysis`, {
        lower_band: parseFloat(lowerBand),
        upper_band: parseFloat(upperBand),
      })
      setAnalysis(response.data)
    } catch (e) {
      console.error('Band analysis error:', e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ background: 'var(--bg-tertiary)', borderRadius: '8px', padding: '12px', marginTop: '12px' }}>
      <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--accent-blue)', marginBottom: '10px' }}>
        Band Analysis Tool
      </div>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '10px' }}>
        <div>
          <label style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Lower Band</label>
          <input
            type="number"
            value={lowerBand}
            onChange={(e) => setLowerBand(e.target.value)}
            placeholder={`₹${(currentPrice * 0.9).toFixed(0)}`}
            style={{ width: '100px', padding: '6px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '12px' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Upper Band</label>
          <input
            type="number"
            value={upperBand}
            onChange={(e) => setUpperBand(e.target.value)}
            placeholder={`₹${(currentPrice * 1.2).toFixed(0)}`}
            style={{ width: '100px', padding: '6px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-secondary)', color: 'var(--text-primary)', fontSize: '12px' }}
          />
        </div>
        <button
          onClick={runAnalysis}
          disabled={loading}
          style={{ padding: '6px 12px', borderRadius: '4px', background: 'var(--accent-blue)', color: '#fff', border: 'none', cursor: 'pointer', fontSize: '11px', marginTop: '14px' }}
        >
          {loading ? '...' : 'Analyze'}
        </button>
      </div>

      {analysis && !analysis.error && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', fontSize: '10px' }}>
          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
            <div style={{ color: 'var(--text-muted)' }}>Band Potential</div>
            <div style={{ color: 'var(--accent-green)', fontWeight: '600' }}>+{analysis.band_analysis?.band_potential_gain}%</div>
          </div>
          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
            <div style={{ color: 'var(--text-muted)' }}>Breakout Prob</div>
            <div style={{ color: analysis.breakout_probability > 60 ? 'var(--accent-green)' : 'var(--text-primary)', fontWeight: '600' }}>{analysis.breakout_probability}%</div>
          </div>
          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
            <div style={{ color: 'var(--text-muted)' }}>P/E at Upper</div>
            <div style={{ fontWeight: '600' }}>{analysis.band_analysis?.upper_band?.pe_at_price || 'N/A'}</div>
          </div>
          {analysis.band_analysis?.if_buy_at_lower && (
            <>
              <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                <div style={{ color: 'var(--text-muted)' }}>If Buy @ Lower</div>
                <div style={{ color: 'var(--accent-green)', fontWeight: '600' }}>+{analysis.band_analysis.if_buy_at_lower.current_pnl_pct}% now</div>
              </div>
              <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                <div style={{ color: 'var(--text-muted)' }}>P/L @ Upper</div>
                <div style={{ color: 'var(--accent-green)', fontWeight: '600' }}>+{analysis.band_analysis.if_buy_at_lower.pnl_at_upper}%</div>
              </div>
              <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                <div style={{ color: 'var(--text-muted)' }}>P/L @ Resist</div>
                <div style={{ color: 'var(--accent-green)', fontWeight: '600' }}>+{analysis.band_analysis.if_buy_at_lower.pnl_at_resistance}%</div>
              </div>
            </>
          )}
          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
            <div style={{ color: 'var(--text-muted)' }}>Lower to Support</div>
            <div style={{ fontWeight: '600' }}>{analysis.band_analysis?.lower_band?.pct_to_support}%</div>
          </div>
          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
            <div style={{ color: 'var(--text-muted)' }}>Upper to Resist</div>
            <div style={{ fontWeight: '600' }}>{analysis.band_analysis?.upper_band?.pct_to_resistance}%</div>
          </div>
        </div>
      )}
    </div>
  )
}

// Strategy Info Modal
function StrategyInfoModal({ strategyId, onClose }) {
  const doc = STRATEGY_DOCS[strategyId]
  if (!doc) return null

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
    }} onClick={onClose}>
      <div style={{
        background: 'var(--bg-secondary)', borderRadius: '12px', padding: '24px',
        maxWidth: '600px', maxHeight: '80vh', overflow: 'auto', border: '1px solid var(--border-color)',
      }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '16px', color: 'var(--accent-orange)' }}>{doc.name}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '20px' }}>×</button>
        </div>

        <p style={{ color: 'var(--text-secondary)', marginBottom: '16px', fontSize: '13px' }}>{doc.description}</p>

        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '13px', color: 'var(--accent-green)', marginBottom: '8px' }}>Entry Rules</h3>
          <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', fontSize: '12px' }}>
            {doc.rules.map((rule, i) => <li key={i} style={{ marginBottom: '4px' }}>{rule}</li>)}
          </ul>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '13px', color: 'var(--accent-blue)', marginBottom: '8px' }}>Configuration</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
            {Object.entries(doc.configuration).map(([key, value]) => (
              <div key={key} style={{ background: 'var(--bg-tertiary)', padding: '6px 10px', borderRadius: '4px', fontSize: '11px' }}>
                <div style={{ color: 'var(--text-muted)' }}>{key}</div>
                <div style={{ color: 'var(--text-primary)', fontWeight: '600' }}>{value}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ fontSize: '13px', color: 'var(--accent-orange)', marginBottom: '8px' }}>Pattern</h3>
          <pre style={{
            background: 'var(--bg-tertiary)', padding: '12px', borderRadius: '6px',
            fontSize: '10px', fontFamily: 'monospace', color: 'var(--accent-green)', overflow: 'auto', whiteSpace: 'pre',
          }}>{doc.diagram}</pre>
        </div>

        <div style={{ background: 'var(--bg-tertiary)', padding: '10px', borderRadius: '6px', fontSize: '12px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Stats: </span>
          <span style={{ color: 'var(--accent-green)' }}>{doc.stats}</span>
        </div>
      </div>
    </div>
  )
}

function TradingStrategies({ onStockSelect }) {
  const [selectedStrategy, setSelectedStrategy] = useState(null)
  const [category, setCategory] = useState('Nifty 50')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [scannedCount, setScannedCount] = useState(0)
  const [expandedStock, setExpandedStock] = useState(null)
  const [stockDetails, setStockDetails] = useState({})
  const [showStrategyInfo, setShowStrategyInfo] = useState(null)
  const [backtestData, setBacktestData] = useState({})
  const [loadingBacktest, setLoadingBacktest] = useState({})

  const handleScan = async () => {
    setLoading(true)
    setResults([])
    setExpandedStock(null)

    try {
      const payload = {
        strategy: selectedStrategy?.id || 'all',
        category: category === 'All Stocks' ? undefined : category,
        scan_all: category === 'All Stocks',
      }

      const response = await axios.post(`${API_BASE}/scan/strategies`, payload)
      setResults(response.data.results || [])
      setScannedCount(response.data.total_scanned || 0)
    } catch (error) {
      console.error('Error scanning:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStockDetails = async (symbol) => {
    if (expandedStock === symbol) {
      setExpandedStock(null)
      return
    }

    if (!stockDetails[symbol]) {
      try {
        const [fundRes, newsRes] = await Promise.all([
          axios.get(`${API_BASE}/stock/${symbol}`),
          axios.get(`${API_BASE}/stock/${symbol}/news?num=5`)
        ])
        setStockDetails(prev => ({ ...prev, [symbol]: { fundamentals: fundRes.data, news: newsRes.data } }))
      } catch (error) {
        console.error('Error loading details:', error)
      }
    }
    setExpandedStock(symbol)
  }

  const loadBacktest = async (symbol, strategyName) => {
    const key = `${symbol}-${strategyName}`
    if (backtestData[key]) return

    setLoadingBacktest(prev => ({ ...prev, [key]: true }))
    try {
      const response = await axios.get(`${API_BASE}/stock/${symbol}/backtest/${encodeURIComponent(strategyName)}`)
      setBacktestData(prev => ({ ...prev, [key]: response.data }))
    } catch (error) {
      console.error('Error loading backtest:', error)
      setBacktestData(prev => ({ ...prev, [key]: { error: 'Failed to load backtest' } }))
    } finally {
      setLoadingBacktest(prev => ({ ...prev, [key]: false }))
    }
  }

  const formatMarketCap = (value) => {
    if (!value) return 'N/A'
    if (value >= 10000000000000) return `₹${(value / 10000000000000).toFixed(2)} L Cr`
    if (value >= 10000000) return `₹${(value / 10000000).toFixed(0)} Cr`
    return `₹${value.toFixed(0)}`
  }

  const sortedResults = [...results].sort((a, b) => (b.avg_score || 0) - (a.avg_score || 0))

  return (
    <div className="trading-strategies">
      {showStrategyInfo && <StrategyInfoModal strategyId={showStrategyInfo} onClose={() => setShowStrategyInfo(null)} />}

      {/* Scanner Section */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">
            <TrendingUp size={16} style={{ marginRight: 8, verticalAlign: 'middle' }} />
            Trading Strategies Scanner
          </span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '16px' }}>
          Scan stocks using professional trading strategies. Click info icon for strategy details.
        </p>

        {/* Strategy Selection */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>Select Strategy</label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            <button className={`btn ${!selectedStrategy ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setSelectedStrategy(null)} style={{ fontSize: '11px', padding: '6px 12px' }}>
              All Strategies
            </button>
            {STRATEGIES.map((strat) => (
              <div key={strat.id} style={{ position: 'relative', display: 'inline-flex' }}>
                <button
                  className={`btn ${selectedStrategy?.id === strat.id ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setSelectedStrategy(strat)}
                  style={{ fontSize: '11px', padding: '6px 12px', paddingRight: '26px' }}
                >
                  {strat.id}
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); setShowStrategyInfo(strat.id) }}
                  style={{ position: 'absolute', right: '4px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer', padding: '2px' }}
                  title="View strategy details"
                >
                  <Info size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Universe & Scan */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-end' }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Stock Universe</label>
            <select className="select-field" value={category} onChange={(e) => setCategory(e.target.value)} style={{ width: '100%' }}>
              {STOCK_CATEGORIES.map((cat) => <option key={cat.value} value={cat.value}>{cat.label}</option>)}
            </select>
          </div>
          <button className="btn btn-primary" onClick={handleScan} disabled={loading} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {loading ? <><div className="loading-spinner" style={{ width: '14px', height: '14px', margin: 0 }}></div>Scanning...</> : <><Play size={14} />Run Scan</>}
          </button>
        </div>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div className="card-header">
            <span className="card-title">Results ({results.length} stocks)</span>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Scanned {scannedCount} stocks</span>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th style={{ textAlign: 'right' }}>Score</th>
                <th style={{ textAlign: 'center' }}>Buy/Sell</th>
                <th style={{ textAlign: 'center' }}>Signal</th>
                <th style={{ textAlign: 'center' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedResults.map((stock) => (
                <>
                  <tr key={stock.symbol}>
                    <td className="symbol" onClick={() => onStockSelect(stock.symbol)}>{stock.symbol}</td>
                    <td className="value" style={{ textAlign: 'right' }}>
                      <span style={{ color: stock.avg_score >= 70 ? 'var(--accent-green)' : stock.avg_score >= 40 ? 'var(--accent-orange)' : 'var(--text-muted)' }}>
                        {stock.avg_score?.toFixed(1)}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span style={{ color: 'var(--accent-green)' }}>{stock.buy_signals || 0}</span> / <span style={{ color: 'var(--accent-red)' }}>{stock.sell_signals || 0}</span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span className={`recommendation ${stock.recommendation?.toLowerCase().replace(' ', '-')}`}>{stock.recommendation || 'N/A'}</span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button className="btn btn-secondary" onClick={() => loadStockDetails(stock.symbol)} style={{ padding: '4px 8px', fontSize: '10px' }}>
                        {expandedStock === stock.symbol ? <ChevronUp size={12} /> : <ChevronDown size={12} />} Details
                      </button>
                    </td>
                  </tr>
                  {expandedStock === stock.symbol && (
                    <tr key={`${stock.symbol}-details`}>
                      <td colSpan={5} style={{ padding: '16px', background: 'var(--bg-tertiary)' }}>
                        {/* Strategy Results with Backtest */}
                        <h4 style={{ fontSize: '13px', color: 'var(--accent-orange)', marginBottom: '12px' }}>
                          <BarChart2 size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                          Strategy Results & Backtests
                        </h4>
                        <div style={{ display: 'grid', gap: '12px' }}>
                          {Object.entries(stock.strategies || {}).map(([name, data]) => {
                            const btKey = `${stock.symbol}-${name}`
                            const bt = backtestData[btKey]
                            const isLoading = loadingBacktest[btKey]

                            return (
                              <div key={name} style={{ background: 'var(--bg-secondary)', borderRadius: '8px', padding: '12px', border: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span style={{ fontWeight: '600', fontSize: '13px' }}>{name}</span>
                                    <button onClick={() => setShowStrategyInfo(name)} style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', cursor: 'pointer' }}>
                                      <Info size={12} />
                                    </button>
                                  </div>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                    <span style={{ color: data.signal?.includes('BUY') ? 'var(--accent-green)' : data.signal?.includes('SELL') ? 'var(--accent-red)' : 'var(--text-muted)', fontWeight: '600' }}>
                                      {data.signal} ({data.score})
                                    </span>
                                    <button
                                      className="btn btn-secondary"
                                      onClick={() => loadBacktest(stock.symbol, name)}
                                      disabled={isLoading}
                                      style={{ padding: '4px 8px', fontSize: '10px' }}
                                    >
                                      {isLoading ? 'Loading...' : bt ? 'Refresh' : 'Run Backtest'}
                                    </button>
                                  </div>
                                </div>

                                {/* Entry/Exit Info */}
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '12px', fontSize: '11px' }}>
                                  <div style={{ background: 'var(--bg-tertiary)', padding: '6px', borderRadius: '4px' }}>
                                    <div style={{ color: 'var(--text-muted)' }}>Entry</div>
                                    <div style={{ color: 'var(--accent-blue)', fontFamily: 'var(--font-mono)' }}>₹{data.entry_price?.toFixed(2)}</div>
                                  </div>
                                  <div style={{ background: 'var(--bg-tertiary)', padding: '6px', borderRadius: '4px' }}>
                                    <div style={{ color: 'var(--text-muted)' }}>Stop Loss</div>
                                    <div style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>₹{data.stop_loss?.toFixed(2)}</div>
                                  </div>
                                  <div style={{ background: 'var(--bg-tertiary)', padding: '6px', borderRadius: '4px' }}>
                                    <div style={{ color: 'var(--text-muted)' }}>Target</div>
                                    <div style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>₹{data.target?.toFixed(2)}</div>
                                  </div>
                                </div>

                                {/* Backtest Results */}
                                {bt && !bt.error && (
                                  <div>
                                    {/* Investment Style & Exit Rule */}
                                    <div style={{ background: 'var(--bg-tertiary)', padding: '10px', borderRadius: '6px', marginBottom: '12px' }}>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div>
                                          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Style: </span>
                                          <span style={{ fontSize: '11px', color: 'var(--accent-blue)', fontWeight: '600' }}>{bt.investment_style || 'Value Investing'}</span>
                                        </div>
                                        <div>
                                          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Exit: </span>
                                          <span style={{ fontSize: '11px', color: 'var(--accent-orange)' }}>{bt.exit_rule}</span>
                                        </div>
                                      </div>
                                    </div>

                                    {/* Key Metrics */}
                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px', marginBottom: '12px', fontSize: '10px' }}>
                                      {[
                                        ['Total Return', `${bt.metrics?.total_return?.toFixed(1)}%`, bt.metrics?.total_return > 0],
                                        ['Win Rate', `${bt.metrics?.win_rate?.toFixed(0)}%`, bt.metrics?.win_rate > 50],
                                        ['Avg ATH Gain', `${bt.metrics?.avg_gain_from_ath?.toFixed(1)}%`, bt.metrics?.avg_gain_from_ath > 0],
                                        ['Trades', bt.metrics?.total_trades, true],
                                      ].map(([label, value, isGood]) => (
                                        <div key={label} style={{ background: 'var(--bg-tertiary)', padding: '6px', borderRadius: '4px', textAlign: 'center' }}>
                                          <div style={{ color: 'var(--text-muted)' }}>{label}</div>
                                          <div style={{ color: isGood ? 'var(--accent-green)' : 'var(--text-primary)', fontWeight: '600' }}>{value}</div>
                                        </div>
                                      ))}
                                    </div>

                                    {/* Current Analysis with S/R */}
                                    {bt.current_analysis && (
                                      <div style={{ background: 'var(--bg-tertiary)', borderRadius: '6px', padding: '12px', marginBottom: '12px' }}>
                                        <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--accent-orange)', marginBottom: '10px' }}>Current Analysis</div>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', fontSize: '10px' }}>
                                          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                                            <div style={{ color: 'var(--text-muted)' }}>Price</div>
                                            <div style={{ fontWeight: '600' }}>₹{bt.current_analysis.price}</div>
                                          </div>
                                          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                                            <div style={{ color: 'var(--text-muted)' }}>ATH</div>
                                            <div style={{ fontWeight: '600' }}>₹{bt.current_analysis.ath}</div>
                                            <div style={{ fontSize: '9px', color: bt.metrics?.pct_from_ath < 0 ? 'var(--accent-red)' : 'var(--accent-green)' }}>{bt.metrics?.pct_from_ath?.toFixed(1)}%</div>
                                          </div>
                                          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                                            <div style={{ color: 'var(--text-muted)' }}>P/E Ratio</div>
                                            <div style={{ fontWeight: '600' }}>{bt.current_analysis.pe_ratio || 'N/A'}</div>
                                          </div>
                                          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                                            <div style={{ color: 'var(--text-muted)' }}>Breakout Prob</div>
                                            <div style={{ fontWeight: '600', color: bt.current_analysis.breakout_probability > 60 ? 'var(--accent-green)' : 'var(--text-primary)' }}>{bt.current_analysis.breakout_probability}%</div>
                                          </div>
                                        </div>
                                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', fontSize: '10px', marginTop: '8px' }}>
                                          <div style={{ background: '#22c55e22', padding: '8px', borderRadius: '4px', borderLeft: '3px solid #22c55e' }}>
                                            <div style={{ color: '#22c55e' }}>Support</div>
                                            <div style={{ fontWeight: '600' }}>₹{bt.current_analysis.nearest_support}</div>
                                            <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{bt.current_analysis.support_distance_pct}% away</div>
                                          </div>
                                          <div style={{ background: '#ef444422', padding: '8px', borderRadius: '4px', borderLeft: '3px solid #ef4444' }}>
                                            <div style={{ color: '#ef4444' }}>Resistance</div>
                                            <div style={{ fontWeight: '600' }}>₹{bt.current_analysis.nearest_resistance}</div>
                                            <div style={{ fontSize: '9px', color: 'var(--text-muted)' }}>{bt.current_analysis.resistance_distance_pct}% away</div>
                                          </div>
                                          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                                            <div style={{ color: 'var(--text-muted)' }}>Next Support</div>
                                            <div style={{ fontWeight: '600' }}>₹{bt.current_analysis.next_support}</div>
                                          </div>
                                          <div style={{ background: 'var(--bg-secondary)', padding: '8px', borderRadius: '4px' }}>
                                            <div style={{ color: 'var(--text-muted)' }}>Next Resistance</div>
                                            <div style={{ fontWeight: '600' }}>₹{bt.current_analysis.next_resistance}</div>
                                          </div>
                                        </div>
                                      </div>
                                    )}

                                    {/* Price Chart with S/R */}
                                    <div style={{ background: 'var(--bg-tertiary)', borderRadius: '6px', padding: '12px', marginBottom: '12px' }}>
                                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                        Price Chart with Support/Resistance & 200 EMA
                                      </div>
                                      <PriceChartWithSR data={bt.timeseries} supportResistance={bt.support_resistance} currentAnalysis={bt.current_analysis} />
                                    </div>

                                    {/* Equity Curve Chart */}
                                    <div style={{ background: 'var(--bg-tertiary)', borderRadius: '6px', padding: '12px', marginBottom: '12px' }}>
                                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                                        Equity Curve (Strategy vs Buy & Hold)
                                      </div>
                                      <EquityCurveChart data={bt.timeseries} />
                                    </div>

                                    {/* Band Analysis Tool */}
                                    <BandAnalysis symbol={stock.symbol} currentPrice={bt.current_analysis?.price || 0} />

                                    {/* Recent Trades */}
                                    {bt.trades && bt.trades.length > 0 && (
                                      <div style={{ marginTop: '12px' }}>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '6px' }}>Trade History (Value Investing)</div>
                                        <div style={{ maxHeight: '200px', overflow: 'auto' }}>
                                          <table style={{ width: '100%', fontSize: '10px' }}>
                                            <thead>
                                              <tr style={{ color: 'var(--text-muted)' }}>
                                                <th style={{ textAlign: 'left', padding: '4px' }}>Entry</th>
                                                <th style={{ textAlign: 'left', padding: '4px' }}>Exit</th>
                                                <th style={{ textAlign: 'right', padding: '4px' }}>Entry ₹</th>
                                                <th style={{ textAlign: 'right', padding: '4px' }}>Exit ₹</th>
                                                <th style={{ textAlign: 'right', padding: '4px' }}>P&L</th>
                                                <th style={{ textAlign: 'right', padding: '4px' }}>ATH Gain</th>
                                                <th style={{ textAlign: 'center', padding: '4px' }}>Days</th>
                                                <th style={{ textAlign: 'left', padding: '4px' }}>Exit Reason</th>
                                              </tr>
                                            </thead>
                                            <tbody>
                                              {bt.trades.map((trade, i) => (
                                                <tr key={i} style={{ borderTop: '1px solid var(--border-subtle)' }}>
                                                  <td style={{ padding: '4px' }}>{trade.entry_date}</td>
                                                  <td style={{ padding: '4px' }}>{trade.exit_date}</td>
                                                  <td style={{ padding: '4px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>₹{trade.entry_price}</td>
                                                  <td style={{ padding: '4px', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>₹{trade.exit_price}</td>
                                                  <td style={{ padding: '4px', textAlign: 'right', color: trade.win ? 'var(--accent-green)' : 'var(--accent-red)', fontWeight: '600' }}>
                                                    {trade.pnl_pct > 0 ? '+' : ''}{trade.pnl_pct}%
                                                  </td>
                                                  <td style={{ padding: '4px', textAlign: 'right', color: trade.gain_from_ath > 0 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                                                    {trade.gain_from_ath > 0 ? '+' : ''}{trade.gain_from_ath}%
                                                  </td>
                                                  <td style={{ padding: '4px', textAlign: 'center' }}>{trade.days_held}</td>
                                                  <td style={{ padding: '4px', fontSize: '9px', color: trade.exit_reason === 'Currently Holding' ? 'var(--accent-blue)' : 'var(--text-secondary)' }}>{trade.exit_reason}</td>
                                                </tr>
                                              ))}
                                            </tbody>
                                          </table>
                                        </div>
                                      </div>
                                    )}
                                  </div>
                                )}

                                {bt?.error && (
                                  <div style={{ color: 'var(--accent-red)', fontSize: '11px', padding: '8px', background: 'var(--bg-tertiary)', borderRadius: '4px' }}>
                                    Backtest error: {bt.error}
                                  </div>
                                )}
                              </div>
                            )
                          })}
                        </div>

                        {/* View Full Analysis Button */}
                        <div style={{ marginTop: '16px' }}>
                          <button className="btn btn-primary" onClick={() => onStockSelect(stock.symbol)} style={{ fontSize: '11px' }}>
                            <Eye size={12} style={{ marginRight: 4 }} /> Full Stock Analysis
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {!loading && results.length === 0 && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div className="empty-state">
            <Target size={64} />
            <h3>Ready to Scan</h3>
            <p>Select a strategy, choose stock universe, and click "Run Scan"</p>
          </div>
        </div>
      )}

      {loading && (
        <div className="card" style={{ marginTop: '16px' }}>
          <div className="loading">
            <div className="loading-spinner"></div>
            Scanning stocks...
          </div>
        </div>
      )}
    </div>
  )
}

export default TradingStrategies
