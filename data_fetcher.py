"""
Indian Stock Market Data Fetcher
================================
This module demonstrates how to fetch real-time financial data and fundamentals
for Indian stocks listed on NSE and BSE.

Data Sources:
1. Yahoo Finance (via yfinance) - Real-time prices, historical data, fundamentals
2. NSE India website - Additional market data
3. BSE India website - BSE specific data

Stock Symbol Conventions:
- NSE: Add ".NS" suffix (e.g., "RELIANCE.NS", "TCS.NS", "INFY.NS")
- BSE: Add ".BO" suffix (e.g., "RELIANCE.BO", "TCS.BO", "INFY.BO")
"""

import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json


class IndianStockDataFetcher:
    """
    Fetches real-time and fundamental data for Indian stocks.

    Usage:
        fetcher = IndianStockDataFetcher()

        # Get real-time price
        price_data = fetcher.get_realtime_price("RELIANCE")

        # Get company fundamentals
        fundamentals = fetcher.get_fundamentals("TCS")

        # Get historical data
        history = fetcher.get_historical_data("INFY", period="1mo")
    """

    # Popular Indian stocks with their NSE symbols
    POPULAR_STOCKS = {
        "RELIANCE": "Reliance Industries Ltd",
        "TCS": "Tata Consultancy Services",
        "HDFCBANK": "HDFC Bank Ltd",
        "INFY": "Infosys Ltd",
        "ICICIBANK": "ICICI Bank Ltd",
        "HINDUNILVR": "Hindustan Unilever Ltd",
        "SBIN": "State Bank of India",
        "BHARTIARTL": "Bharti Airtel Ltd",
        "ITC": "ITC Ltd",
        "KOTAKBANK": "Kotak Mahindra Bank",
        "LT": "Larsen & Toubro Ltd",
        "AXISBANK": "Axis Bank Ltd",
        "ASIANPAINT": "Asian Paints Ltd",
        "MARUTI": "Maruti Suzuki India Ltd",
        "TITAN": "Titan Company Ltd",
        "SUNPHARMA": "Sun Pharmaceutical",
        "BAJFINANCE": "Bajaj Finance Ltd",
        "WIPRO": "Wipro Ltd",
        "HCLTECH": "HCL Technologies Ltd",
        "TATAMOTORS": "Tata Motors Ltd",
        "TATASTEEL": "Tata Steel Ltd",
        "ADANIENT": "Adani Enterprises Ltd",
        "POWERGRID": "Power Grid Corp",
        "NTPC": "NTPC Ltd",
        "ONGC": "Oil & Natural Gas Corp",
    }

    # Nifty 50 Index and other indices
    INDICES = {
        # Main Indices
        "NIFTY50": "^NSEI",
        "NIFTY100": "^CNX100",
        "NIFTY200": "^CNX200",
        "NIFTY500": "^CRSLDX",
        "NIFTYNEXT50": "^NSMIDCP",
        "SENSEX": "^BSESN",

        # Sectoral Indices
        "BANKNIFTY": "^NSEBANK",
        "NIFTYIT": "^CNXIT",
        "NIFTYPHARMA": "^CNXPHARMA",
        "NIFTYAUTO": "^CNXAUTO",
        "NIFTYFMCG": "^CNXFMCG",
        "NIFTYMETAL": "^CNXMETAL",
        "NIFTYREALTY": "^CNXREALTY",
        "NIFTYENERGY": "^CNXENERGY",
        "NIFTYINFRA": "^CNXINFRA",
        "NIFTYPSUBANK": "^CNXPSUBANK",
        "NIFTYPVTBANK": "^NIFTYPVTBANK",
        "NIFTYFIN": "^CNXFIN",
        "NIFTYMEDIA": "^CNXMEDIA",

        # Cap-based Indices
        "NIFTYMIDCAP50": "^NSEMDCP50",
        "NIFTYMIDCAP100": "^CNX100",
        "NIFTYSMALLCAP50": "^NSESMLCP50",
        "NIFTYSMALLCAP100": "^CNXSC",

        # Strategy Indices
        "NIFTYDIV": "^NIFTYDIV50",
        "NIFTYGROWTH": "^NIFTYGROWSECT15",
        "NIFTYVALUE": "^NIFTYVAL30",

        # Volatility Index
        "INDIAVIX": "^INDIAVIX",
    }

    # Index categories for display
    INDEX_CATEGORIES = {
        "Main Indices": ["NIFTY50", "NIFTY100", "NIFTY200", "NIFTY500", "SENSEX"],
        "Sectoral": ["BANKNIFTY", "NIFTYIT", "NIFTYPHARMA", "NIFTYAUTO", "NIFTYFMCG", "NIFTYMETAL", "NIFTYENERGY", "NIFTYFIN"],
        "Market Cap": ["NIFTYMIDCAP50", "NIFTYSMALLCAP50", "NIFTYNEXT50"],
        "Volatility": ["INDIAVIX"],
    }

    def __init__(self, exchange: str = "NSE"):
        """
        Initialize the data fetcher.

        Args:
            exchange: "NSE" or "BSE" - default exchange to use
        """
        self.exchange = exchange
        self.suffix = ".NS" if exchange == "NSE" else ".BO"

    def _get_ticker_symbol(self, symbol: str) -> str:
        """Convert symbol to Yahoo Finance format."""
        # Check if it's an index
        if symbol.upper() in self.INDICES:
            return self.INDICES[symbol.upper()]
        # Check if already has suffix
        if symbol.endswith(".NS") or symbol.endswith(".BO"):
            return symbol
        return f"{symbol.upper()}{self.suffix}"

    def get_realtime_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch real-time price data for a stock.

        This is HOW we fetch real-time data:
        1. Use yfinance library to connect to Yahoo Finance API
        2. The API provides near real-time data (15-20 min delay for free tier)
        3. Data includes: current price, day high/low, volume, etc.

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")

        Returns:
            Dictionary with real-time price information
        """
        ticker_symbol = self._get_ticker_symbol(symbol)
        ticker = yf.Ticker(ticker_symbol)

        try:
            # Get real-time info
            info = ticker.info

            # Get today's data
            today_data = ticker.history(period="1d")

            result = {
                "symbol": symbol.upper(),
                "ticker": ticker_symbol,
                "company_name": info.get("longName", "N/A"),
                "exchange": info.get("exchange", self.exchange),
                "currency": info.get("currency", "INR"),

                # Price Data
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
                "previous_close": info.get("previousClose", 0),
                "open": info.get("open") or info.get("regularMarketOpen", 0),
                "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh", 0),
                "day_low": info.get("dayLow") or info.get("regularMarketDayLow", 0),

                # Volume Data
                "volume": info.get("volume") or info.get("regularMarketVolume", 0),
                "average_volume": info.get("averageVolume", 0),
                "average_volume_10d": info.get("averageVolume10days", 0),

                # 52 Week Data
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow", 0),

                # Change
                "change": 0,
                "change_percent": 0,

                # Timestamp
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "market_state": info.get("marketState", "UNKNOWN"),
            }

            # Calculate change
            if result["current_price"] and result["previous_close"]:
                result["change"] = round(result["current_price"] - result["previous_close"], 2)
                result["change_percent"] = round(
                    (result["change"] / result["previous_close"]) * 100, 2
                )

            return result

        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental data for a company.

        This is HOW we fetch fundamentals:
        1. Yahoo Finance provides extensive fundamental data
        2. Includes: Market Cap, P/E, P/B, EPS, Revenue, Profit margins, etc.
        3. Also includes balance sheet, income statement, and cash flow data

        Args:
            symbol: Stock symbol (e.g., "RELIANCE", "TCS")

        Returns:
            Dictionary with fundamental information
        """
        ticker_symbol = self._get_ticker_symbol(symbol)
        ticker = yf.Ticker(ticker_symbol)

        try:
            info = ticker.info

            fundamentals = {
                "symbol": symbol.upper(),
                "company_name": info.get("longName", "N/A"),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "website": info.get("website", "N/A"),
                "description": info.get("longBusinessSummary", "N/A")[:500] + "..." if info.get("longBusinessSummary") else "N/A",

                # Valuation Metrics
                "valuation": {
                    "market_cap": info.get("marketCap", 0),
                    "market_cap_formatted": self._format_large_number(info.get("marketCap", 0)),
                    "enterprise_value": info.get("enterpriseValue", 0),
                    "enterprise_value_formatted": self._format_large_number(info.get("enterpriseValue", 0)),
                    "pe_ratio": round(info.get("trailingPE", 0) or 0, 2),
                    "forward_pe": round(info.get("forwardPE", 0) or 0, 2),
                    "peg_ratio": round(info.get("pegRatio", 0) or 0, 2),
                    "price_to_book": round(info.get("priceToBook", 0) or 0, 2),
                    "price_to_sales": round(info.get("priceToSalesTrailing12Months", 0) or 0, 2),
                    "ev_to_ebitda": round(info.get("enterpriseToEbitda", 0) or 0, 2),
                    "ev_to_revenue": round(info.get("enterpriseToRevenue", 0) or 0, 2),
                },

                # Profitability Metrics
                "profitability": {
                    "profit_margin": self._format_percent(info.get("profitMargins", 0)),
                    "operating_margin": self._format_percent(info.get("operatingMargins", 0)),
                    "gross_margin": self._format_percent(info.get("grossMargins", 0)),
                    "ebitda_margin": self._format_percent(info.get("ebitdaMargins", 0)),
                    "return_on_assets": self._format_percent(info.get("returnOnAssets", 0)),
                    "return_on_equity": self._format_percent(info.get("returnOnEquity", 0)),
                },

                # Per Share Data
                "per_share": {
                    "eps_ttm": round(info.get("trailingEps", 0) or 0, 2),
                    "eps_forward": round(info.get("forwardEps", 0) or 0, 2),
                    "book_value": round(info.get("bookValue", 0) or 0, 2),
                    "revenue_per_share": round(info.get("revenuePerShare", 0) or 0, 2),
                },

                # Dividend Data
                "dividends": {
                    "dividend_rate": info.get("dividendRate", 0) or 0,
                    "dividend_yield": self._format_percent(info.get("dividendYield", 0)),
                    "payout_ratio": self._format_percent(info.get("payoutRatio", 0)),
                    "ex_dividend_date": info.get("exDividendDate", "N/A"),
                },

                # Financial Health
                "financial_health": {
                    "total_cash": self._format_large_number(info.get("totalCash", 0)),
                    "total_debt": self._format_large_number(info.get("totalDebt", 0)),
                    "debt_to_equity": round(info.get("debtToEquity", 0) or 0, 2),
                    "current_ratio": round(info.get("currentRatio", 0) or 0, 2),
                    "quick_ratio": round(info.get("quickRatio", 0) or 0, 2),
                },

                # Revenue & Earnings
                "financials": {
                    "total_revenue": self._format_large_number(info.get("totalRevenue", 0)),
                    "revenue_growth": self._format_percent(info.get("revenueGrowth", 0)),
                    "gross_profit": self._format_large_number(info.get("grossProfits", 0)),
                    "ebitda": self._format_large_number(info.get("ebitda", 0)),
                    "net_income": self._format_large_number(info.get("netIncomeToCommon", 0)),
                    "earnings_growth": self._format_percent(info.get("earningsGrowth", 0)),
                },

                # Shares Info
                "shares": {
                    "shares_outstanding": self._format_large_number(info.get("sharesOutstanding", 0)),
                    "float_shares": self._format_large_number(info.get("floatShares", 0)),
                    "insider_ownership": self._format_percent(info.get("heldPercentInsiders", 0)),
                    "institutional_ownership": self._format_percent(info.get("heldPercentInstitutions", 0)),
                },

                # Analyst Recommendations
                "analyst": {
                    "target_high": info.get("targetHighPrice", 0),
                    "target_low": info.get("targetLowPrice", 0),
                    "target_mean": info.get("targetMeanPrice", 0),
                    "recommendation": info.get("recommendationKey", "N/A"),
                    "num_analysts": info.get("numberOfAnalystOpinions", 0),
                },
            }

            return fundamentals

        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch historical price data.

        Args:
            symbol: Stock symbol
            period: Data period - 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
            interval: Data interval - 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

        Returns:
            DataFrame with OHLCV data
        """
        ticker_symbol = self._get_ticker_symbol(symbol)
        ticker = yf.Ticker(ticker_symbol)

        return ticker.history(period=period, interval=interval)

    def get_financial_statements(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Fetch financial statements (Income Statement, Balance Sheet, Cash Flow).

        Returns:
            Dictionary with DataFrames for each statement
        """
        ticker_symbol = self._get_ticker_symbol(symbol)
        ticker = yf.Ticker(ticker_symbol)

        return {
            "income_statement": ticker.income_stmt,
            "balance_sheet": ticker.balance_sheet,
            "cash_flow": ticker.cashflow,
            "quarterly_income": ticker.quarterly_income_stmt,
            "quarterly_balance": ticker.quarterly_balance_sheet,
            "quarterly_cashflow": ticker.quarterly_cashflow,
        }

    def get_index_data(self, index_name: str = "NIFTY50") -> Dict[str, Any]:
        """
        Fetch data for market indices.

        Args:
            index_name: NIFTY50, BANKNIFTY, SENSEX, NIFTYIT, NIFTYPHARMA
        """
        if index_name.upper() not in self.INDICES:
            return {"error": f"Unknown index: {index_name}"}

        return self.get_realtime_price(index_name)

    def get_multiple_stocks(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Fetch data for multiple stocks at once."""
        return [self.get_realtime_price(symbol) for symbol in symbols]

    def _format_large_number(self, num: float) -> str:
        """Format large numbers in Indian numbering system (Cr, L)."""
        if not num or num == 0:
            return "N/A"

        abs_num = abs(num)
        sign = "-" if num < 0 else ""

        if abs_num >= 10000000:  # 1 Crore
            return f"{sign}{abs_num/10000000:.2f} Cr"
        elif abs_num >= 100000:  # 1 Lakh
            return f"{sign}{abs_num/100000:.2f} L"
        elif abs_num >= 1000:
            return f"{sign}{abs_num/1000:.2f} K"
        else:
            return f"{sign}{abs_num:.2f}"

    def _format_percent(self, value: float) -> str:
        """Format value as percentage."""
        if not value or value == 0:
            return "N/A"
        return f"{value * 100:.2f}%"


# Demo function to showcase the data fetching
def demo_data_fetching():
    """
    Demonstrate how to fetch real-time data and fundamentals.
    """
    print("=" * 80)
    print("INDIAN STOCK MARKET DATA FETCHER - DEMO")
    print("=" * 80)

    fetcher = IndianStockDataFetcher(exchange="NSE")

    # 1. Real-time Price Data
    print("\n" + "=" * 40)
    print("1. REAL-TIME PRICE DATA")
    print("=" * 40)
    print("\nHow it works:")
    print("- We use yfinance library which connects to Yahoo Finance API")
    print("- NSE stocks use '.NS' suffix (e.g., RELIANCE.NS)")
    print("- BSE stocks use '.BO' suffix (e.g., RELIANCE.BO)")
    print("- Data has ~15-20 min delay (free tier)")

    stock = "RELIANCE"
    print(f"\nFetching real-time data for {stock}...")
    price_data = fetcher.get_realtime_price(stock)

    if "error" not in price_data:
        print(f"\nCompany: {price_data['company_name']}")
        print(f"Current Price: ₹{price_data['current_price']:,.2f}")
        print(f"Change: ₹{price_data['change']:,.2f} ({price_data['change_percent']}%)")
        print(f"Day Range: ₹{price_data['day_low']:,.2f} - ₹{price_data['day_high']:,.2f}")
        print(f"52 Week Range: ₹{price_data['fifty_two_week_low']:,.2f} - ₹{price_data['fifty_two_week_high']:,.2f}")
        print(f"Volume: {price_data['volume']:,}")

    # 2. Fundamental Data
    print("\n" + "=" * 40)
    print("2. FUNDAMENTAL DATA")
    print("=" * 40)
    print("\nHow it works:")
    print("- Yahoo Finance provides extensive fundamental data")
    print("- Includes: P/E, P/B, Market Cap, Revenue, Margins, etc.")
    print("- Financial statements are also available")

    print(f"\nFetching fundamentals for {stock}...")
    fundamentals = fetcher.get_fundamentals(stock)

    if "error" not in fundamentals:
        print(f"\nCompany: {fundamentals['company_name']}")
        print(f"Sector: {fundamentals['sector']}")
        print(f"Industry: {fundamentals['industry']}")

        print("\n--- Valuation Metrics ---")
        val = fundamentals['valuation']
        print(f"Market Cap: ₹{val['market_cap_formatted']}")
        print(f"P/E Ratio: {val['pe_ratio']}")
        print(f"P/B Ratio: {val['price_to_book']}")
        print(f"EV/EBITDA: {val['ev_to_ebitda']}")

        print("\n--- Profitability ---")
        prof = fundamentals['profitability']
        print(f"Profit Margin: {prof['profit_margin']}")
        print(f"ROE: {prof['return_on_equity']}")
        print(f"ROA: {prof['return_on_assets']}")

        print("\n--- Financial Health ---")
        health = fundamentals['financial_health']
        print(f"Total Cash: ₹{health['total_cash']}")
        print(f"Total Debt: ₹{health['total_debt']}")
        print(f"Debt/Equity: {health['debt_to_equity']}")

    # 3. Market Indices
    print("\n" + "=" * 40)
    print("3. MARKET INDICES")
    print("=" * 40)

    for index_name in ["NIFTY50", "SENSEX", "BANKNIFTY"]:
        index_data = fetcher.get_index_data(index_name)
        if "error" not in index_data:
            change_symbol = "▲" if index_data['change'] >= 0 else "▼"
            print(f"{index_name}: {index_data['current_price']:,.2f} {change_symbol} {index_data['change_percent']}%")

    return fetcher


if __name__ == "__main__":
    demo_data_fetching()
