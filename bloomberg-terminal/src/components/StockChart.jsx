import { useState } from 'react'
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Area,
  CartesianGrid
} from 'recharts'

function StockChart({ data, indicators, showVolume = true, height = 400 }) {
  const [showEMA20, setShowEMA20] = useState(true)
  const [showEMA50, setShowEMA50] = useState(true)
  const [showEMA200, setShowEMA200] = useState(true)

  if (!data || data.length === 0) {
    return (
      <div className="chart-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: 'var(--text-muted)' }}>No chart data available</span>
      </div>
    )
  }

  // Calculate min/max for y-axis with some padding
  const prices = data.map(d => [d.low, d.high]).flat()
  const minPrice = Math.min(...prices) * 0.98
  const maxPrice = Math.max(...prices) * 1.02

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const d = payload[0].payload
      return (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          padding: '10px',
          borderRadius: '4px',
          fontSize: '12px'
        }}>
          <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>{d.date}</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 12px' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Open:</span>
            <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{d.open}</span>
            <span style={{ color: 'var(--text-secondary)' }}>High:</span>
            <span style={{ color: 'var(--accent-green)', fontFamily: 'var(--font-mono)' }}>{d.high}</span>
            <span style={{ color: 'var(--text-secondary)' }}>Low:</span>
            <span style={{ color: 'var(--accent-red)', fontFamily: 'var(--font-mono)' }}>{d.low}</span>
            <span style={{ color: 'var(--text-secondary)' }}>Close:</span>
            <span style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>{d.close}</span>
            {d.rsi && <>
              <span style={{ color: 'var(--text-secondary)' }}>RSI:</span>
              <span style={{
                color: d.rsi > 70 ? 'var(--accent-red)' : d.rsi < 30 ? 'var(--accent-green)' : 'var(--text-primary)',
                fontFamily: 'var(--font-mono)'
              }}>{d.rsi}</span>
            </>}
          </div>
        </div>
      )
    }
    return null
  }

  return (
    <div>
      {/* Chart Controls */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '12px', fontSize: '11px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)' }}>
          <input type="checkbox" checked={showEMA20} onChange={() => setShowEMA20(!showEMA20)} />
          <span style={{ color: '#4a9eff' }}>EMA 20</span>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)' }}>
          <input type="checkbox" checked={showEMA50} onChange={() => setShowEMA50(!showEMA50)} />
          <span style={{ color: '#ff6b00' }}>EMA 50</span>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-secondary)' }}>
          <input type="checkbox" checked={showEMA200} onChange={() => setShowEMA200(!showEMA200)} />
          <span style={{ color: '#00c853' }}>EMA 200</span>
        </label>
      </div>

      {/* Main Price Chart */}
      <div className="chart-container" style={{ height: height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" />
            <XAxis
              dataKey="date"
              tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
              tickFormatter={(val) => val.slice(5)}
              interval="preserveStartEnd"
            />
            <YAxis
              domain={[minPrice, maxPrice]}
              tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
              tickFormatter={(val) => val.toFixed(0)}
              orientation="right"
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Support Line */}
            {indicators?.support && (
              <ReferenceLine
                y={indicators.support}
                stroke="#00c853"
                strokeDasharray="5 5"
                label={{ value: `S: ${indicators.support}`, fill: '#00c853', fontSize: 10, position: 'left' }}
              />
            )}

            {/* Resistance Line */}
            {indicators?.resistance && (
              <ReferenceLine
                y={indicators.resistance}
                stroke="#ff4444"
                strokeDasharray="5 5"
                label={{ value: `R: ${indicators.resistance}`, fill: '#ff4444', fontSize: 10, position: 'left' }}
              />
            )}

            {/* ATH Line */}
            {indicators?.ath && (
              <ReferenceLine
                y={indicators.ath}
                stroke="#ffc107"
                strokeDasharray="3 3"
                label={{ value: `ATH: ${indicators.ath}`, fill: '#ffc107', fontSize: 10, position: 'right' }}
              />
            )}

            {/* Price Area */}
            <Area
              type="monotone"
              dataKey="close"
              fill="rgba(74, 158, 255, 0.1)"
              stroke="none"
            />

            {/* Price Line */}
            <Line
              type="monotone"
              dataKey="close"
              stroke="#4a9eff"
              strokeWidth={2}
              dot={false}
              name="Close"
            />

            {/* EMAs */}
            {showEMA20 && (
              <Line
                type="monotone"
                dataKey="ema20"
                stroke="#4a9eff"
                strokeWidth={1}
                dot={false}
                strokeDasharray="2 2"
              />
            )}
            {showEMA50 && (
              <Line
                type="monotone"
                dataKey="ema50"
                stroke="#ff6b00"
                strokeWidth={1}
                dot={false}
                strokeDasharray="2 2"
              />
            )}
            {showEMA200 && (
              <Line
                type="monotone"
                dataKey="ema200"
                stroke="#00c853"
                strokeWidth={1}
                dot={false}
                strokeDasharray="2 2"
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Volume Chart */}
      {showVolume && (
        <div style={{ height: 80, marginTop: 8 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
              <XAxis dataKey="date" tick={false} axisLine={false} />
              <YAxis
                tick={{ fill: 'var(--text-muted)', fontSize: 9 }}
                tickFormatter={(val) => `${(val / 1000000).toFixed(0)}M`}
                orientation="right"
                width={40}
              />
              <Bar
                dataKey="volume"
                fill="rgba(74, 158, 255, 0.3)"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* RSI Chart */}
      <div style={{ height: 80, marginTop: 8 }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 0, right: 30, left: 0, bottom: 0 }}>
            <XAxis dataKey="date" tick={false} axisLine={false} />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: 'var(--text-muted)', fontSize: 9 }}
              orientation="right"
              width={40}
              ticks={[30, 50, 70]}
            />
            <ReferenceLine y={70} stroke="#ff4444" strokeDasharray="2 2" />
            <ReferenceLine y={30} stroke="#00c853" strokeDasharray="2 2" />
            <Area
              type="monotone"
              dataKey="rsi"
              fill="rgba(255, 107, 0, 0.1)"
              stroke="#ff6b00"
              strokeWidth={1}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export default StockChart
