"""
FastAPI Backend for Bloomberg Terminal
======================================
Serves stock data, fundamentals, news, and strategy analysis.
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import re
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uvicorn
import feedparser

from stock_universe import (
    NIFTY_50, NIFTY_NEXT_50, NIFTY_MIDCAP_100, NIFTY_SMALLCAP_100,
    ALL_STOCKS, ADDITIONAL_STOCKS, STOCKS_BY_CATEGORY, parse_custom_symbols
)
from trading_strategies import TradingStrategies
from backtester import Backtester

app = FastAPI(title="Indian Stock Terminal API", version="2.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=20)

# Cache for stock data
CACHE = {}
CACHE_DURATION = 300  # 5 minutes

# All Nifty Indices
INDICES = {
    "NIFTY 50": "^NSEI",
    "NIFTY BANK": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
    "NIFTY NEXT 50": "^NSMIDCP",
    "NIFTY MIDCAP 50": "NIFTYMIDCAP50.NS",
    "NIFTY 100": "^CNX100",
    "NIFTY 200": "^CNX200",
    "NIFTY 500": "^CNX500",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY ENERGY": "^CNXENERGY",
    "NIFTY INFRA": "^CNXINFRA",
    "NIFTY PSE": "^CNXPSE",
    "NIFTY MEDIA": "^CNXMEDIA",
    "NIFTY PRIVATE BANK": "^NIFTYPVTBANK",
    "NIFTY COMMODITIES": "^CNXCMDT",
    "NIFTY CONSUMPTION": "^CNXCONSUME",
    "NIFTY FIN SERVICE": "^CNXFIN",
    "NIFTY CPSE": "^CNXCPSE",
    "NIFTY GROWSECT 15": "^CNXGROWTH",
    "NIFTY MNC": "^CNXMNC",
    "NIFTY SERV SECTOR": "^CNXSERVICE",
    "INDIA VIX": "^INDIAVIX",
}

GLOBAL_INDICES = {
    "DOW JONES": "^DJI",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "FTSE 100": "^FTSE",
    "DAX": "^GDAXI",
    "NIKKEI 225": "^N225",
    "HANG SENG": "^HSI",
    "SHANGHAI": "000001.SS",
    "KOSPI": "^KS11",
    "ASX 200": "^AXJO",
}

COMMODITIES = {
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "CRUDE OIL": "CL=F",
    "NATURAL GAS": "NG=F",
    "COPPER": "HG=F",
    "PLATINUM": "PL=F",
    "PALLADIUM": "PA=F",
}

# Advanced Screener Templates (simplified for yfinance data availability)
SCREENER_TEMPLATES = {
    "high_quality_multibagger": {
        "name": "High Quality Multibagger",
        "description": "High ROE, low debt, good margins - like Asian Paints/Titan",
        "filters": {
            "market_cap_min": 20000000000,  # 2000 Cr
            "roe_min": 15,
            "debt_to_equity_max": 100,
            "operating_margin_min": 10,
        }
    },
    "early_multibagger": {
        "name": "Early Multibagger",
        "description": "Small/Mid caps with strong fundamentals",
        "filters": {
            "market_cap_min": 5000000000,  # 500 Cr
            "market_cap_max": 100000000000,  # 10000 Cr
            "roe_min": 12,
            "debt_to_equity_max": 150,
        }
    },
    "peg_multibagger": {
        "name": "PEG Multibagger",
        "description": "Growth at reasonable price (PEG < 1.5)",
        "filters": {
            "peg_ratio_max": 1.5,
            "roe_min": 12,
        }
    },
    "cash_flow_strength": {
        "name": "Cash Flow Strength",
        "description": "Positive free cash flow companies",
        "filters": {
            "free_cash_flow_positive": True,
            "roe_min": 10,
        }
    },
    "low_debt_quality": {
        "name": "Low Debt Quality",
        "description": "Quality companies with minimal debt",
        "filters": {
            "market_cap_min": 20000000000,  # 2000 Cr
            "roe_min": 12,
            "debt_to_equity_max": 50,
        }
    },
    "high_margin_business": {
        "name": "High Margin Business",
        "description": "Companies with strong operating margins",
        "filters": {
            "operating_margin_min": 15,
            "profit_margin_min": 10,
            "market_cap_min": 10000000000,
        }
    },
    "value_stocks": {
        "name": "Value Stocks",
        "description": "Low PE with decent fundamentals",
        "filters": {
            "pe_max": 20,
            "roe_min": 10,
            "market_cap_min": 10000000000,
        }
    },
    "near_52_week_high": {
        "name": "Near 52-Week High",
        "description": "Stocks showing momentum near highs",
        "filters": {
            "near_52_week_high": True,
            "market_cap_min": 10000000000,
        }
    },
    "large_cap_quality": {
        "name": "Large Cap Quality",
        "description": "Blue chip stocks with strong fundamentals",
        "filters": {
            "market_cap_min": 500000000000,  # 50000 Cr
            "roe_min": 12,
        }
    },
    "above_200_dma": {
        "name": "Above 200 DMA",
        "description": "Stocks in long-term uptrend",
        "filters": {
            "price_above_200_dma": True,
            "market_cap_min": 10000000000,
        }
    },
    "ultimate_multibagger": {
        "name": "Ultimate Multibagger",
        "description": "Mid cap, high ROE, low debt, above 200 DMA",
        "filters": {
            "market_cap_min": 10000000000,  # 1000 Cr
            "market_cap_max": 200000000000,  # 20000 Cr
            "roe_min": 15,
            "debt_to_equity_max": 100,
            "price_above_200_dma": True,
        }
    },
}


def get_cache_key(key: str) -> str:
    return f"{key}_{datetime.now().strftime('%Y%m%d%H%M')}"


def fetch_news_rss(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
    """Fetch news from Google News RSS feed"""
    try:
        # Use Google News RSS
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(url)

        news_items = []
        for entry in feed.entries[:num_results]:
            title = entry.get('title', 'No title')
            link = entry.get('link', '')
            source = entry.get('source', {}).get('title', 'Unknown')
            published = entry.get('published', '')

            # Sentiment analysis
            positive_words = ['surge', 'gain', 'rise', 'up', 'high', 'bull', 'growth', 'profit', 'strong', 'buy', 'rally', 'boost', 'beat', 'soar', 'jump']
            negative_words = ['fall', 'drop', 'down', 'low', 'bear', 'loss', 'weak', 'sell', 'crash', 'decline', 'miss', 'cut', 'plunge', 'sink', 'tumble']

            title_lower = title.lower()
            pos_count = sum(1 for word in positive_words if word in title_lower)
            neg_count = sum(1 for word in negative_words if word in title_lower)

            if pos_count > neg_count:
                sentiment = "positive"
                sentiment_score = min(pos_count * 0.2, 1.0)
            elif neg_count > pos_count:
                sentiment = "negative"
                sentiment_score = -min(neg_count * 0.2, 1.0)
            else:
                sentiment = "neutral"
                sentiment_score = 0

            news_items.append({
                "title": title,
                "url": link,
                "source": source,
                "time": published,
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
            })

        return news_items
    except Exception as e:
        print(f"Error fetching news RSS: {e}")
        return []


def scrape_table_data(section, max_rows=None):
    """Helper to scrape table data from a section"""
    result = []
    table = section.find('table') if section else None
    if not table:
        return result

    headers_row = table.find('thead')
    headers = []
    if headers_row:
        headers = [th.get_text(strip=True) for th in headers_row.find_all('th')]

    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        if max_rows:
            rows = rows[:max_rows]
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if headers and cells:
                row_data = {}
                for i in range(min(len(headers), len(cells))):
                    row_data[headers[i]] = cells[i].get_text(strip=True)
                result.append(row_data)
    return result


def get_financial_data_from_yfinance(symbol: str) -> Dict[str, Any]:
    """Get financial data from yfinance as fallback"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        data = {}

        # Get quarterly financials
        try:
            quarterly = ticker.quarterly_financials
            if quarterly is not None and not quarterly.empty:
                quarterly_data = []
                for col in quarterly.columns[:8]:  # Last 8 quarters
                    row = {"Period": col.strftime("%b %Y")}
                    for idx in quarterly.index[:10]:  # Top 10 metrics
                        val = quarterly.loc[idx, col]
                        # Convert to Cr
                        if pd.notna(val):
                            row[str(idx).replace(" ", "")] = f"{val/10000000:.2f}"
                    quarterly_data.append(row)
                data['quarterly_results'] = quarterly_data
        except:
            pass

        # Get annual income statement
        try:
            income = ticker.financials
            if income is not None and not income.empty:
                income_data = []
                for idx in income.index[:15]:
                    row = {"": str(idx)}
                    for col in income.columns[:6]:
                        val = income.loc[idx, col]
                        if pd.notna(val):
                            row[col.strftime("%b %Y")] = f"{val/10000000:.2f}"
                        else:
                            row[col.strftime("%b %Y")] = "-"
                    income_data.append(row)
                data['profit_loss'] = income_data
        except:
            pass

        # Get balance sheet
        try:
            balance = ticker.balance_sheet
            if balance is not None and not balance.empty:
                balance_data = []
                for idx in balance.index[:15]:
                    row = {"": str(idx)}
                    for col in balance.columns[:6]:
                        val = balance.loc[idx, col]
                        if pd.notna(val):
                            row[col.strftime("%b %Y")] = f"{val/10000000:.2f}"
                        else:
                            row[col.strftime("%b %Y")] = "-"
                    balance_data.append(row)
                data['balance_sheet'] = balance_data
        except:
            pass

        # Get cash flow
        try:
            cashflow = ticker.cashflow
            if cashflow is not None and not cashflow.empty:
                cashflow_data = []
                for idx in cashflow.index[:10]:
                    row = {"": str(idx)}
                    for col in cashflow.columns[:6]:
                        val = cashflow.loc[idx, col]
                        if pd.notna(val):
                            row[col.strftime("%b %Y")] = f"{val/10000000:.2f}"
                        else:
                            row[col.strftime("%b %Y")] = "-"
                    cashflow_data.append(row)
                data['cash_flows'] = cashflow_data
        except:
            pass

        # Get major holders (shareholding)
        try:
            holders = ticker.major_holders
            if holders is not None and not holders.empty:
                shareholding_data = []
                for idx, row in holders.iterrows():
                    shareholding_data.append({
                        "Category": str(row.iloc[1]) if len(row) > 1 else str(idx),
                        "Holding": str(row.iloc[0]) if len(row) > 0 else "N/A"
                    })
                data['shareholding'] = shareholding_data
        except:
            pass

        # Get institutional holders
        try:
            inst = ticker.institutional_holders
            if inst is not None and not inst.empty:
                data['institutional_holders'] = inst.head(10).to_dict('records')
        except:
            pass

        return data
    except Exception as e:
        print(f"Error getting yfinance data for {symbol}: {e}")
        return {}


def get_peer_comparison(symbol: str, industry: str) -> List[Dict[str, Any]]:
    """Get peer comparison data by finding stocks in same industry"""
    peers = []
    try:
        # Industry to stock mapping for common industries
        industry_stocks = {
            "Information Technology Services": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "MPHASIS", "COFORGE", "PERSISTENT"],
            "Banks": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK", "INDUSINDBK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB"],
            "Oil & Gas": ["RELIANCE", "ONGC", "IOC", "BPCL", "HINDPETRO", "GAIL", "PETRONET", "MRPL"],
            "Automobiles": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO", "EICHERMOT", "ASHOKLEY", "TVSMOTOR"],
            "Pharmaceuticals": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "BIOCON", "LUPIN", "AUROPHARMA", "TORNTPHARM"],
            "Consumer Goods": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR", "MARICO", "GODREJCP", "COLPAL"],
            "Steel": ["TATASTEEL", "JSWSTEEL", "HINDALCO", "SAIL", "JINDALSTEL", "NMDC", "VEDL"],
            "Power": ["POWERGRID", "NTPC", "TATAPOWER", "ADANIGREEN", "TORNTPOWER", "JSW ENERGY", "NHPC"],
            "Telecom": ["BHARTIARTL", "JIO", "VODAFONE", "TATACOMM"],
            "Real Estate": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "BRIGADE", "SOBHA"],
            "Insurance": ["HDFCLIFE", "SBILIFE", "ICICIPRULI", "ICICIGI", "BAJAJFINSV"],
        }

        # Find matching industry
        matching_stocks = []
        for ind_name, stocks in industry_stocks.items():
            if ind_name.lower() in industry.lower() or industry.lower() in ind_name.lower():
                matching_stocks = stocks
                break

        # If no match found, use sector-based matching from ALL_STOCKS
        if not matching_stocks:
            matching_stocks = NIFTY_50[:15]

        # Remove current symbol and get peer data
        peer_symbols = [s for s in matching_stocks if s != symbol][:10]

        for peer_symbol in peer_symbols:
            try:
                ticker = yf.Ticker(f"{peer_symbol}.NS")
                info = ticker.info
                if info.get("currentPrice"):
                    peers.append({
                        "S.No.": len(peers) + 1,
                        "Name": info.get("shortName", peer_symbol),
                        "CMP Rs.": f"{info.get('currentPrice', 0):.2f}",
                        "P/E": f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else "N/A",
                        "Mar Cap Rs.Cr.": f"{info.get('marketCap', 0)/10000000:.0f}" if info.get('marketCap') else "N/A",
                        "ROCE %": f"{(info.get('returnOnEquity', 0) or 0) * 100:.2f}" if info.get('returnOnEquity') else "N/A",
                        "D/E": f"{(info.get('debtToEquity', 0) or 0)/100:.2f}" if info.get('debtToEquity') else "N/A",
                        "ROE %": f"{(info.get('returnOnEquity', 0) or 0) * 100:.2f}" if info.get('returnOnEquity') else "N/A",
                    })
            except:
                continue

        return peers
    except Exception as e:
        print(f"Error getting peers for {symbol}: {e}")
        return []


def scrape_screener_data(symbol: str) -> Dict[str, Any]:
    """Scrape comprehensive fundamental data from Screener.in"""
    try:
        url = f"https://www.screener.in/company/{symbol}/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')
        data = {}

        # Get key ratios from the ratios section
        ratios_section = soup.find('section', {'id': 'ratios'})
        if ratios_section:
            ratio_items = ratios_section.find_all('li', class_='flex')
            for item in ratio_items:
                name_elem = item.find('span', class_='name')
                value_elem = item.find('span', class_='value')
                if name_elem and value_elem:
                    name = name_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    data[name] = value

        # Get top section data (Market Cap, Current Price, etc.)
        top_ratios = soup.find('ul', {'id': 'top-ratios'})
        if top_ratios:
            items = top_ratios.find_all('li')
            for item in items:
                name_elem = item.find('span', class_='name')
                value_elem = item.find('span', class_='number')
                if name_elem and value_elem:
                    name = name_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    data[name] = value

        # Get quarterly results (all rows)
        quarters_section = soup.find('section', {'id': 'quarters'})
        data['quarterly_results'] = scrape_table_data(quarters_section, max_rows=15)

        # Get Profit & Loss (Annual)
        profit_loss_section = soup.find('section', {'id': 'profit-loss'})
        data['profit_loss'] = scrape_table_data(profit_loss_section, max_rows=20)

        # Get compounded growth rates from profit-loss section
        if profit_loss_section:
            growth_cards = profit_loss_section.find_all('div', class_='ranges')
            growth_data = {}
            for card in growth_cards:
                title = card.find_previous_sibling('h6')
                if title:
                    title_text = title.get_text(strip=True)
                    ranges = {}
                    for item in card.find_all('div', class_='range-value'):
                        period = item.find('span', class_='name')
                        value = item.find('span', class_='value')
                        if period and value:
                            ranges[period.get_text(strip=True)] = value.get_text(strip=True)
                    growth_data[title_text] = ranges
            data['growth_metrics'] = growth_data

        # Get Balance Sheet
        balance_sheet_section = soup.find('section', {'id': 'balance-sheet'})
        data['balance_sheet'] = scrape_table_data(balance_sheet_section, max_rows=20)

        # Get Cash Flows
        cash_flow_section = soup.find('section', {'id': 'cash-flow'})
        data['cash_flows'] = scrape_table_data(cash_flow_section, max_rows=15)

        # Get Ratios (historical)
        ratios_table_section = soup.find('section', {'id': 'ratios'})
        if ratios_table_section:
            data['ratios_history'] = scrape_table_data(ratios_table_section, max_rows=15)

        # Get peer comparison
        peers_section = soup.find('section', {'id': 'peers'})
        data['peers'] = scrape_table_data(peers_section, max_rows=15)

        # Get shareholding pattern
        shareholding_section = soup.find('section', {'id': 'shareholding'})
        data['shareholding'] = scrape_table_data(shareholding_section)

        # Get pros and cons
        pros_section = soup.find('div', class_='pros')
        if pros_section:
            pros = [li.get_text(strip=True) for li in pros_section.find_all('li')]
            data['pros'] = pros

        cons_section = soup.find('div', class_='cons')
        if cons_section:
            cons = [li.get_text(strip=True) for li in cons_section.find_all('li')]
            data['cons'] = cons

        return data

    except Exception as e:
        print(f"Error scraping {symbol}: {e}")
        # Fallback to yfinance data
        print(f"Using yfinance fallback for {symbol}")
        return get_financial_data_from_yfinance(symbol)


def get_stock_fundamentals(symbol: str) -> Dict[str, Any]:
    """Get comprehensive fundamentals from Yahoo Finance and Screener.in"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        info = ticker.info

        # Basic info from Yahoo Finance
        fundamentals = {
            "symbol": symbol,
            "name": info.get("longName", info.get("shortName", symbol)),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "previous_close": info.get("previousClose", 0),
            "open": info.get("open", 0),
            "day_high": info.get("dayHigh", 0),
            "day_low": info.get("dayLow", 0),
            "volume": info.get("volume", 0),
            "avg_volume": info.get("averageVolume", 0),
            "market_cap": info.get("marketCap", 0),
            "enterprise_value": info.get("enterpriseValue", 0),
            "pe_ratio": info.get("trailingPE", info.get("forwardPE", "N/A")),
            "forward_pe": info.get("forwardPE", "N/A"),
            "peg_ratio": info.get("pegRatio", "N/A"),
            "price_to_book": info.get("priceToBook", "N/A"),
            "price_to_sales": info.get("priceToSalesTrailing12Months", "N/A"),
            "book_value": info.get("bookValue", "N/A"),
            "dividend_yield": info.get("dividendYield", 0),
            "dividend_rate": info.get("dividendRate", 0),
            "payout_ratio": info.get("payoutRatio", "N/A"),
            "beta": info.get("beta", "N/A"),
            "52_week_high": info.get("fiftyTwoWeekHigh", 0),
            "52_week_low": info.get("fiftyTwoWeekLow", 0),
            "50_day_avg": info.get("fiftyDayAverage", 0),
            "200_day_avg": info.get("twoHundredDayAverage", 0),
            "eps": info.get("trailingEps", "N/A"),
            "forward_eps": info.get("forwardEps", "N/A"),
            "revenue": info.get("totalRevenue", 0),
            "revenue_growth": info.get("revenueGrowth", "N/A"),
            "gross_profit": info.get("grossProfits", 0),
            "gross_margins": info.get("grossMargins", "N/A"),
            "operating_margins": info.get("operatingMargins", "N/A"),
            "profit_margins": info.get("profitMargins", "N/A"),
            "ebitda": info.get("ebitda", 0),
            "ebitda_margins": info.get("ebitdaMargins", "N/A"),
            "operating_cashflow": info.get("operatingCashflow", 0),
            "free_cashflow": info.get("freeCashflow", 0),
            "total_cash": info.get("totalCash", 0),
            "total_debt": info.get("totalDebt", 0),
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "current_ratio": info.get("currentRatio", "N/A"),
            "quick_ratio": info.get("quickRatio", "N/A"),
            "return_on_equity": info.get("returnOnEquity", "N/A"),
            "return_on_assets": info.get("returnOnAssets", "N/A"),
            "revenue_per_share": info.get("revenuePerShare", "N/A"),
            "earnings_growth": info.get("earningsGrowth", "N/A"),
            "shares_outstanding": info.get("sharesOutstanding", 0),
            "float_shares": info.get("floatShares", 0),
            "held_percent_insiders": info.get("heldPercentInsiders", "N/A"),
            "held_percent_institutions": info.get("heldPercentInstitutions", "N/A"),
            "short_ratio": info.get("shortRatio", "N/A"),
            "target_mean_price": info.get("targetMeanPrice", "N/A"),
            "target_high_price": info.get("targetHighPrice", "N/A"),
            "target_low_price": info.get("targetLowPrice", "N/A"),
            "recommendation": info.get("recommendationKey", "N/A"),
            "number_of_analysts": info.get("numberOfAnalystOpinions", 0),
        }

        # Calculate additional metrics
        if fundamentals["current_price"] and fundamentals["52_week_high"]:
            fundamentals["distance_from_52w_high"] = round(
                ((fundamentals["52_week_high"] - fundamentals["current_price"]) / fundamentals["52_week_high"]) * 100, 2
            )

        if fundamentals["current_price"] and fundamentals["52_week_low"]:
            fundamentals["distance_from_52w_low"] = round(
                ((fundamentals["current_price"] - fundamentals["52_week_low"]) / fundamentals["52_week_low"]) * 100, 2
            )

        # Calculate change
        if fundamentals["current_price"] and fundamentals["previous_close"]:
            fundamentals["change"] = round(fundamentals["current_price"] - fundamentals["previous_close"], 2)
            fundamentals["change_percent"] = round(
                (fundamentals["change"] / fundamentals["previous_close"]) * 100, 2
            )

        # Try to get additional data from Screener.in
        screener_data = scrape_screener_data(symbol)
        if screener_data:
            # Map screener data to our format
            screener_mapping = {
                "ROE": "roe",
                "ROCE": "roce",
                "Debt to equity": "debt_to_equity_screener",
                "Sales growth": "sales_growth",
                "Profit growth": "profit_growth",
                "OPM": "operating_profit_margin",
                "NPM": "net_profit_margin",
                "EV / EBITDA": "ev_to_ebitda",
                "Price to Earning": "pe_screener",
                "Price to book value": "pb_screener",
                "Dividend Payout %": "dividend_payout",
                "Face Value": "face_value",
                "Stock P/E": "stock_pe",
                "Industry P/E": "industry_pe",
                "Intrinsic Value": "intrinsic_value",
                "Graham Number": "graham_number",
                "PEG Ratio": "peg_screener",
                "Promoter holding": "promoter_holding",
            }

            for screener_key, our_key in screener_mapping.items():
                if screener_key in screener_data:
                    fundamentals[our_key] = screener_data[screener_key]

            # Add all financial statements and data from Screener.in
            financial_fields = [
                "quarterly_results", "profit_loss", "balance_sheet",
                "cash_flows", "ratios_history", "growth_metrics",
                "peers", "shareholding", "pros", "cons"
            ]
            for field in financial_fields:
                if field in screener_data and screener_data[field]:
                    fundamentals[field] = screener_data[field]

        # If no peers data, generate from industry
        if not fundamentals.get("peers"):
            industry = fundamentals.get("industry", "")
            fundamentals["peers"] = get_peer_comparison(symbol, industry)

        return fundamentals

    except Exception as e:
        print(f"Error getting fundamentals for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def get_stock_history(symbol: str, period: str = "1y") -> Dict[str, Any]:
    """Get historical price data for a stock"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period=period)

        if hist.empty:
            return {"error": "No data available"}

        # Convert to list of dictionaries
        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })

        # Calculate technical indicators
        closes = hist["Close"].values

        # EMAs
        ema20 = pd.Series(closes).ewm(span=20).mean().tolist()
        ema50 = pd.Series(closes).ewm(span=50).mean().tolist()
        ema200 = pd.Series(closes).ewm(span=200).mean().tolist()

        # RSI
        delta = pd.Series(closes).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).tolist()

        # Add indicators to data
        for i, d in enumerate(data):
            d["ema20"] = round(ema20[i], 2) if i < len(ema20) and not np.isnan(ema20[i]) else None
            d["ema50"] = round(ema50[i], 2) if i < len(ema50) and not np.isnan(ema50[i]) else None
            d["ema200"] = round(ema200[i], 2) if i < len(ema200) and not np.isnan(ema200[i]) else None
            d["rsi"] = round(rsi[i], 2) if i < len(rsi) and not np.isnan(rsi[i]) else None

        # Calculate support/resistance
        highs = hist["High"].values
        lows = hist["Low"].values

        # Simple support/resistance based on recent pivots
        resistance = float(np.max(highs[-20:]))
        support = float(np.min(lows[-20:]))

        # ATH/ATL
        ath = float(np.max(highs))
        atl = float(np.min(lows))

        return {
            "symbol": symbol,
            "data": data,
            "indicators": {
                "support": round(support, 2),
                "resistance": round(resistance, 2),
                "ath": round(ath, 2),
                "atl": round(atl, 2),
                "current_rsi": round(rsi[-1], 2) if rsi and not np.isnan(rsi[-1]) else None,
            }
        }

    except Exception as e:
        print(f"Error getting history for {symbol}: {e}")
        return {"error": str(e)}


def run_strategy_scan(symbol: str, strategy_name: str = None) -> Dict[str, Any]:
    """Run trading strategies on a stock"""
    try:
        strategies = TradingStrategies()
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="2y")

        if hist.empty or len(hist) < 200:
            return {"symbol": symbol, "error": "Insufficient data"}

        results = {}
        strategy_methods = [
            ("ATH Breakout", strategies.strategy_200dma_ath_breakout),
            ("52-Week Momentum", strategies.strategy_52week_high_momentum),
            ("VCP Pattern", strategies.strategy_vcp),
            ("Cup & Handle", strategies.strategy_cup_and_handle),
            ("Donchian Breakout", strategies.strategy_donchian_turtle),
            ("MA Stack", strategies.strategy_ma_momentum_stack),
            ("Relative Strength", strategies.strategy_relative_strength),
            ("Bollinger Squeeze", strategies.strategy_bollinger_squeeze),
            ("Base Breakout", strategies.strategy_base_breakout),
            ("Stage Analysis", strategies.strategy_stage_analysis),
        ]

        # If specific strategy requested, only run that one
        if strategy_name:
            strategy_methods = [(n, m) for n, m in strategy_methods if n == strategy_name]

        for name, method in strategy_methods:
            try:
                result = method(hist)
                if result:
                    # Handle StrategySignal enum
                    signal_str = result.signal.value if hasattr(result.signal, 'value') else str(result.signal)
                    # Combine conditions_met and conditions_failed into conditions dict
                    conditions = {}
                    for c in getattr(result, 'conditions_met', []):
                        conditions[c] = True
                    for c in getattr(result, 'conditions_failed', []):
                        conditions[c] = False

                    results[name] = {
                        "score": result.score,
                        "signal": signal_str,
                        "entry_price": result.entry_price,
                        "stop_loss": result.stop_loss,
                        "target": result.target,
                        "conditions": conditions,
                    }
            except Exception as e:
                print(f"Error running {name} on {symbol}: {e}")
                continue

        # Calculate overall recommendation
        if results:
            avg_score = sum(r["score"] for r in results.values()) / len(results)
            buy_signals = sum(1 for r in results.values() if "BUY" in r["signal"])
            sell_signals = sum(1 for r in results.values() if "SELL" in r["signal"])

            if avg_score >= 70 and buy_signals >= 5:
                recommendation = "STRONG BUY"
            elif avg_score >= 50 and buy_signals > sell_signals:
                recommendation = "BUY"
            elif avg_score <= 30 and sell_signals >= 5:
                recommendation = "STRONG SELL"
            elif avg_score <= 50 and sell_signals > buy_signals:
                recommendation = "SELL"
            else:
                recommendation = "HOLD"

            return {
                "symbol": symbol,
                "strategies": results,
                "avg_score": round(avg_score, 2),
                "recommendation": recommendation,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
            }

        return {"symbol": symbol, "strategies": {}, "recommendation": "HOLD"}

    except Exception as e:
        print(f"Error running strategy scan for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}


def run_backtest(symbol: str, strategy: str = "ma_crossover") -> Dict[str, Any]:
    """Run backtest on a stock"""
    try:
        backtester = Backtester()
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="3y")

        if hist.empty:
            return {"error": "No data available"}

        result = backtester.run_backtest(hist, strategy=strategy)

        return {
            "symbol": symbol,
            "strategy": strategy,
            "total_return": round(result.total_return * 100, 2),
            "cagr": round(result.cagr * 100, 2),
            "sharpe_ratio": round(result.sharpe_ratio, 2),
            "sortino_ratio": round(result.sortino_ratio, 2),
            "max_drawdown": round(result.max_drawdown * 100, 2),
            "win_rate": round(result.win_rate * 100, 2),
            "profit_factor": round(result.profit_factor, 2),
            "total_trades": result.total_trades,
            "avg_trade_return": round(result.avg_trade_return * 100, 2),
            "calmar_ratio": round(result.calmar_ratio, 2) if hasattr(result, 'calmar_ratio') else None,
        }

    except Exception as e:
        print(f"Error running backtest for {symbol}: {e}")
        return {"error": str(e)}


def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict[str, Any]:
    """Calculate support and resistance levels using pivot points and price clusters"""
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values

    supports = []
    resistances = []

    # Find local minima (supports) and maxima (resistances)
    for i in range(window, len(df) - window):
        if lows[i] == min(lows[i-window:i+window+1]):
            supports.append(float(lows[i]))
        if highs[i] == max(highs[i-window:i+window+1]):
            resistances.append(float(highs[i]))

    # Cluster nearby levels (within 2%)
    def cluster_levels(levels, threshold=0.02):
        if not levels:
            return []
        levels = sorted(levels)
        clusters = []
        current_cluster = [levels[0]]
        for level in levels[1:]:
            if (level - current_cluster[0]) / current_cluster[0] < threshold:
                current_cluster.append(level)
            else:
                clusters.append(sum(current_cluster) / len(current_cluster))
                current_cluster = [level]
        clusters.append(sum(current_cluster) / len(current_cluster))
        return clusters

    supports = cluster_levels(supports)
    resistances = cluster_levels(resistances)
    current_price = float(closes[-1])

    supports_below = [s for s in supports if s < current_price]
    resistances_above = [r for r in resistances if r > current_price]

    nearest_support = max(supports_below) if supports_below else current_price * 0.9
    nearest_resistance = min(resistances_above) if resistances_above else current_price * 1.1
    next_support = max([s for s in supports_below if s < nearest_support], default=nearest_support * 0.95)
    next_resistance = min([r for r in resistances_above if r > nearest_resistance], default=nearest_resistance * 1.05)

    return {
        "all_supports": supports[-10:],
        "all_resistances": resistances[-10:],
        "nearest_support": float(round(nearest_support, 2)),
        "nearest_resistance": float(round(nearest_resistance, 2)),
        "next_support": float(round(next_support, 2)),
        "next_resistance": float(round(next_resistance, 2)),
        "support_distance_pct": float(round((current_price - nearest_support) / current_price * 100, 2)),
        "resistance_distance_pct": float(round((nearest_resistance - current_price) / current_price * 100, 2)),
    }


def calculate_breakout_probability(df: pd.DataFrame, resistance: float) -> float:
    """Calculate probability of breaking resistance based on momentum and volume"""
    if len(df) < 50:
        return 50.0

    recent = df.tail(20)
    close = recent['Close'].values
    volume = recent['Volume'].values
    factors = []

    # Price momentum
    price_change = (close[-1] - close[0]) / close[0]
    factors.append(min(70, max(30, 50 + price_change * 200)))

    # Volume expansion
    avg_vol = df['Volume'].tail(50).mean()
    recent_vol = volume[-5:].mean()
    vol_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
    factors.append(min(80, max(20, 40 + vol_ratio * 20)))

    # Distance to resistance
    distance_pct = (resistance - close[-1]) / close[-1]
    factors.append(70 if distance_pct < 0.02 else 60 if distance_pct < 0.05 else 40)

    # Higher lows pattern
    lows = recent['Low'].values
    higher_lows = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])
    factors.append(min(75, max(25, 30 + higher_lows * 3)))

    return float(round(sum(factors) / len(factors), 1))


def get_exit_rule_description(strategy_name: str) -> str:
    """Get human-readable exit rule for each strategy"""
    rules = {
        "ATH Breakout": "Exit when price closes below 200-day EMA",
        "52-Week Momentum": "Exit when price closes below 50-day EMA",
        "VCP Pattern": "Exit when price breaks below pivot low",
        "Cup & Handle": "Exit when price falls below handle low / 50 EMA",
        "Donchian Breakout": "Exit when price breaks 20-day low",
        "MA Stack": "Exit when 21 EMA crosses below 50 EMA (death cross)",
        "Relative Strength": "Exit when price closes below 50-day EMA",
        "Bollinger Squeeze": "Exit when price closes below 20-day SMA",
        "Base Breakout": "Exit when price breaks below base low",
        "Stage Analysis": "Exit when price closes below 200-day EMA (Stage 4)",
    }
    return rules.get(strategy_name, "Exit when price closes below 200-day EMA")


def run_strategy_backtest(symbol: str, strategy_name: str) -> Dict[str, Any]:
    """Run VALUE INVESTING backtest with long-term exit strategies, S/R levels, P/E tracking"""
    try:
        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="5y")
        info = ticker.info or {}

        if hist.empty or len(hist) < 250:
            return {"error": "Insufficient data for backtest"}

        # Calculate indicators
        hist['EMA_200'] = hist['Close'].ewm(span=200, adjust=False).mean()
        hist['EMA_50'] = hist['Close'].ewm(span=50, adjust=False).mean()
        hist['EMA_21'] = hist['Close'].ewm(span=21, adjust=False).mean()
        hist['SMA_20'] = hist['Close'].rolling(20).mean()
        hist['ATH'] = hist['High'].cummax()
        hist['ATH_prev'] = hist['ATH'].shift(1)
        hist['Low_20'] = hist['Low'].rolling(20).min()
        hist['High_20'] = hist['High'].rolling(20).max()

        # VALUE INVESTING EXIT CONDITIONS (hold until trend breaks)
        exit_conditions = {
            "ATH Breakout": lambda row, entry: row['Close'] < row['EMA_200'],
            "52-Week Momentum": lambda row, entry: row['Close'] < row['EMA_50'],
            "VCP Pattern": lambda row, entry: row['Close'] < entry.get('pivot_low', row['Low_20']),
            "Cup & Handle": lambda row, entry: row['Close'] < entry.get('handle_low', row['EMA_50']),
            "Donchian Breakout": lambda row, entry: row['Close'] < row['Low_20'],
            "MA Stack": lambda row, entry: row['EMA_21'] < row['EMA_50'],
            "Relative Strength": lambda row, entry: row['Close'] < row['EMA_50'],
            "Bollinger Squeeze": lambda row, entry: row['Close'] < row['SMA_20'],
            "Base Breakout": lambda row, entry: row['Close'] < entry.get('base_low', row['EMA_50']),
            "Stage Analysis": lambda row, entry: row['Close'] < row['EMA_200'],
        }

        # Entry conditions
        def check_entry(row, prev_row, strategy):
            try:
                if strategy == "ATH Breakout":
                    return row['Close'] > row['ATH_prev'] and row['Close'] > row['EMA_200']
                elif strategy == "52-Week Momentum":
                    return row['Close'] > prev_row['High'] * 0.95 and row['Close'] > row['EMA_50']
                elif strategy == "VCP Pattern":
                    return row['Close'] > row['High_20'] and row['Volume'] > hist['Volume'].rolling(20).mean().iloc[-1] * 1.3
                elif strategy == "Donchian Breakout":
                    return row['Close'] > row['High_20']
                elif strategy == "MA Stack":
                    return row['EMA_21'] > row['EMA_50'] > row['EMA_200']
                else:
                    return row['Close'] > row['EMA_200'] and row['Close'] > prev_row['High']
            except:
                return False

        exit_cond = exit_conditions.get(strategy_name, lambda r, e: r['Close'] < r['EMA_200'])

        # Run backtest
        trades = []
        position = None
        capital = 100000
        equity_curve = []
        dates_list = []
        prices_list = []
        ema200_list = []
        ath_list = []

        for i in range(201, len(hist)):
            row = hist.iloc[i]
            prev_row = hist.iloc[i-1]
            date = hist.index[i]

            # Track data
            dates_list.append(date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date))
            prices_list.append(float(round(row['Close'], 2)))
            ema200_list.append(float(round(row['EMA_200'], 2)))
            ath_list.append(float(round(row['ATH'], 2)))

            if position is None:
                if check_entry(row, prev_row, strategy_name):
                    position = {
                        'entry_date': date,
                        'entry_price': float(row['Close']),
                        'ath_at_entry': float(row['ATH_prev']),
                        'pivot_low': float(hist['Low'].iloc[max(0,i-20):i].min()),
                        'handle_low': float(row['EMA_50']),
                        'base_low': float(hist['Low'].iloc[max(0,i-20):i].min()),
                        'shares': capital / row['Close']
                    }
            else:
                try:
                    if exit_cond(row, position):
                        pnl = (row['Close'] - position['entry_price']) / position['entry_price'] * 100
                        gain_from_ath = (row['Close'] - position['ath_at_entry']) / position['ath_at_entry'] * 100 if position['ath_at_entry'] > 0 else 0

                        trades.append({
                            'entry_date': position['entry_date'],
                            'exit_date': date,
                            'entry_price': position['entry_price'],
                            'exit_price': float(row['Close']),
                            'pnl_pct': pnl,
                            'gain_from_ath': gain_from_ath,
                            'days_held': (date - position['entry_date']).days,
                            'exit_reason': get_exit_rule_description(strategy_name),
                            'win': pnl > 0
                        })
                        capital = capital * (1 + pnl / 100)
                        position = None
                except:
                    pass

            current_value = position['shares'] * row['Close'] if position else capital
            equity_curve.append(float(current_value))

        # Close open position
        if position and len(hist) > 0:
            final_row = hist.iloc[-1]
            pnl = (final_row['Close'] - position['entry_price']) / position['entry_price'] * 100
            gain_from_ath = (final_row['Close'] - position['ath_at_entry']) / position['ath_at_entry'] * 100
            trades.append({
                'entry_date': position['entry_date'],
                'exit_date': hist.index[-1],
                'entry_price': position['entry_price'],
                'exit_price': float(final_row['Close']),
                'pnl_pct': pnl,
                'gain_from_ath': gain_from_ath,
                'days_held': (hist.index[-1] - position['entry_date']).days,
                'exit_reason': "Currently Holding",
                'win': pnl > 0
            })

        # Metrics
        total_return = (equity_curve[-1] / 100000 - 1) * 100 if equity_curve else 0
        winning = [t for t in trades if t['win']]
        avg_gain_from_ath = sum(t['gain_from_ath'] for t in trades) / len(trades) if trades else 0

        # Support/Resistance
        sr = calculate_support_resistance(hist)
        breakout_prob = calculate_breakout_probability(hist, sr['nearest_resistance'])

        # P/E and current info
        pe_ratio = info.get('trailingPE') or info.get('forwardPE') or 0
        current_price = float(hist['Close'].iloc[-1])
        current_ath = float(hist['ATH'].iloc[-1])
        pct_from_ath = (current_price - current_ath) / current_ath * 100

        # Format trades
        trade_markers = []
        for t in trades:
            trade_markers.append({
                "entry_date": t['entry_date'].strftime("%Y-%m-%d") if hasattr(t['entry_date'], 'strftime') else str(t['entry_date']),
                "exit_date": t['exit_date'].strftime("%Y-%m-%d") if hasattr(t['exit_date'], 'strftime') else str(t['exit_date']),
                "entry_price": float(round(t['entry_price'], 2)),
                "exit_price": float(round(t['exit_price'], 2)),
                "pnl_pct": float(round(t['pnl_pct'], 2)),
                "gain_from_ath": float(round(t['gain_from_ath'], 2)),
                "days_held": int(t['days_held']),
                "exit_reason": str(t['exit_reason']),
                "win": bool(t['win'])
            })

        # Equity as percentage
        initial = equity_curve[0] if equity_curve else 100000
        equity_pct = [float(round((e / initial - 1) * 100, 2)) for e in equity_curve]
        initial_price = prices_list[0] if prices_list else 1
        benchmark_pct = [float(round((p / initial_price - 1) * 100, 2)) for p in prices_list]

        return {
            "symbol": symbol,
            "strategy": strategy_name,
            "investment_style": "Value Investing (Long-term Hold)",
            "exit_rule": get_exit_rule_description(strategy_name),
            "metrics": {
                "total_return": float(round(total_return, 2)),
                "total_trades": len(trades),
                "winning_trades": len(winning),
                "losing_trades": len(trades) - len(winning),
                "win_rate": float(round(len(winning) / len(trades) * 100, 2)) if trades else 0,
                "avg_gain_from_ath": float(round(avg_gain_from_ath, 2)),
                "current_pe": float(round(pe_ratio, 2)) if pe_ratio else None,
                "pct_from_ath": float(round(pct_from_ath, 2)),
            },
            "current_analysis": {
                "price": float(round(current_price, 2)),
                "ath": float(round(current_ath, 2)),
                "nearest_support": sr['nearest_support'],
                "nearest_resistance": sr['nearest_resistance'],
                "next_support": sr['next_support'],
                "next_resistance": sr['next_resistance'],
                "support_distance_pct": sr['support_distance_pct'],
                "resistance_distance_pct": sr['resistance_distance_pct'],
                "breakout_probability": float(round(breakout_prob, 1)),
                "pe_ratio": float(round(pe_ratio, 2)) if pe_ratio else None,
            },
            "support_resistance": {
                "supports": [float(round(s, 2)) for s in sr['all_supports']],
                "resistances": [float(round(r, 2)) for r in sr['all_resistances']],
            },
            "timeseries": {
                "dates": dates_list[-500:],
                "prices": prices_list[-500:],
                "ema_200": ema200_list[-500:],
                "ath": ath_list[-500:],
                "equity": equity_pct[-500:],
                "benchmark": benchmark_pct[-500:],
            },
            "trades": trade_markers,
        }

    except Exception as e:
        print(f"Error running strategy backtest for {symbol}/{strategy_name}: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.post("/api/stock/{symbol}/band-analysis")
async def analyze_price_band(symbol: str, request: Dict[str, Any] = Body(...)):
    """Analyze price band for value investing: % gain, P/L, P/E at levels, breakout probability"""
    try:
        lower_band = float(request.get("lower_band", 0))
        upper_band = float(request.get("upper_band", 0))

        if not lower_band or not upper_band:
            return {"error": "Both lower_band and upper_band are required"}

        ticker = yf.Ticker(f"{symbol}.NS")
        hist = ticker.history(period="2y")
        info = ticker.info or {}

        if hist.empty:
            return {"error": "No data available"}

        current_price = float(hist['Close'].iloc[-1])
        pe_ratio = info.get('trailingPE') or info.get('forwardPE') or 0
        eps = current_price / pe_ratio if pe_ratio > 0 else 0

        sr = calculate_support_resistance(hist)
        breakout_prob = calculate_breakout_probability(hist, upper_band)

        band_analysis = {
            "lower_band": {
                "price": lower_band,
                "pct_from_current": float(round((lower_band - current_price) / current_price * 100, 2)),
                "pe_at_price": float(round(lower_band / eps, 2)) if eps > 0 else None,
                "pct_to_support": float(round((lower_band - sr['nearest_support']) / lower_band * 100, 2)),
                "pct_to_resistance": float(round((sr['nearest_resistance'] - lower_band) / lower_band * 100, 2)),
            },
            "upper_band": {
                "price": upper_band,
                "pct_from_current": float(round((upper_band - current_price) / current_price * 100, 2)),
                "pe_at_price": float(round(upper_band / eps, 2)) if eps > 0 else None,
                "pct_to_support": float(round((upper_band - sr['nearest_support']) / upper_band * 100, 2)),
                "pct_to_resistance": float(round((sr['nearest_resistance'] - upper_band) / upper_band * 100, 2)),
            },
            "band_potential_gain": float(round((upper_band - lower_band) / lower_band * 100, 2)),
        }

        if lower_band < current_price:
            band_analysis["if_buy_at_lower"] = {
                "current_pnl_pct": float(round((current_price - lower_band) / lower_band * 100, 2)),
                "pnl_at_upper": float(round((upper_band - lower_band) / lower_band * 100, 2)),
                "pnl_at_resistance": float(round((sr['nearest_resistance'] - lower_band) / lower_band * 100, 2)),
            }

        return {
            "symbol": symbol,
            "current_price": current_price,
            "current_pe": float(round(pe_ratio, 2)) if pe_ratio else None,
            "band_analysis": band_analysis,
            "support_resistance": {
                "nearest_support": sr['nearest_support'],
                "nearest_resistance": sr['nearest_resistance'],
            },
            "breakout_probability": float(round(breakout_prob, 1)),
        }

    except Exception as e:
        return {"error": str(e)}


def parse_value(value_str: str) -> float:
    """Parse value string like '20%' or '2000 Cr' to float"""
    if not value_str:
        return 0
    value_str = str(value_str).strip().replace(',', '')
    value_upper = value_str.upper()

    # Handle percentage
    if '%' in value_str:
        return float(value_str.replace('%', '')) / 100

    # Handle Cr (crore) - case insensitive
    if 'CR' in value_upper:
        num_part = re.sub(r'[^\d.]', '', value_str)
        return float(num_part) * 10000000 if num_part else 0

    # Handle L (lakh) - case insensitive
    if 'L' in value_upper and 'CR' not in value_upper:
        num_part = re.sub(r'[^\d.]', '', value_str)
        return float(num_part) * 100000 if num_part else 0

    try:
        return float(value_str)
    except:
        return 0


def apply_advanced_filter(stock: Dict, filter_name: str, filter_value: Any, hist: pd.DataFrame = None) -> bool:
    """Apply a single filter to a stock"""
    try:
        # Market cap filters
        if filter_name == "market_cap_min":
            return stock.get("market_cap", 0) >= filter_value
        if filter_name == "market_cap_max":
            return stock.get("market_cap", 0) <= filter_value

        # ROE/ROCE filters
        if filter_name == "roe_min":
            roe = stock.get("return_on_equity") or stock.get("roe")
            if roe == "N/A" or roe is None:
                return False
            roe_val = parse_value(str(roe)) if isinstance(roe, str) else roe
            return roe_val * 100 >= filter_value if roe_val < 1 else roe_val >= filter_value

        if filter_name == "roce_min":
            roce = stock.get("roce")
            if not roce or roce == "N/A":
                # Approximate ROCE using ROE if ROCE not available
                roe = stock.get("return_on_equity")
                if roe and roe != "N/A":
                    roe_val = parse_value(str(roe)) if isinstance(roe, str) else roe
                    roe_pct = roe_val * 100 if roe_val < 1 else roe_val
                    return roe_pct >= filter_value * 0.8  # Allow some margin
                return True  # Pass if no data
            roce_val = parse_value(str(roce))
            return roce_val >= filter_value if roce_val > 1 else roce_val * 100 >= filter_value

        # Debt to equity
        if filter_name == "debt_to_equity_max":
            dte = stock.get("debt_to_equity") or stock.get("debt_to_equity_screener")
            if dte == "N/A" or dte is None:
                return True  # Pass if no debt data
            dte_val = parse_value(str(dte)) if isinstance(dte, str) else dte
            return dte_val <= filter_value

        # Operating margin
        if filter_name == "operating_margin_min":
            opm = stock.get("operating_margins") or stock.get("operating_profit_margin")
            if opm == "N/A" or opm is None:
                return False
            opm_val = parse_value(str(opm)) if isinstance(opm, str) else opm
            return opm_val * 100 >= filter_value if opm_val < 1 else opm_val >= filter_value

        # Promoter holding
        if filter_name == "promoter_holding_min":
            ph = stock.get("promoter_holding") or stock.get("held_percent_insiders")
            if ph == "N/A" or ph is None:
                return False
            ph_val = parse_value(str(ph)) if isinstance(ph, str) else ph
            return ph_val >= filter_value if ph_val > 1 else ph_val * 100 >= filter_value

        if filter_name == "promoter_holding_max":
            ph = stock.get("promoter_holding") or stock.get("held_percent_insiders")
            if ph == "N/A" or ph is None:
                return True
            ph_val = parse_value(str(ph)) if isinstance(ph, str) else ph
            return ph_val <= filter_value if ph_val > 1 else ph_val * 100 <= filter_value

        # Promoter pledge (assume 0 if not available)
        if filter_name == "promoter_pledge_max":
            return True  # Most stocks pass this if data not available

        # PE filters
        if filter_name == "pe_max":
            pe = stock.get("pe_ratio")
            if pe == "N/A" or pe is None:
                return False
            return pe <= filter_value

        if filter_name == "pe_min":
            pe = stock.get("pe_ratio")
            if pe == "N/A" or pe is None:
                return False
            return pe >= filter_value

        # PEG ratio
        if filter_name == "peg_ratio_max":
            peg = stock.get("peg_ratio") or stock.get("peg_screener")
            if peg == "N/A" or peg is None:
                return False
            peg_val = parse_value(str(peg)) if isinstance(peg, str) else peg
            return peg_val <= filter_value and peg_val > 0

        # Volume filters
        if filter_name == "avg_volume_min":
            return stock.get("avg_volume", 0) >= filter_value

        # Growth filters (use earnings_growth as proxy)
        if "growth" in filter_name:
            eg = stock.get("earnings_growth") or stock.get("revenue_growth")
            if eg == "N/A" or eg is None:
                return False
            eg_val = parse_value(str(eg)) if isinstance(eg, str) else eg
            return eg_val * 100 >= filter_value / 2 if eg_val < 1 else eg_val >= filter_value / 2

        # Technical filters (need historical data)
        if filter_name == "price_above_200_dma" and hist is not None and not hist.empty:
            current_price = stock.get("current_price", 0)
            dma_200 = stock.get("200_day_avg", 0)
            return current_price > dma_200 if dma_200 else True

        if filter_name == "near_52_week_high":
            current = stock.get("current_price", 0)
            high_52 = stock.get("52_week_high", 0)
            if current and high_52:
                return (current / high_52) >= 0.9  # Within 10% of 52-week high
            return False

        # Free cash flow
        if filter_name == "free_cash_flow_positive":
            fcf = stock.get("free_cashflow", 0)
            return fcf > 0 if fcf else True

        # Operating cash flow > net profit
        if filter_name == "operating_cf_gt_profit":
            ocf = stock.get("operating_cashflow", 0)
            profit = stock.get("revenue", 0) * parse_value(str(stock.get("profit_margins", 0)))
            return ocf > profit if ocf and profit else True

        # Profit margin filter
        if filter_name == "profit_margin_min":
            pm = stock.get("profit_margins")
            if pm == "N/A" or pm is None:
                return True
            pm_val = parse_value(str(pm)) if isinstance(pm, str) else pm
            return pm_val * 100 >= filter_value if pm_val < 1 else pm_val >= filter_value

        # Price filters
        if filter_name == "price_min":
            return stock.get("current_price", 0) >= filter_value
        if filter_name == "price_max":
            return stock.get("current_price", 0) <= filter_value

        # Price to Book
        if filter_name == "price_to_book_max":
            pb = stock.get("price_to_book")
            if pb == "N/A" or pb is None:
                return True
            return float(pb) <= filter_value
        if filter_name == "price_to_book_min":
            pb = stock.get("price_to_book")
            if pb == "N/A" or pb is None:
                return True
            return float(pb) >= filter_value

        # EV/EBITDA
        if filter_name == "ev_to_ebitda_max":
            ev = stock.get("enterpriseToEbitda") or stock.get("ev_to_ebitda")
            if ev == "N/A" or ev is None:
                return True
            return float(ev) <= filter_value
        if filter_name == "ev_to_ebitda_min":
            ev = stock.get("enterpriseToEbitda") or stock.get("ev_to_ebitda")
            if ev == "N/A" or ev is None:
                return True
            return float(ev) >= filter_value

        # Free Cash Flow
        if filter_name == "free_cash_flow_min":
            fcf = stock.get("free_cashflow", 0)
            return fcf >= filter_value if fcf else True
        if filter_name == "free_cash_flow_max":
            fcf = stock.get("free_cashflow", 0)
            return fcf <= filter_value if fcf else True

        # EPS
        if filter_name == "eps_min":
            eps = stock.get("trailingEps") or stock.get("eps")
            if eps == "N/A" or eps is None:
                return True
            return float(eps) >= filter_value
        if filter_name == "eps_max":
            eps = stock.get("trailingEps") or stock.get("eps")
            if eps == "N/A" or eps is None:
                return True
            return float(eps) <= filter_value

        # Revenue/Earnings Growth
        if filter_name == "revenue_growth_min":
            rg = stock.get("revenue_growth") or stock.get("revenueGrowth")
            if rg == "N/A" or rg is None:
                return True
            rg_val = float(rg) * 100 if float(rg) < 1 else float(rg)
            return rg_val >= filter_value
        if filter_name == "earnings_growth_min":
            eg = stock.get("earnings_growth") or stock.get("earningsGrowth")
            if eg == "N/A" or eg is None:
                return True
            eg_val = float(eg) * 100 if float(eg) < 1 else float(eg)
            return eg_val >= filter_value

        # Dividend Yield
        if filter_name == "dividend_yield_min":
            dy = stock.get("dividendYield") or stock.get("dividend_yield")
            if dy == "N/A" or dy is None:
                return True
            dy_val = float(dy) * 100 if float(dy) < 1 else float(dy)
            return dy_val >= filter_value
        if filter_name == "dividend_yield_max":
            dy = stock.get("dividendYield") or stock.get("dividend_yield")
            if dy == "N/A" or dy is None:
                return True
            dy_val = float(dy) * 100 if float(dy) < 1 else float(dy)
            return dy_val <= filter_value

        # Price to Sales
        if filter_name == "price_to_sales_max":
            ps = stock.get("priceToSalesTrailing12Months") or stock.get("price_to_sales")
            if ps == "N/A" or ps is None:
                return True
            return float(ps) <= filter_value
        if filter_name == "price_to_sales_min":
            ps = stock.get("priceToSalesTrailing12Months") or stock.get("price_to_sales")
            if ps == "N/A" or ps is None:
                return True
            return float(ps) >= filter_value

        # Current Ratio
        if filter_name == "current_ratio_min":
            cr = stock.get("currentRatio") or stock.get("current_ratio")
            if cr == "N/A" or cr is None:
                return True
            return float(cr) >= filter_value

        # Near 52 week low
        if filter_name == "near_52_week_low":
            current = stock.get("current_price", 0)
            low_52 = stock.get("52_week_low", 0)
            if current and low_52:
                return (current / low_52) <= 1.1  # Within 10% of 52-week low
            return False

        # ROE max
        if filter_name == "roe_max":
            roe = stock.get("return_on_equity")
            if roe == "N/A" or roe is None:
                return True
            roe_val = float(roe) * 100 if float(roe) < 1 else float(roe)
            return roe_val <= filter_value

        # Debt to equity min
        if filter_name == "debt_to_equity_min":
            dte = stock.get("debt_to_equity")
            if dte == "N/A" or dte is None:
                return True
            return float(dte) >= filter_value

        # Operating margin max
        if filter_name == "operating_margin_max":
            opm = stock.get("operating_margins")
            if opm == "N/A" or opm is None:
                return True
            opm_val = float(opm) * 100 if float(opm) < 1 else float(opm)
            return opm_val <= filter_value

        # Default: pass the filter (for unknown filters)
        return True

    except Exception as e:
        print(f"Error applying filter {filter_name}: {e}")
        return True


# API Endpoints

@app.get("/")
async def root():
    return {"message": "Indian Stock Terminal API v2.0", "status": "running"}


@app.get("/api/indices")
async def get_indices():
    """Get all Indian and global indices"""
    result = {"indian": [], "global": [], "commodities": []}

    # Indian indices
    for name, symbol in INDICES.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")

            if not hist.empty:
                current = hist["Close"].iloc[-1]
                previous = hist["Close"].iloc[0] if len(hist) > 1 else current
                change = current - previous
                change_pct = (change / previous) * 100 if previous else 0

                result["indian"].append({
                    "name": name,
                    "symbol": symbol,
                    "price": round(current, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                })
        except:
            continue

    # Global indices
    for name, symbol in GLOBAL_INDICES.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")

            if not hist.empty:
                current = hist["Close"].iloc[-1]
                previous = hist["Close"].iloc[0] if len(hist) > 1 else current
                change = current - previous
                change_pct = (change / previous) * 100 if previous else 0

                result["global"].append({
                    "name": name,
                    "symbol": symbol,
                    "price": round(current, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                })
        except:
            continue

    # Commodities
    for name, symbol in COMMODITIES.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")

            if not hist.empty:
                current = hist["Close"].iloc[-1]
                previous = hist["Close"].iloc[0] if len(hist) > 1 else current
                change = current - previous
                change_pct = (change / previous) * 100 if previous else 0

                result["commodities"].append({
                    "name": name,
                    "symbol": symbol,
                    "price": round(current, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_pct, 2),
                })
        except:
            continue

    return result


@app.get("/api/stock/{symbol}")
async def get_stock(symbol: str):
    """Get comprehensive stock data"""
    fundamentals = get_stock_fundamentals(symbol)
    return fundamentals


@app.get("/api/stock/{symbol}/history")
async def get_stock_history_api(symbol: str, period: str = "1y"):
    """Get stock price history with indicators"""
    return get_stock_history(symbol, period)


@app.get("/api/stock/{symbol}/news")
async def get_stock_news(symbol: str, num: int = 10):
    """Get news for a stock"""
    return fetch_news_rss(f"{symbol} NSE stock India", num)


@app.get("/api/stock/{symbol}/strategies")
async def get_stock_strategies(symbol: str, strategy: str = None):
    """Run trading strategies on a stock"""
    return run_strategy_scan(symbol, strategy)


@app.get("/api/stock/{symbol}/backtest")
async def get_stock_backtest(symbol: str, strategy: str = "ma_crossover"):
    """Run backtest on a stock"""
    return run_backtest(symbol, strategy)


@app.get("/api/stock/{symbol}/backtest/{strategy_name}")
async def get_strategy_backtest(symbol: str, strategy_name: str):
    """Run detailed backtest for a specific strategy with timeseries"""
    return run_strategy_backtest(symbol, strategy_name)


@app.get("/api/news/market")
async def get_market_news(num: int = 20):
    """Get overall market news"""
    indian_news = fetch_news_rss("Indian stock market NSE BSE Nifty Sensex", num // 2)
    global_news = fetch_news_rss("global stock market S&P Dow Jones NASDAQ", num // 2)
    return {"indian": indian_news, "global": global_news}


@app.get("/api/stocks/universe")
async def get_stock_universe():
    """Get all available stocks organized by category"""
    return {
        "categories": {
            "Nifty 50": NIFTY_50,
            "Nifty Next 50": NIFTY_NEXT_50,
            "Nifty Midcap 100": NIFTY_MIDCAP_100,
            "Nifty Smallcap 100": NIFTY_SMALLCAP_100,
            "Additional Stocks": ADDITIONAL_STOCKS,
        },
        "total": len(ALL_STOCKS),
        "all_stocks": sorted(ALL_STOCKS),
    }


@app.get("/api/strategies/list")
async def get_strategies_list():
    """Get list of available trading strategies"""
    return {
        "strategies": [
            {"id": "ATH Breakout", "name": "ATH Breakout", "description": "200-Day Trend Filter + All-Time High Breakout"},
            {"id": "52-Week Momentum", "name": "52-Week Momentum", "description": "Near 52-week high with volume confirmation"},
            {"id": "VCP Pattern", "name": "VCP Pattern", "description": "Volatility Contraction Pattern (Mark Minervini)"},
            {"id": "Cup & Handle", "name": "Cup & Handle", "description": "Classic O'Neil Cup and Handle formation"},
            {"id": "Donchian Breakout", "name": "Donchian Breakout", "description": "Turtle Trading Donchian Channel breakout"},
            {"id": "MA Stack", "name": "MA Stack", "description": "Price > EMA 20 > EMA 50 > EMA 200 alignment"},
            {"id": "Relative Strength", "name": "Relative Strength", "description": "Outperforming index with momentum"},
            {"id": "Bollinger Squeeze", "name": "Bollinger Squeeze", "description": "Low volatility squeeze before expansion"},
            {"id": "Base Breakout", "name": "Base Breakout", "description": "Consolidation base breakout pattern"},
            {"id": "Stage Analysis", "name": "Stage Analysis", "description": "Weinstein Stage 2 accumulation"},
        ]
    }


@app.post("/api/scan/strategies")
async def scan_strategies(request: Dict[str, Any] = Body(...)):
    """Scan stocks with trading strategies"""
    symbols = request.get("symbols")
    category = request.get("category")
    scan_all = request.get("scan_all", False)
    strategy_name = request.get("strategy")

    if scan_all:
        stocks_to_scan = ALL_STOCKS
    elif category and category in STOCKS_BY_CATEGORY:
        stocks_to_scan = STOCKS_BY_CATEGORY[category]
    elif symbols:
        stocks_to_scan = symbols
    else:
        stocks_to_scan = NIFTY_50

    results = []

    # "all" means run all strategies, not a specific one
    actual_strategy = None if strategy_name == "all" else strategy_name

    def scan_stock(symbol):
        return run_strategy_scan(symbol, actual_strategy)

    # Run in parallel
    with ThreadPoolExecutor(max_workers=10) as exec:
        futures = [exec.submit(scan_stock, s) for s in stocks_to_scan[:100]]  # Limit to 100 for performance
        for future in futures:
            try:
                result = future.result(timeout=30)
                if "error" not in result and result.get("strategies"):
                    # If specific strategy, only include stocks that pass it
                    if actual_strategy:
                        strat_result = result.get("strategies", {}).get(actual_strategy)
                        if strat_result and strat_result.get("score", 0) >= 50:
                            results.append(result)
                    else:
                        # For "all" strategies, include stocks with avg_score >= 30 or any buy signal
                        avg = result.get("avg_score", 0)
                        buy_signals = result.get("buy_signals", 0)
                        if avg >= 30 or buy_signals >= 2:
                            results.append(result)
            except:
                continue

    # Sort by average score
    results.sort(key=lambda x: x.get("avg_score", 0), reverse=True)

    return {
        "total_scanned": len(stocks_to_scan),
        "results_count": len(results),
        "results": results,
    }


@app.get("/api/screener/templates")
async def get_screener_templates():
    """Get all screener templates"""
    return {
        "templates": [
            {"id": k, "name": v["name"], "description": v["description"]}
            for k, v in SCREENER_TEMPLATES.items()
        ]
    }


@app.post("/api/screener/advanced")
async def run_advanced_screener(request: Dict[str, Any] = Body(...)):
    """Run advanced stock screener with custom filters or template"""
    template_id = request.get("template")
    custom_filters = request.get("filters", {})
    category = request.get("category", "Nifty 50")
    custom_query = request.get("query", "")

    # Get filters from template or use custom
    if template_id and template_id in SCREENER_TEMPLATES:
        filters = SCREENER_TEMPLATES[template_id]["filters"]
    else:
        filters = custom_filters

    # Parse custom query if provided
    if custom_query:
        # Parse query like "Market Cap > 2000 Cr AND ROE > 20 AND ROCE > 20"
        parts = custom_query.upper().split(" AND ")
        for part in parts:
            part = part.strip()
            # Market Cap
            if "MARKET CAP" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["market_cap_min"] = parse_value(val)
            elif "MARKET CAP" in part and "<" in part:
                val = part.split("<")[1].strip()
                filters["market_cap_max"] = parse_value(val)
            # CMP (Current Market Price)
            elif "CMP" in part and ">" in part and "EBITDA" not in part and "BV" not in part:
                val = part.split(">")[1].strip()
                filters["price_min"] = float(val.replace("RS", "").replace(".", "").strip())
            elif "CMP" in part and "<" in part and "EBITDA" not in part and "BV" not in part:
                val = part.split("<")[1].strip()
                filters["price_max"] = float(val.replace("RS", "").replace(".", "").strip())
            # ROE
            elif "ROE" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["roe_min"] = float(val.replace("%", ""))
            elif "ROE" in part and "<" in part:
                val = part.split("<")[1].strip()
                filters["roe_max"] = float(val.replace("%", ""))
            # ROCE
            elif "ROCE" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["roce_min"] = float(val.replace("%", ""))
            elif "ROCE" in part and "<" in part:
                val = part.split("<")[1].strip()
                filters["roce_max"] = float(val.replace("%", ""))
            # Debt to Equity
            elif ("DEBT TO EQUITY" in part or "DEBT/EQUITY" in part or "D/E" in part) and "<" in part:
                val = part.split("<")[1].strip()
                de_val = float(val)
                filters["debt_to_equity_max"] = de_val * 100 if de_val < 1 else de_val
            elif ("DEBT TO EQUITY" in part or "DEBT/EQUITY" in part or "D/E" in part) and ">" in part:
                val = part.split(">")[1].strip()
                de_val = float(val)
                filters["debt_to_equity_min"] = de_val * 100 if de_val < 1 else de_val
            # Operating Margin / OPM
            elif ("OPERATING MARGIN" in part or "OPM" in part) and ">" in part:
                val = part.split(">")[1].strip()
                filters["operating_margin_min"] = float(val.replace("%", ""))
            elif ("OPERATING MARGIN" in part or "OPM" in part) and "<" in part:
                val = part.split("<")[1].strip()
                filters["operating_margin_max"] = float(val.replace("%", ""))
            # Profit Margin / NPM
            elif ("PROFIT MARGIN" in part or "NPM" in part) and ">" in part:
                val = part.split(">")[1].strip()
                filters["profit_margin_min"] = float(val.replace("%", ""))
            # PE Ratio
            elif ("P/E" in part or part.startswith("PE ")) and "<" in part:
                val = part.split("<")[1].strip()
                filters["pe_max"] = float(val)
            elif ("P/E" in part or part.startswith("PE ")) and ">" in part:
                val = part.split(">")[1].strip()
                filters["pe_min"] = float(val)
            # PEG Ratio
            elif "PEG" in part and "<" in part:
                val = part.split("<")[1].strip()
                filters["peg_ratio_max"] = float(val)
            elif "PEG" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["peg_ratio_min"] = float(val)
            # Price to Book / CMP/BV / P/B
            elif ("PRICE TO BOOK" in part or "P/B" in part or "CMP/BV" in part or "PB" in part) and "<" in part:
                val = part.split("<")[1].strip()
                filters["price_to_book_max"] = float(val)
            elif ("PRICE TO BOOK" in part or "P/B" in part or "CMP/BV" in part or "PB" in part) and ">" in part:
                val = part.split(">")[1].strip()
                filters["price_to_book_min"] = float(val)
            # EV/EBITDA
            elif ("EV/EBITDA" in part or "EV TO EBITDA" in part) and "<" in part:
                val = part.split("<")[1].strip()
                filters["ev_to_ebitda_max"] = float(val)
            elif ("EV/EBITDA" in part or "EV TO EBITDA" in part) and ">" in part:
                val = part.split(">")[1].strip()
                filters["ev_to_ebitda_min"] = float(val)
            # Free Cash Flow
            elif "FREE CASH FLOW" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["free_cash_flow_min"] = parse_value(val)
            elif "FREE CASH FLOW" in part and "<" in part:
                val = part.split("<")[1].strip()
                filters["free_cash_flow_max"] = parse_value(val)
            elif "FCF" in part and ">" in part:
                filters["free_cash_flow_positive"] = True
            # EPS
            elif "EPS" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["eps_min"] = float(val.replace("RS", "").strip())
            elif "EPS" in part and "<" in part:
                val = part.split("<")[1].strip()
                filters["eps_max"] = float(val.replace("RS", "").strip())
            # Revenue/Sales Growth
            elif ("SALES GROWTH" in part or "REVENUE GROWTH" in part) and ">" in part:
                val = part.split(">")[1].strip()
                filters["revenue_growth_min"] = float(val.replace("%", ""))
            # Earnings/Profit Growth
            elif ("EARNINGS GROWTH" in part or "PROFIT GROWTH" in part) and ">" in part:
                val = part.split(">")[1].strip()
                filters["earnings_growth_min"] = float(val.replace("%", ""))
            # Dividend Yield
            elif "DIVIDEND YIELD" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["dividend_yield_min"] = float(val.replace("%", ""))
            elif "DIVIDEND YIELD" in part and "<" in part:
                val = part.split("<")[1].strip()
                filters["dividend_yield_max"] = float(val.replace("%", ""))
            # Promoter Holding
            elif "PROMOTER HOLDING" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["promoter_holding_min"] = float(val.replace("%", ""))
            elif "PROMOTER HOLDING" in part and "<" in part:
                val = part.split("<")[1].strip()
                filters["promoter_holding_max"] = float(val.replace("%", ""))
            # Price to Sales / Market Cap to Sales
            elif ("PRICE TO SALES" in part or "P/S" in part or "MCAP/SALES" in part) and "<" in part:
                val = part.split("<")[1].strip()
                filters["price_to_sales_max"] = float(val)
            elif ("PRICE TO SALES" in part or "P/S" in part or "MCAP/SALES" in part) and ">" in part:
                val = part.split(">")[1].strip()
                filters["price_to_sales_min"] = float(val)
            # Current Ratio
            elif "CURRENT RATIO" in part and ">" in part:
                val = part.split(">")[1].strip()
                filters["current_ratio_min"] = float(val)
            # Technical filters
            elif "PRICE > 200 DMA" in part or "PRICE ABOVE 200" in part or "ABOVE 200 DMA" in part:
                filters["price_above_200_dma"] = True
            elif "52 WEEK HIGH" in part or "NEAR 52W HIGH" in part or "52W HIGH" in part:
                filters["near_52_week_high"] = True
            elif "52 WEEK LOW" in part or "NEAR 52W LOW" in part:
                filters["near_52_week_low"] = True

    # Get stocks to screen
    stocks_to_screen = STOCKS_BY_CATEGORY.get(category, NIFTY_50)
    if category == "All Stocks":
        stocks_to_screen = ALL_STOCKS

    # Limit based on category size
    max_stocks = 200 if category == "All Stocks" else 100
    results = []

    def screen_stock_fast(symbol):
        """Fast screening using only Yahoo Finance data"""
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info

            if not info or not info.get("currentPrice"):
                return None

            # Build basic fundamentals for filtering
            fundamentals = {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", "N/A"),
                "price_to_book": info.get("priceToBook", "N/A"),
                "return_on_equity": info.get("returnOnEquity", "N/A"),
                "debt_to_equity": info.get("debtToEquity", "N/A"),
                "operating_margins": info.get("operatingMargins", "N/A"),
                "profit_margins": info.get("profitMargins", "N/A"),
                "52_week_high": info.get("fiftyTwoWeekHigh", 0),
                "52_week_low": info.get("fiftyTwoWeekLow", 0),
                "50_day_avg": info.get("fiftyDayAverage", 0),
                "200_day_avg": info.get("twoHundredDayAverage", 0),
                "held_percent_insiders": info.get("heldPercentInsiders", "N/A"),
                "peg_ratio": info.get("pegRatio", "N/A"),
                "earnings_growth": info.get("earningsGrowth", "N/A"),
                "revenue_growth": info.get("revenueGrowth", "N/A"),
                "free_cashflow": info.get("freeCashflow", 0),
                "operating_cashflow": info.get("operatingCashflow", 0),
            }

            # Get historical data for technical filters if needed
            hist = None
            if any(f in filters for f in ["price_above_200_dma", "near_52_week_high", "volume_increasing"]):
                try:
                    hist = ticker.history(period="3mo")
                except:
                    pass

            # Apply all filters
            for filter_name, filter_value in filters.items():
                if not apply_advanced_filter(fundamentals, filter_name, filter_value, hist):
                    return None

            return fundamentals
        except Exception as e:
            return None

    # Run in parallel with more workers and shorter timeout
    with ThreadPoolExecutor(max_workers=25) as exec:
        futures = [exec.submit(screen_stock_fast, s) for s in stocks_to_screen[:max_stocks]]
        for future in futures:
            try:
                result = future.result(timeout=15)
                if result:
                    results.append(result)
            except:
                continue

    # Sort by market cap
    results.sort(key=lambda x: x.get("market_cap", 0), reverse=True)

    return {
        "count": len(results),
        "filters_applied": filters,
        "results": results,
    }


@app.post("/api/screener")
async def run_screener(filters: Dict[str, Any] = Body(...)):
    """Run stock screener with custom filters (legacy endpoint)"""
    results = []

    category = filters.get("category", "Nifty 50")
    stocks_to_screen = STOCKS_BY_CATEGORY.get(category, NIFTY_50)

    for symbol in stocks_to_screen[:50]:  # Limit for performance
        try:
            fundamentals = get_stock_fundamentals(symbol)

            # Apply filters
            passes = True

            if "min_market_cap" in filters:
                if fundamentals.get("market_cap", 0) < filters["min_market_cap"]:
                    passes = False

            if "min_pe" in filters:
                pe = fundamentals.get("pe_ratio")
                if pe != "N/A" and pe and pe < filters["min_pe"]:
                    passes = False

            if "max_pe" in filters:
                pe = fundamentals.get("pe_ratio")
                if pe != "N/A" and pe and pe > filters["max_pe"]:
                    passes = False

            if "min_roe" in filters:
                roe = fundamentals.get("return_on_equity")
                if roe == "N/A" or not roe or roe < filters["min_roe"]:
                    passes = False

            if passes:
                results.append(fundamentals)

        except Exception as e:
            continue

    return {"count": len(results), "results": results}


# ==================== WATCHLIST / PORTFOLIO API ====================

@app.post("/api/watchlist/analyze")
async def analyze_watchlist(request: Dict[str, Any] = Body(...)):
    """
    Analyze a watchlist/portfolio of holdings.
    Returns comprehensive data for all holdings including:
    - Current prices and P&L
    - News for each stock
    - Strategy signals
    - Aggregated portfolio metrics
    """
    holdings = request.get("holdings", [])

    if not holdings:
        return {"error": "No holdings provided"}

    results = []
    total_invested = 0
    total_current_value = 0
    all_news = []
    strategy_alerts = []

    strategies_instance = TradingStrategies()

    def analyze_holding(holding):
        """Analyze a single holding"""
        try:
            symbol = holding.get("symbol", "").upper().replace(".NS", "")
            qty = float(holding.get("quantity", 0))
            avg_price = float(holding.get("avg_price", 0))

            if not symbol:
                return None

            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info or {}
            hist = ticker.history(period="1y")

            if hist.empty:
                return None

            current_price = float(hist['Close'].iloc[-1])
            prev_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price

            # Calculate P&L
            invested_value = qty * avg_price
            current_value = qty * current_price
            pnl = current_value - invested_value
            pnl_pct = (pnl / invested_value * 100) if invested_value > 0 else 0
            day_change = current_price - prev_close
            day_change_pct = (day_change / prev_close * 100) if prev_close > 0 else 0

            # Get news
            news = []
            try:
                news_url = f"https://news.google.com/rss/search?q={symbol}+stock+india&hl=en-IN&gl=IN&ceid=IN:en"
                feed = feedparser.parse(news_url)
                for entry in feed.entries[:3]:
                    news.append({
                        "title": entry.get('title', ''),
                        "link": entry.get('link', ''),
                        "source": entry.get('source', {}).get('title', 'News'),
                        "published": entry.get('published', ''),
                    })
            except:
                pass

            # Run strategy analysis
            strategy_signals = []
            try:
                strategy_methods = [
                    ("ATH Breakout", strategies_instance.strategy_200dma_ath_breakout),
                    ("VCP Pattern", strategies_instance.strategy_vcp),
                    ("MA Stack", strategies_instance.strategy_ma_momentum_stack),
                ]

                for strat_name, strat_func in strategy_methods:
                    try:
                        result = strat_func(hist)
                        signal = result.signal.value if hasattr(result.signal, 'value') else str(result.signal)
                        if "BUY" in signal.upper():
                            strategy_signals.append({
                                "strategy": strat_name,
                                "signal": signal,
                                "score": result.score if hasattr(result, 'score') else 0
                            })
                    except:
                        pass
            except:
                pass

            # Support/Resistance
            sr = calculate_support_resistance(hist)

            return {
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", symbol)),
                "sector": info.get("sector", "N/A"),
                "quantity": qty,
                "avg_price": round(avg_price, 2),
                "current_price": round(current_price, 2),
                "invested_value": round(invested_value, 2),
                "current_value": round(current_value, 2),
                "pnl": round(pnl, 2),
                "pnl_pct": round(pnl_pct, 2),
                "day_change": round(day_change, 2),
                "day_change_pct": round(day_change_pct, 2),
                "pe_ratio": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "support": sr.get("nearest_support"),
                "resistance": sr.get("nearest_resistance"),
                "news": news,
                "strategy_signals": strategy_signals,
            }
        except Exception as e:
            print(f"Error analyzing {holding}: {e}")
            return None

    # Analyze all holdings in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(analyze_holding, h) for h in holdings]
        for future in futures:
            try:
                result = future.result(timeout=30)
                if result:
                    results.append(result)
                    total_invested += result["invested_value"]
                    total_current_value += result["current_value"]
                    all_news.extend(result["news"])

                    # Collect strategy alerts
                    for sig in result.get("strategy_signals", []):
                        strategy_alerts.append({
                            "symbol": result["symbol"],
                            "strategy": sig["strategy"],
                            "signal": sig["signal"],
                        })
            except:
                continue

    # Sort news by recency (if we have published dates)
    all_news = all_news[:20]  # Limit to 20 most recent

    # Portfolio summary
    total_pnl = total_current_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0

    # Sort results by current value (largest holdings first)
    results.sort(key=lambda x: x["current_value"], reverse=True)

    return {
        "portfolio_summary": {
            "total_invested": round(total_invested, 2),
            "current_value": round(total_current_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "holdings_count": len(results),
        },
        "holdings": results,
        "news": all_news,
        "strategy_alerts": strategy_alerts,
    }


@app.get("/api/watchlist/quick/{symbols}")
async def quick_watchlist(symbols: str):
    """
    Quick watchlist view - just pass comma-separated symbols.
    Example: /api/watchlist/quick/RELIANCE,TCS,INFY
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]

    results = []

    def get_quick_data(symbol):
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            hist = ticker.history(period="5d")
            info = ticker.info or {}

            if hist.empty:
                return None

            current = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
            change = current - prev
            change_pct = (change / prev * 100) if prev > 0 else 0

            return {
                "symbol": symbol,
                "name": info.get("shortName", symbol),
                "price": round(current, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "pe": info.get("trailingPE"),
                "market_cap": info.get("marketCap"),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
            }
        except:
            return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_quick_data, s) for s in symbol_list]
        for future in futures:
            try:
                result = future.result(timeout=15)
                if result:
                    results.append(result)
            except:
                continue

    return {"count": len(results), "stocks": results}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
