import { useState, useEffect } from 'react'
import { Search, Clock } from 'lucide-react'

function Header({ searchQuery, setSearchQuery, onSearch }) {
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      onSearch(searchQuery.trim().toUpperCase())
      setSearchQuery('')
    }
  }

  const formatTime = (date) => {
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    })
  }

  const formatDate = (date) => {
    return date.toLocaleDateString('en-IN', {
      weekday: 'short',
      day: '2-digit',
      month: 'short',
      year: 'numeric'
    })
  }

  return (
    <header className="header">
      <div className="header-logo">
        <h1>IST</h1>
        <span>Indian Stock Terminal</span>
      </div>

      <div className="header-search">
        <Search size={14} />
        <input
          type="text"
          placeholder="Search stocks (e.g., RELIANCE, TCS)"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyPress={handleKeyPress}
        />
      </div>

      <div className="header-time">
        <Clock size={12} style={{ marginRight: 6, verticalAlign: 'middle' }} />
        {formatDate(currentTime)} | {formatTime(currentTime)} IST
      </div>
    </header>
  )
}

export default Header
