#!/usr/bin/env python3
"""
Indian Stock Market Terminal - Complete Web Application
========================================================
Bloomberg-style terminal for Indian markets with:
- Market Overview Landing Page
- All Indices (Indian + Global)
- Commodities
- News & Sentiment
- Stock Screener
- Trading Strategies
- Full Stock Analysis

Run with: streamlit run app.py
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import yfinance as yf

from data_fetcher import IndianStockDataFetcher
from technical_analysis import TechnicalAnalysis
from stock_screener import StockScreener, EXTENDED_UNIVERSE
from strategies_page import render_strategies_page
from stock_universe import (
    NIFTY_50, NIFTY_100, NIFTY_200, ALL_STOCKS,
    COMMODITIES, GLOBAL_INDICES, STOCKS_BY_CATEGORY, get_all_stocks_sorted
)
from news_sentiment import NewsSentimentAnalyzer, Sentiment

# Page configuration
st.set_page_config(
    page_title="Indian Stock Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    [data-testid="stSidebar"] { background-color: #1a1a2e; }

    .market-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 5px 0;
        border: 1px solid #2a2a4a;
    }

    .index-up { color: #00ff88 !important; }
    .index-down { color: #ff4757 !important; }

    .news-card {
        background: #1a1a2e;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
        border-left: 3px solid #667eea;
    }

    .commodity-card {
        background: linear-gradient(135deg, #2d1b4e 0%, #1a1a2e 100%);
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }

    .section-title {
        color: #ffffff;
        font-size: 1.3em;
        font-weight: 600;
        margin: 20px 0 10px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid #667eea;
    }

    .metric-box {
        background: #1e1e2e;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'fetcher' not in st.session_state:
    st.session_state.fetcher = IndianStockDataFetcher(exchange="NSE")

if 'news_analyzer' not in st.session_state:
    st.session_state.news_analyzer = NewsSentimentAnalyzer()

if 'screener' not in st.session_state:
    st.session_state.screener = StockScreener()
    st.session_state.screener.set_universe(EXTENDED_UNIVERSE)

if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = "RELIANCE"

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]


def get_commodity_data(symbol: str) -> Dict:
    """Fetch commodity data."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if hist.empty:
            return {"error": "No data"}

        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev) * 100 if prev else 0

        return {
            "price": current,
            "change": change,
            "change_pct": change_pct
        }
    except Exception as e:
        return {"error": str(e)}


def get_global_index_data(symbol: str) -> Dict:
    """Fetch global index data."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        if hist.empty:
            return {"error": "No data"}

        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2] if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev) * 100 if prev else 0

        return {
            "price": current,
            "change": change,
            "change_pct": change_pct
        }
    except Exception as e:
        return {"error": str(e)}


def render_sidebar():
    """Render the sidebar with navigation and search."""
    with st.sidebar:
        st.markdown("## 🇮🇳 Indian Stock Terminal")
        st.markdown("---")

        # Navigation
        st.markdown("### 📍 Navigation")
        page = st.radio(
            "Select Page:",
            ["🏠 Market Overview", "📈 Stock Analysis", "🔍 Stock Screener", "🎯 Trading Strategies"],
            label_visibility="collapsed"
        )
        st.session_state.page = page

        st.markdown("---")

        # Quick Search - All 300+ stocks
        st.markdown("### 🔍 Quick Search")

        # Get all stocks sorted
        all_stocks_sorted = get_all_stocks_sorted()

        # Add search functionality
        search_text = st.text_input("Search symbol:", placeholder="Type to search...")

        if search_text:
            # Filter stocks based on search
            filtered = [s for s in all_stocks_sorted if search_text.upper() in s]
            if filtered:
                selected = st.selectbox("Results:", filtered[:50], key="search_results")
                if st.button("Go →", key="go_search"):
                    st.session_state.selected_stock = selected
                    st.session_state.page = "📈 Stock Analysis"
                    st.rerun()
        else:
            # Show dropdown with all stocks organized
            category = st.selectbox("Category:", list(STOCKS_BY_CATEGORY.keys()))
            stocks_list = STOCKS_BY_CATEGORY[category]

            selected = st.selectbox(
                f"Select Stock ({len(stocks_list)} stocks):",
                stocks_list,
                index=0
            )

            if st.button("Go to Stock →", use_container_width=True):
                st.session_state.selected_stock = selected
                st.session_state.page = "📈 Stock Analysis"
                st.rerun()

        st.markdown("---")

        # Watchlist
        st.markdown("### ⭐ Watchlist")
        for stock in st.session_state.watchlist[:5]:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(stock, key=f"wl_{stock}", use_container_width=True):
                    st.session_state.selected_stock = stock
                    st.session_state.page = "📈 Stock Analysis"
                    st.rerun()
            with col2:
                if st.button("✕", key=f"rm_{stock}"):
                    st.session_state.watchlist.remove(stock)
                    st.rerun()

        st.markdown("---")

        # Quick Market Summary
        st.markdown("### 📊 Market")
        for idx in ["NIFTY50", "SENSEX"]:
            data = st.session_state.fetcher.get_index_data(idx)
            if "error" not in data:
                color = "🟢" if data['change'] >= 0 else "🔴"
                st.markdown(f"{color} **{idx}**: {data['current_price']:,.0f} ({data['change_percent']:+.2f}%)")


def render_market_overview():
    """Render the Market Overview landing page."""

    st.markdown("# 🏠 Market Overview")
    st.markdown(f"*Last Updated: {datetime.now().strftime('%d %b %Y %I:%M %p IST')}*")

    # Top row - Indian Indices
    st.markdown('<div class="section-title">🇮🇳 Indian Market Indices</div>', unsafe_allow_html=True)

    indian_indices = {
        "NIFTY 50": "NIFTY50",
        "SENSEX": "SENSEX",
        "BANK NIFTY": "BANKNIFTY",
        "NIFTY IT": "NIFTYIT",
        "NIFTY PHARMA": "NIFTYPHARMA",
        "NIFTY AUTO": "NIFTYAUTO",
        "NIFTY FMCG": "NIFTYFMCG",
        "NIFTY METAL": "NIFTYMETAL",
    }

    cols = st.columns(4)
    for i, (name, symbol) in enumerate(indian_indices.items()):
        with cols[i % 4]:
            data = st.session_state.fetcher.get_index_data(symbol)
            if "error" not in data:
                color = "#00ff88" if data['change'] >= 0 else "#ff4757"
                arrow = "▲" if data['change'] >= 0 else "▼"
                st.markdown(f"""
                <div class="market-card">
                    <p style="color: #888; margin: 0; font-size: 0.85em;">{name}</p>
                    <h3 style="color: white; margin: 5px 0;">{data['current_price']:,.2f}</h3>
                    <p style="color: {color}; margin: 0;">{arrow} {data['change_percent']:+.2f}%</p>
                </div>
                """, unsafe_allow_html=True)

    # More Indian Indices
    st.markdown("")
    cols2 = st.columns(4)
    more_indices = {
        "NIFTY MIDCAP 50": "NIFTYMIDCAP50",
        "NIFTY SMALLCAP": "NIFTYSMALLCAP50",
        "NIFTY ENERGY": "NIFTYENERGY",
        "INDIA VIX": "INDIAVIX",
    }

    for i, (name, symbol) in enumerate(more_indices.items()):
        with cols2[i % 4]:
            data = st.session_state.fetcher.get_index_data(symbol)
            if "error" not in data:
                # VIX up is bearish
                if symbol == "INDIAVIX":
                    color = "#ff4757" if data['change'] >= 0 else "#00ff88"
                else:
                    color = "#00ff88" if data['change'] >= 0 else "#ff4757"
                arrow = "▲" if data['change'] >= 0 else "▼"
                st.markdown(f"""
                <div class="market-card">
                    <p style="color: #888; margin: 0; font-size: 0.85em;">{name}</p>
                    <h3 style="color: white; margin: 5px 0;">{data['current_price']:,.2f}</h3>
                    <p style="color: {color}; margin: 0;">{arrow} {data['change_percent']:+.2f}%</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Two column layout - Global Indices + Commodities
    col_global, col_commodities = st.columns(2)

    with col_global:
        st.markdown('<div class="section-title">🌍 Global Indices</div>', unsafe_allow_html=True)

        global_display = {
            "🇺🇸 DOW JONES": "^DJI",
            "🇺🇸 S&P 500": "^GSPC",
            "🇺🇸 NASDAQ": "^IXIC",
            "🇬🇧 FTSE 100": "^FTSE",
            "🇩🇪 DAX": "^GDAXI",
            "🇯🇵 NIKKEI 225": "^N225",
            "🇭🇰 HANG SENG": "^HSI",
            "🇨🇳 SHANGHAI": "000001.SS",
        }

        for name, symbol in global_display.items():
            data = get_global_index_data(symbol)
            if "error" not in data:
                color = "#00ff88" if data['change'] >= 0 else "#ff4757"
                arrow = "▲" if data['change'] >= 0 else "▼"
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #2a2a4a;">
                    <span style="color: #ddd;">{name}</span>
                    <span style="color: {color};">{data['price']:,.2f} {arrow} {data['change_pct']:+.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

    with col_commodities:
        st.markdown('<div class="section-title">🥇 Commodities</div>', unsafe_allow_html=True)

        commodity_display = {
            "🥇 GOLD": "GC=F",
            "🥈 SILVER": "SI=F",
            "🛢️ CRUDE OIL": "CL=F",
            "⛽ NATURAL GAS": "NG=F",
            "🔶 COPPER": "HG=F",
        }

        for name, symbol in commodity_display.items():
            data = get_commodity_data(symbol)
            if "error" not in data:
                color = "#00ff88" if data['change'] >= 0 else "#ff4757"
                arrow = "▲" if data['change'] >= 0 else "▼"
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #2a2a4a;">
                    <span style="color: #ddd;">{name}</span>
                    <span style="color: {color};">${data['price']:,.2f} {arrow} {data['change_pct']:+.2f}%</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # News Section
    col_local, col_global_news = st.columns(2)

    with col_local:
        st.markdown('<div class="section-title">📰 Indian Market News</div>', unsafe_allow_html=True)

        news_analyzer = st.session_state.news_analyzer

        # Get Indian market news
        if 'indian_news_cache' not in st.session_state:
            with st.spinner("Loading news..."):
                st.session_state.indian_news_cache = news_analyzer.get_market_news(num_results=6)

        news_items = st.session_state.indian_news_cache

        if news_items:
            # Overall sentiment
            overall = news_analyzer.get_overall_sentiment(news_items)
            sentiment_map = {
                Sentiment.VERY_POSITIVE: ("🚀 Very Bullish", "#00ff88"),
                Sentiment.POSITIVE: ("📈 Bullish", "#00cc66"),
                Sentiment.NEUTRAL: ("➖ Neutral", "#888888"),
                Sentiment.NEGATIVE: ("📉 Bearish", "#ff6b6b"),
                Sentiment.VERY_NEGATIVE: ("⚠️ Very Bearish", "#ff4757"),
            }
            label, color = sentiment_map.get(overall, ("➖ Neutral", "#888888"))

            st.markdown(f"""
            <div style="background: {color}20; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
                <span style="color: {color}; font-weight: bold;">Market Sentiment: {label}</span>
            </div>
            """, unsafe_allow_html=True)

            for news in news_items[:5]:
                emoji = "🟢" if news.sentiment in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE] else "🔴" if news.sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE] else "🟡"
                st.markdown(f"""
                <div class="news-card">
                    {emoji} {news.title[:100]}{'...' if len(news.title) > 100 else ''}
                    <br><small style="color: #666;">{news.source}</small>
                </div>
                """, unsafe_allow_html=True)

        if st.button("🔄 Refresh Indian News"):
            st.session_state.indian_news_cache = news_analyzer.get_market_news(num_results=6)
            st.rerun()

    with col_global_news:
        st.markdown('<div class="section-title">🌐 Global Market News</div>', unsafe_allow_html=True)

        # Get global market news
        if 'global_news_cache' not in st.session_state:
            with st.spinner("Loading global news..."):
                st.session_state.global_news_cache = news_analyzer.get_google_news("global stock market news", 6)

        global_news = st.session_state.global_news_cache

        if global_news:
            overall = news_analyzer.get_overall_sentiment(global_news)
            sentiment_map = {
                Sentiment.VERY_POSITIVE: ("🚀 Very Bullish", "#00ff88"),
                Sentiment.POSITIVE: ("📈 Bullish", "#00cc66"),
                Sentiment.NEUTRAL: ("➖ Neutral", "#888888"),
                Sentiment.NEGATIVE: ("📉 Bearish", "#ff6b6b"),
                Sentiment.VERY_NEGATIVE: ("⚠️ Very Bearish", "#ff4757"),
            }
            label, color = sentiment_map.get(overall, ("➖ Neutral", "#888888"))

            st.markdown(f"""
            <div style="background: {color}20; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
                <span style="color: {color}; font-weight: bold;">Global Sentiment: {label}</span>
            </div>
            """, unsafe_allow_html=True)

            for news in global_news[:5]:
                emoji = "🟢" if news.sentiment in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE] else "🔴" if news.sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE] else "🟡"
                st.markdown(f"""
                <div class="news-card">
                    {emoji} {news.title[:100]}{'...' if len(news.title) > 100 else ''}
                    <br><small style="color: #666;">{news.source}</small>
                </div>
                """, unsafe_allow_html=True)

        if st.button("🔄 Refresh Global News"):
            st.session_state.global_news_cache = news_analyzer.get_google_news("global stock market news", 6)
            st.rerun()

    st.markdown("---")

    # Market Insights
    st.markdown('<div class="section-title">💡 Market Insights</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        nifty_data = st.session_state.fetcher.get_index_data("NIFTY50")
        if "error" not in nifty_data:
            trend = "Bullish" if nifty_data['change'] > 0 else "Bearish"
            st.markdown(f"""
            <div class="metric-box">
                <h4 style="color: #667eea;">Nifty Trend</h4>
                <h2 style="color: {'#00ff88' if trend == 'Bullish' else '#ff4757'};">{trend}</h2>
                <p style="color: #888;">Based on today's movement</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        vix_data = st.session_state.fetcher.get_index_data("INDIAVIX")
        if "error" not in vix_data:
            vix_level = "Low" if vix_data['current_price'] < 15 else "Moderate" if vix_data['current_price'] < 20 else "High"
            color = "#00ff88" if vix_level == "Low" else "#ffa502" if vix_level == "Moderate" else "#ff4757"
            st.markdown(f"""
            <div class="metric-box">
                <h4 style="color: #667eea;">Volatility (VIX)</h4>
                <h2 style="color: {color};">{vix_level}</h2>
                <p style="color: #888;">VIX: {vix_data['current_price']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)

    with col3:
        bank_data = st.session_state.fetcher.get_index_data("BANKNIFTY")
        if "error" not in bank_data:
            bank_trend = "Strong" if bank_data['change_percent'] > 0.5 else "Weak" if bank_data['change_percent'] < -0.5 else "Neutral"
            color = "#00ff88" if bank_trend == "Strong" else "#ff4757" if bank_trend == "Weak" else "#888888"
            st.markdown(f"""
            <div class="metric-box">
                <h4 style="color: #667eea;">Banking Sector</h4>
                <h2 style="color: {color};">{bank_trend}</h2>
                <p style="color: #888;">{bank_data['change_percent']:+.2f}% today</p>
            </div>
            """, unsafe_allow_html=True)


def render_stock_analysis_page():
    """Render comprehensive stock analysis page."""

    symbol = st.session_state.selected_stock
    fetcher = st.session_state.fetcher

    with st.spinner(f"Loading {symbol}..."):
        price_data = fetcher.get_realtime_price(symbol)
        fundamentals = fetcher.get_fundamentals(symbol)

    if "error" in price_data:
        st.error(f"Error loading {symbol}: {price_data.get('error')}")
        return

    # Header
    company_name = fundamentals.get('company_name', symbol)
    sector = fundamentals.get('sector', 'N/A')
    industry = fundamentals.get('industry', 'N/A')

    current_price = price_data.get('current_price', 0)
    change = price_data.get('change', 0)
    change_pct = price_data.get('change_percent', 0)

    color = "#00ff88" if change >= 0 else "#ff4757"
    arrow = "▲" if change >= 0 else "▼"

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); padding: 25px; border-radius: 15px;">
            <h1 style="color: white; margin: 0;">{company_name}</h1>
            <p style="color: #888; margin: 5px 0;">
                🏢 {sector} | 🏭 {industry} | 📊 NSE: {symbol}
            </p>
            <div style="margin-top: 15px;">
                <span style="font-size: 2.5em; font-weight: bold; color: {color};">₹{current_price:,.2f}</span>
                <span style="font-size: 1.2em; color: {color}; margin-left: 15px;">
                    {arrow} ₹{abs(change):,.2f} ({change_pct:+.2f}%)
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("⭐ Add to Watchlist", use_container_width=True):
            if symbol not in st.session_state.watchlist:
                st.session_state.watchlist.append(symbol)
                st.success(f"Added {symbol}!")

    st.markdown("---")

    # Key Metrics
    st.markdown("### 📊 Key Metrics")

    val = fundamentals.get('valuation', {})
    prof = fundamentals.get('profitability', {})
    health = fundamentals.get('financial_health', {})
    div = fundamentals.get('dividends', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Market Cap", val.get('market_cap_formatted', 'N/A'))
        st.metric("P/E Ratio", val.get('pe_ratio', 'N/A'))
        st.metric("P/B Ratio", val.get('price_to_book', 'N/A'))
        st.metric("EV/EBITDA", val.get('ev_to_ebitda', 'N/A'))

    with col2:
        st.metric("ROE", prof.get('return_on_equity', 'N/A'))
        st.metric("ROA", prof.get('return_on_assets', 'N/A'))
        st.metric("Profit Margin", prof.get('profit_margin', 'N/A'))
        st.metric("Operating Margin", prof.get('operating_margin', 'N/A'))

    with col3:
        st.metric("Debt/Equity", health.get('debt_to_equity', 'N/A'))
        st.metric("Current Ratio", health.get('current_ratio', 'N/A'))
        st.metric("Quick Ratio", health.get('quick_ratio', 'N/A'))
        st.metric("Total Cash", health.get('total_cash', 'N/A'))

    with col4:
        st.metric("52W High", f"₹{price_data.get('fifty_two_week_high', 0):,.2f}")
        st.metric("52W Low", f"₹{price_data.get('fifty_two_week_low', 0):,.2f}")
        st.metric("Div Yield", div.get('dividend_yield', 'N/A'))
        st.metric("Volume", f"{price_data.get('volume', 0):,}")

    st.markdown("---")

    # Pros and Cons
    render_pros_cons(fundamentals)

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Chart",
        "📊 Financials",
        "🏢 Shareholding",
        "📋 Peer Comparison",
        "📰 News"
    ])

    with tab1:
        render_chart(symbol)

    with tab2:
        render_financials(symbol)

    with tab3:
        render_shareholding(symbol, fundamentals)

    with tab4:
        render_peer_comparison(symbol, fundamentals)

    with tab5:
        render_stock_news(symbol)


def render_pros_cons(fundamentals: Dict):
    """Render pros and cons analysis."""

    st.markdown("### ✅ Pros & Cons")

    val = fundamentals.get('valuation', {})
    prof = fundamentals.get('profitability', {})
    health = fundamentals.get('financial_health', {})

    pros = []
    cons = []

    # Analyze
    de = health.get('debt_to_equity', None)
    if de is not None and de < 0.5:
        pros.append("Company is almost debt free")
    elif de is not None and de > 2:
        cons.append("Company has high debt levels")

    roe_str = prof.get('return_on_equity', 'N/A')
    if roe_str and roe_str != 'N/A':
        try:
            roe = float(str(roe_str).replace('%', '').split('-')[0])
            if roe > 20:
                pros.append(f"High ROE of {roe:.1f}%")
            elif roe < 10:
                cons.append(f"Low ROE of {roe:.1f}%")
        except:
            pass

    pe = val.get('pe_ratio', None)
    if pe and pe < 15:
        pros.append("Stock trading at attractive valuation")
    elif pe and pe > 50:
        cons.append("Stock trading at expensive valuation")

    cr = health.get('current_ratio', None)
    if cr and cr > 2:
        pros.append("Strong liquidity position")
    elif cr and cr < 1:
        cons.append("Weak liquidity position")

    opm_str = prof.get('operating_margin', 'N/A')
    if opm_str and opm_str != 'N/A':
        try:
            opm = float(str(opm_str).replace('%', '').split('-')[0])
            if opm > 20:
                pros.append(f"Strong operating margins of {opm:.1f}%")
        except:
            pass

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: #1a2e1a; padding: 15px; border-radius: 8px; border-left: 4px solid #00ff88;">
            <h4 style="color: #00ff88; margin: 0 0 10px 0;">PROS</h4>
        """, unsafe_allow_html=True)
        for pro in pros[:5] if pros else ["No significant pros identified"]:
            st.markdown(f"• {pro}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: #2e1a1a; padding: 15px; border-radius: 8px; border-left: 4px solid #ff4757;">
            <h4 style="color: #ff4757; margin: 0 0 10px 0;">CONS</h4>
        """, unsafe_allow_html=True)
        for con in cons[:5] if cons else ["No significant cons identified"]:
            st.markdown(f"• {con}")
        st.markdown("</div>", unsafe_allow_html=True)


def render_chart(symbol: str):
    """Render interactive chart."""

    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)

    df = st.session_state.fetcher.get_historical_data(symbol, period=period)

    if df.empty:
        st.error("No chart data available")
        return

    df = TechnicalAnalysis.add_all_indicators(df)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        show_ema20 = st.checkbox("EMA 20", value=True)
    with col2:
        show_ema50 = st.checkbox("EMA 50", value=True)
    with col3:
        show_ema200 = st.checkbox("EMA 200", value=True)
    with col4:
        show_volume = st.checkbox("Volume", value=True)

    rows = 2 if show_volume else 1
    row_heights = [0.7, 0.3] if show_volume else [1]

    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=row_heights)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='Price',
        increasing_line_color='#26a69a', decreasing_line_color='#ef5350'
    ), row=1, col=1)

    if show_ema20 and 'EMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], name='EMA 20',
                                 line=dict(color='#f7931a', width=1.5)), row=1, col=1)
    if show_ema50 and 'EMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], name='EMA 50',
                                 line=dict(color='#2962ff', width=1.5)), row=1, col=1)
    if show_ema200 and 'EMA_200' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], name='EMA 200',
                                 line=dict(color='#9c27b0', width=2)), row=1, col=1)

    if show_volume:
        colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['Close'], df['Open'])]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

    # ATH/ATL lines
    ath_atl = TechnicalAnalysis.find_all_time_high_low(df)
    fig.add_hline(y=ath_atl['ath']['price'], line_dash="dot", line_color="#ffd700",
                  annotation_text=f"ATH: ₹{ath_atl['ath']['price']:,.0f}", row=1, col=1)
    fig.add_hline(y=ath_atl['atl']['price'], line_dash="dot", line_color="#ff6b6b",
                  annotation_text=f"ATL: ₹{ath_atl['atl']['price']:,.0f}", row=1, col=1)

    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # RSI Chart
    if 'RSI' in df.columns:
        st.markdown("#### RSI (14)")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI',
                                      line=dict(color='#7c4dff', width=2)))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="#ef5350")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="#26a69a")
        fig_rsi.update_layout(height=200, yaxis_range=[0, 100], template='plotly_dark')
        st.plotly_chart(fig_rsi, use_container_width=True)


def render_financials(symbol: str):
    """Render financial statements."""

    statements = st.session_state.fetcher.get_financial_statements(symbol)

    tab1, tab2, tab3 = st.tabs(["📊 Quarterly Results", "💰 Profit & Loss", "📋 Balance Sheet"])

    with tab1:
        st.markdown("#### Quarterly Results")
        if statements['quarterly_income'] is not None and not statements['quarterly_income'].empty:
            st.dataframe(statements['quarterly_income'].T.head(8), use_container_width=True)
        else:
            st.info("Quarterly data not available")

    with tab2:
        st.markdown("#### Annual Profit & Loss")
        if statements['income_statement'] is not None and not statements['income_statement'].empty:
            st.dataframe(statements['income_statement'].T, use_container_width=True)
        else:
            st.info("P&L data not available")

    with tab3:
        st.markdown("#### Balance Sheet")
        if statements['balance_sheet'] is not None and not statements['balance_sheet'].empty:
            st.dataframe(statements['balance_sheet'].T, use_container_width=True)
        else:
            st.info("Balance sheet not available")


def render_shareholding(symbol: str, fundamentals: Dict):
    """Render shareholding pattern."""

    st.markdown("#### Shareholding Pattern")

    shares = fundamentals.get('shares', {})

    insider = shares.get('insider_ownership', '0%')
    institutional = shares.get('institutional_ownership', '0%')

    try:
        insider_pct = float(str(insider).replace('%', '').split('-')[0]) if insider != 'N/A' else 0
        inst_pct = float(str(institutional).replace('%', '').split('-')[0]) if institutional != 'N/A' else 0
        public_pct = max(0, 100 - insider_pct - inst_pct)
    except:
        insider_pct, inst_pct, public_pct = 40, 30, 30

    col1, col2 = st.columns([1, 2])

    with col1:
        fig = go.Figure(data=[go.Pie(
            labels=['Promoters', 'FIIs/DIIs', 'Public'],
            values=[insider_pct, inst_pct, public_pct],
            hole=0.5,
            marker_colors=['#667eea', '#00ff88', '#ffa502'],
        )])
        fig.update_layout(height=300, template='plotly_dark', showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### Ownership Breakdown")
        data = {
            'Category': ['Promoters', 'FIIs/DIIs', 'Public', 'Total'],
            'Holding (%)': [f"{insider_pct:.2f}%", f"{inst_pct:.2f}%", f"{public_pct:.2f}%", "100.00%"]
        }
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def render_peer_comparison(symbol: str, fundamentals: Dict):
    """Render peer comparison."""

    st.markdown("#### Peer Comparison")

    sector_peers = {
        "Technology": ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM"],
        "Financial Services": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
        "Energy": ["RELIANCE", "ONGC", "BPCL", "NTPC", "POWERGRID"],
        "Consumer Goods": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "TATACONSUM"],
        "Automobile": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "HEROMOTOCO"],
        "Pharmaceuticals": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN"],
    }

    sector = fundamentals.get('sector', 'Technology')

    peers = []
    for sec, stocks in sector_peers.items():
        if symbol in stocks or sec in sector:
            peers = stocks[:6]
            break

    if not peers:
        peers = ["TCS", "INFY", "WIPRO", "HCLTECH", "RELIANCE"]

    peer_data = []
    for peer in peers:
        try:
            price = st.session_state.fetcher.get_realtime_price(peer)
            fund = st.session_state.fetcher.get_fundamentals(peer)

            if "error" not in price and "error" not in fund:
                peer_data.append({
                    'Name': fund.get('company_name', peer)[:20],
                    'CMP (₹)': f"{price.get('current_price', 0):,.2f}",
                    'P/E': fund.get('valuation', {}).get('pe_ratio', 'N/A'),
                    'M.Cap': fund.get('valuation', {}).get('market_cap_formatted', 'N/A'),
                    'ROE': fund.get('profitability', {}).get('return_on_equity', 'N/A'),
                    'D/E': fund.get('financial_health', {}).get('debt_to_equity', 'N/A'),
                })
        except:
            continue

    if peer_data:
        st.dataframe(pd.DataFrame(peer_data), use_container_width=True, hide_index=True)
    else:
        st.info("Peer data not available")


def render_stock_news(symbol: str):
    """Render stock-specific news."""

    st.markdown("#### Latest News")

    news_analyzer = st.session_state.news_analyzer

    with st.spinner("Fetching news..."):
        news_items = news_analyzer.get_stock_news(symbol, num_results=8)

    if news_items:
        overall = news_analyzer.get_overall_sentiment(news_items)
        sentiment_map = {
            Sentiment.VERY_POSITIVE: ("🚀 Very Bullish", "#00ff88"),
            Sentiment.POSITIVE: ("📈 Bullish", "#00cc66"),
            Sentiment.NEUTRAL: ("➖ Neutral", "#888888"),
            Sentiment.NEGATIVE: ("📉 Bearish", "#ff6b6b"),
            Sentiment.VERY_NEGATIVE: ("⚠️ Very Bearish", "#ff4757"),
        }
        label, color = sentiment_map.get(overall, ("➖ Neutral", "#888888"))

        st.markdown(f"""
        <div style="background: {color}20; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 15px;">
            <span style="color: {color}; font-weight: bold;">News Sentiment: {label}</span>
        </div>
        """, unsafe_allow_html=True)

        for news in news_items:
            emoji = "🟢" if news.sentiment in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE] else "🔴" if news.sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE] else "🟡"
            st.markdown(f"""
            <div class="news-card">
                <b>{emoji} {news.title}</b>
                <br><small style="color: #666;">{news.source} | Score: {news.sentiment_score:+.2f}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No recent news found")


def render_screener_page():
    """Render the stock screener page."""

    st.markdown("# 🔍 Stock Screener")
    st.markdown("Filter stocks based on fundamental criteria")

    col1, col2 = st.columns([2, 1])

    with col1:
        query = st.text_area(
            "Enter filter query:",
            value="Market Cap > 500 AND ROE > 15 AND Debt to Equity < 1 AND OPM > 15",
            height=100
        )

    with col2:
        templates = st.session_state.screener.get_templates()
        template_names = list(templates.keys())
        selected_template = st.selectbox("Quick Templates:", ["Custom"] + template_names)

        if selected_template != "Custom":
            template = templates[selected_template]
            st.info(f"**{template['name']}**: {template['description']}")

    if st.button("🔍 Run Screener", type="primary", use_container_width=True):
        with st.spinner("Screening stocks..."):
            try:
                if selected_template != "Custom":
                    results = st.session_state.screener.screen_template(selected_template, limit=30)
                else:
                    filters = st.session_state.screener.parse_query(query)
                    if filters:
                        results = st.session_state.screener.screen(filters, limit=30)
                    else:
                        st.error("Invalid query")
                        return

                if results.empty:
                    st.warning("No stocks found")
                else:
                    st.success(f"Found {len(results)} stocks")
                    st.dataframe(results, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"Error: {str(e)}")


def main():
    """Main application."""
    render_sidebar()

    page = st.session_state.get('page', '🏠 Market Overview')

    if page == "🏠 Market Overview":
        render_market_overview()
    elif page == "📈 Stock Analysis":
        render_stock_analysis_page()
    elif page == "🔍 Stock Screener":
        render_screener_page()
    elif page == "🎯 Trading Strategies":
        render_strategies_page()


if __name__ == "__main__":
    main()
