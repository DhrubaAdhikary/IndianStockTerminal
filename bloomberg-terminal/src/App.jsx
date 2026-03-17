import { useState } from 'react'
import './App.css'
import Sidebar from './components/Sidebar'
import MarketOverview from './pages/MarketOverview'
import StockAnalysis from './pages/StockAnalysis'
import TradingStrategies from './pages/TradingStrategies'
import Screener from './pages/Screener'
import Watchlist from './pages/Watchlist'
import Header from './components/Header'
import { ArrowLeft } from 'lucide-react'

function App() {
  const [currentPage, setCurrentPage] = useState('overview')
  const [selectedStock, setSelectedStock] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [pageHistory, setPageHistory] = useState([])

  const handleStockSelect = (symbol) => {
    // Save current page to history before navigating
    setPageHistory(prev => [...prev, { page: currentPage, stock: selectedStock }])
    setSelectedStock(symbol)
    setCurrentPage('stock')
  }

  const handlePageChange = (page) => {
    setPageHistory(prev => [...prev, { page: currentPage, stock: selectedStock }])
    setCurrentPage(page)
  }

  const handleBack = () => {
    if (pageHistory.length > 0) {
      const prev = pageHistory[pageHistory.length - 1]
      setPageHistory(pageHistory.slice(0, -1))
      setCurrentPage(prev.page)
      setSelectedStock(prev.stock)
    }
  }

  const renderPage = () => {
    switch (currentPage) {
      case 'overview':
        return <MarketOverview onStockSelect={handleStockSelect} />
      case 'stock':
        return <StockAnalysis symbol={selectedStock} onBack={handleBack} />
      case 'strategies':
        return <TradingStrategies onStockSelect={handleStockSelect} />
      case 'screener':
        return <Screener onStockSelect={handleStockSelect} />
      case 'watchlist':
        return <Watchlist onStockSelect={handleStockSelect} />
      default:
        return <MarketOverview onStockSelect={handleStockSelect} />
    }
  }

  return (
    <div className="app">
      <Header
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onSearch={handleStockSelect}
      />
      <div className="main-container">
        <Sidebar
          currentPage={currentPage}
          setCurrentPage={handlePageChange}
          onStockSelect={handleStockSelect}
        />
        <main className="content">
          {pageHistory.length > 0 && (
            <button
              onClick={handleBack}
              className="back-button"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-primary)',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                marginBottom: '16px',
                fontSize: '13px',
              }}
            >
              <ArrowLeft size={16} />
              Back
            </button>
          )}
          {renderPage()}
        </main>
      </div>
    </div>
  )
}

export default App
