# Indian Stock Terminal

A Bloomberg-style terminal for Indian Stock Market analysis with real-time data, trading strategies, stock screening, and portfolio management.

## Features

- **Market Overview**: Live market data, top gainers/losers, sector performance, FII/DII activity
- **Stock Analysis**: Detailed stock view with technicals, fundamentals, news, and peer comparison
- **Trading Strategies**: Backtest value investing strategies (ATH Breakout, Golden Cross, MA Stack, etc.)
- **Stock Screener**: Custom queries with 20+ filters (Market Cap, P/E, ROE, D/E, etc.)
- **Watchlist/Portfolio**: Upload holdings via CSV, track P&L, aggregated news, strategy alerts

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                         │
│                              Port: 5173 (dev) / 80 (prod)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Market     │  │   Trading    │  │    Stock     │  │   Watchlist  │     │
│  │   Overview   │  │  Strategies  │  │   Screener   │  │   Portfolio  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                    │                                         │
│  ┌──────────────┐  ┌──────────────┐                                         │
│  │    Stock     │  │   Sidebar    │  Components: Header, Charts, Tables     │
│  │   Analysis   │  │   (Indices)  │                                         │
│  └──────────────┘  └──────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BACKEND (FastAPI + Python)                         │
│                                  Port: 8001                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         API ENDPOINTS                                │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  GET  /api/indices              - Market indices (Nifty, Sensex)    │    │
│  │  GET  /api/market/overview      - Gainers, losers, sectors          │    │
│  │  GET  /api/stock/{symbol}       - Stock details + technicals        │    │
│  │  GET  /api/stock/{symbol}/news  - Latest news for stock             │    │
│  │  POST /api/screener             - Screen stocks with filters        │    │
│  │  POST /api/strategy/backtest    - Backtest trading strategies       │    │
│  │  POST /api/watchlist/analyze    - Analyze portfolio holdings        │    │
│  │  GET  /api/watchlist/quick/{s}  - Quick watchlist lookup            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      CORE MODULES                                    │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  • Stock Data Fetcher (yfinance)                                    │    │
│  │  • Technical Indicators (pandas, numpy)                             │    │
│  │  • Strategy Backtester (value investing logic)                      │    │
│  │  • Screener Engine (query parser + filters)                         │    │
│  │  • Support/Resistance Calculator                                    │    │
│  │  • News Aggregator (Google News RSS)                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Yahoo Finance API (via yfinance) - Stock prices, fundamentals            │
│  • NSE India - Market data (.NS suffix for NSE stocks)                      │
│  • Google News RSS - Stock-related news                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer      | Technology                                      |
|------------|------------------------------------------------|
| Frontend   | React 18, Vite, Recharts, Lucide Icons, Axios |
| Backend    | Python 3.11, FastAPI, Uvicorn                  |
| Data       | yfinance, pandas, numpy                        |
| Storage    | localStorage (client-side portfolio)           |

---

## Project Structure

```
indian-stock-terminal/
├── api_server.py              # FastAPI backend (all endpoints)
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── bloomberg-terminal/        # React Frontend
│   ├── src/
│   │   ├── App.jsx           # Main app with routing
│   │   ├── App.css           # Global styles (dark theme)
│   │   ├── config.js         # API base URL config
│   │   │
│   │   ├── components/
│   │   │   ├── Header.jsx    # Top bar with search
│   │   │   └── Sidebar.jsx   # Navigation + live indices
│   │   │
│   │   └── pages/
│   │       ├── MarketOverview.jsx    # Dashboard
│   │       ├── StockAnalysis.jsx     # Stock detail view
│   │       ├── TradingStrategies.jsx # Backtesting
│   │       ├── Screener.jsx          # Stock screener
│   │       └── Watchlist.jsx         # Portfolio tracker
│   │
│   ├── package.json
│   └── vite.config.js
│
└── docker/                    # Deployment configs (optional)
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    ├── docker-compose.yml
    └── nginx.conf
```

---

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Navigate to project root
cd indian-stock-terminal

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload
```

Backend runs at: http://localhost:8001

### Frontend Setup

```bash
# Navigate to frontend directory
cd bloomberg-terminal

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: http://localhost:5173

---

## API Reference

### Market Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/indices` | GET | Indian, global indices & commodities |
| `/api/market/overview` | GET | Top gainers, losers, most active, sectors |

### Stock Data

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stock/{symbol}` | GET | Full stock data (price, technicals, fundamentals) |
| `/api/stock/{symbol}/news` | GET | Latest news articles |
| `/api/stock/{symbol}/peers` | GET | Peer comparison |
| `/api/stock/{symbol}/band-analysis` | POST | Price band P/E analysis |

### Screener

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/screener` | POST | Screen stocks with custom filters |

**Supported Filters:**
- Market Cap: `mcap_min`, `mcap_max` (in Crores)
- Valuation: `pe_min/max`, `pb_min/max`, `ev_ebitda_min/max`
- Returns: `roe_min/max`, `roce_min/max`
- Margins: `npm_min/max`, `opm_min/max`
- Debt: `debt_to_equity_max`, `current_ratio_min`
- Growth: `revenue_growth_min`, `profit_growth_min`
- Dividend: `dividend_yield_min`

**Example Query:**
```
Market Cap > 10000 Cr AND P/E < 25 AND ROE > 15 AND D/E < 1
```

### Trading Strategies

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/strategy/backtest` | POST | Backtest value investing strategies |

**Available Strategies:**
- `ath_breakout` - Buy on All-Time High breakout
- `golden_cross` - 50 EMA crosses above 200 EMA
- `52w_high` - Buy near 52-week high
- `ma_stack` - Moving averages in bullish alignment
- `ema_crossover` - 9/21 EMA crossover
- `macd` - MACD signal crossover

### Watchlist/Portfolio

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/watchlist/analyze` | POST | Full portfolio analysis with P&L, news, signals |
| `/api/watchlist/quick/{symbols}` | GET | Quick lookup for comma-separated symbols |

**POST Body Example:**
```json
{
  "holdings": [
    {"symbol": "RELIANCE", "quantity": 10, "avg_price": 2500},
    {"symbol": "TCS", "quantity": 5, "avg_price": 3200}
  ]
}
```

---

## Screener Query Syntax

The screener supports natural language queries. Examples:

```
# Basic filters
Market Cap > 5000 Cr
P/E < 20
ROE > 15

# Combined filters
Market Cap > 10000 Cr AND P/E < 25 AND ROE > 15
P/B < 3 AND D/E < 0.5 AND Dividend Yield > 2

# Value investing
Market Cap > 50000 Cr AND P/E < 20 AND ROE > 18 AND D/E < 0.3

# Growth stocks
Revenue Growth > 15 AND Profit Growth > 20 AND P/E < 30
```

**All Supported Filters:**

| Filter | Syntax | Typical Range |
|--------|--------|---------------|
| Market Cap | `Market Cap > X Cr` | 1000 - 500000 Cr |
| P/E Ratio | `P/E < X` or `PE < X` | 5 - 50 |
| P/B Ratio | `P/B < X` or `PB < X` | 0.5 - 10 |
| EV/EBITDA | `EV/EBITDA < X` | 5 - 30 |
| ROE | `ROE > X` | 10 - 30% |
| ROCE | `ROCE > X` | 10 - 30% |
| Net Profit Margin | `NPM > X` or `Net Margin > X` | 5 - 25% |
| Operating Margin | `OPM > X` or `Op Margin > X` | 10 - 30% |
| Debt to Equity | `D/E < X` or `Debt/Equity < X` | 0 - 1.5 |
| Current Ratio | `Current Ratio > X` | 1 - 3 |
| Dividend Yield | `Dividend > X` or `Div Yield > X` | 1 - 5% |
| Revenue Growth | `Revenue Growth > X` | 10 - 30% |
| Profit Growth | `Profit Growth > X` | 10 - 30% |
| EPS | `EPS > X` | 10 - 500 |
| Beta | `Beta < X` | 0.5 - 1.5 |

---

## Watchlist CSV Format

Upload your holdings via CSV with this format:

```csv
Symbol, Quantity, Average Price
RELIANCE, 10, 2500
TCS, 5, 3200
INFY, 20, 1450
HDFCBANK, 15, 1600
```

- First row can be header (auto-detected)
- Symbol should be NSE symbol (without .NS suffix)
- Quantity and Average Price are numbers

---

## Trading Strategies Explained

### 1. ATH Breakout (All-Time High)
- **Entry**: Stock breaks above previous all-time high
- **Exit**: Price falls below 200-day EMA
- **Best for**: Momentum/breakout investing

### 2. Golden Cross
- **Entry**: 50 EMA crosses above 200 EMA
- **Exit**: 50 EMA crosses below 200 EMA (Death Cross)
- **Best for**: Long-term trend following

### 3. 52-Week High
- **Entry**: Stock within 5% of 52-week high with strong volume
- **Exit**: Price falls below 200-day EMA
- **Best for**: Relative strength investing

### 4. MA Stack
- **Entry**: Price > 20 EMA > 50 EMA > 200 EMA (bullish alignment)
- **Exit**: EMAs lose alignment
- **Best for**: Trend confirmation

### 5. EMA Crossover (9/21)
- **Entry**: 9 EMA crosses above 21 EMA
- **Exit**: 9 EMA crosses below 21 EMA
- **Best for**: Swing trading

### 6. MACD
- **Entry**: MACD line crosses above signal line
- **Exit**: MACD line crosses below signal line
- **Best for**: Momentum trading

---

## Deployment

### Option 1: Render.com (Recommended for simplicity)

**Backend:**
1. Create Web Service on Render
2. Connect GitHub repo
3. Build: `pip install -r requirements.txt`
4. Start: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`

**Frontend:**
1. Create Static Site on Render
2. Root Directory: `bloomberg-terminal`
3. Build: `npm install && npm run build`
4. Publish: `dist`

### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up --build
```

Access at http://localhost (nginx proxies to both services)

### Option 3: Manual VPS

```bash
# Backend (use PM2 or systemd)
pm2 start "uvicorn api_server:app --host 0.0.0.0 --port 8001" --name stock-api

# Frontend (build and serve with nginx)
cd bloomberg-terminal && npm run build
# Copy dist/ to nginx html folder
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8001 | Backend API port |
| `VITE_API_BASE` | `/api` | Frontend API base (prod) |

---

## Known Limitations

1. **Data Source**: Uses Yahoo Finance which may have delays (15-20 min for NSE)
2. **Rate Limits**: Heavy usage may hit Yahoo Finance rate limits
3. **No Auth**: Currently no user authentication
4. **Client Storage**: Portfolio stored in browser localStorage

---

## Troubleshooting

**Screener returns 0 results:**
- Check if filters are too restrictive
- D/E values in yfinance are percentages (D/E < 1 means < 100%)
- Some filters like ROCE are approximated

**API errors:**
- Ensure backend is running on port 8001
- Check CORS if frontend can't reach backend
- Verify stock symbol exists (use NSE symbols)

**Slow loading:**
- First load fetches fresh data from Yahoo Finance
- Subsequent requests are faster (data cached in memory)

---

## License

MIT License - Free for personal and commercial use.

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
