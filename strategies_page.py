"""
Trading Strategies Page - With Custom Stock Input
==================================================
Allows:
- Paste custom stock symbols (up to 6000)
- Apply trading strategies
- Full stock analysis on click
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional

from data_fetcher import IndianStockDataFetcher
from trading_strategies import TradingStrategies, StrategySignal, STRATEGY_INFO
from backtester import Backtester, format_backtest_result
from technical_analysis import TechnicalAnalysis
from news_sentiment import NewsSentimentAnalyzer, Sentiment
from stock_universe import (
    NIFTY_50, NIFTY_100, NIFTY_200, ALL_STOCKS,
    STOCKS_BY_CATEGORY, parse_custom_symbols
)


def render_strategies_page():
    """Render the trading strategies page."""

    st.markdown("# 🎯 Trading Strategies Scanner")
    st.markdown("Scan stocks for entry signals using professional strategies")

    # Initialize
    if 'fetcher' not in st.session_state:
        st.session_state.fetcher = IndianStockDataFetcher()
    if 'strategies' not in st.session_state:
        st.session_state.strategies = TradingStrategies()
    if 'backtester' not in st.session_state:
        st.session_state.backtester = Backtester()
    if 'news_analyzer' not in st.session_state:
        st.session_state.news_analyzer = NewsSentimentAnalyzer()

    # Step 1: Stock Selection
    st.markdown("### 📋 Step 1: Select Stocks to Scan")

    input_method = st.radio(
        "Choose input method:",
        ["📊 Predefined List", "✏️ Custom Symbols (Paste your list)"],
        horizontal=True
    )

    if input_method == "📊 Predefined List":
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox(
                "Select stock category:",
                ["Nifty 50", "Nifty 100", "Nifty 200", "Nifty Midcap 100", "All Stocks (300+)"]
            )
        with col2:
            st.info(f"Stocks in {category}: {len(STOCKS_BY_CATEGORY.get(category.replace(' (300+)', ''), []))}")

        if category == "Nifty 50":
            stocks_to_scan = NIFTY_50
        elif category == "Nifty 100":
            stocks_to_scan = NIFTY_100
        elif category == "Nifty 200":
            stocks_to_scan = NIFTY_200
        elif category == "All Stocks (300+)":
            stocks_to_scan = ALL_STOCKS
        else:
            stocks_to_scan = STOCKS_BY_CATEGORY.get("Nifty Midcap 100", NIFTY_100)

    else:
        st.markdown("**Paste stock symbols (comma, space, or newline separated):**")
        custom_input = st.text_area(
            "Stock Symbols:",
            placeholder="RELIANCE, TCS, INFY, HDFCBANK\nor\nRELIANCE\nTCS\nINFY",
            height=150,
            help="You can paste up to 6000 stock symbols"
        )

        if custom_input:
            stocks_to_scan = parse_custom_symbols(custom_input)
            st.success(f"✅ Parsed {len(stocks_to_scan)} unique symbols")

            # Show preview
            with st.expander("Preview parsed symbols"):
                st.write(", ".join(stocks_to_scan[:50]))
                if len(stocks_to_scan) > 50:
                    st.write(f"... and {len(stocks_to_scan) - 50} more")
        else:
            stocks_to_scan = []

    st.markdown("---")

    # Step 2: Strategy Selection
    st.markdown("### 🎯 Step 2: Select Trading Strategy")

    strategy_names = list(STRATEGY_INFO.keys())

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_strategy = st.selectbox(
            "Choose a strategy:",
            strategy_names,
            format_func=lambda x: f"📈 {x}"
        )

    with col2:
        min_score = st.slider("Minimum Score", 0, 100, 50)

    # Strategy info
    if selected_strategy:
        info = STRATEGY_INFO[selected_strategy]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; color: white;">
            <h3 style="margin: 0 0 10px 0;">{selected_strategy}</h3>
            <p style="margin: 5px 0;">{info['description']}</p>
            <div style="display: flex; gap: 30px; margin-top: 15px;">
                <div><b>Win Rate:</b> {info['typical_win_rate']}</div>
                <div><b>Sharpe:</b> {info['typical_sharpe']}</div>
                <div><b>Annual Return:</b> {info.get('annual_return', 'N/A')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Scan button
    if stocks_to_scan:
        if st.button(f"🔍 Scan {len(stocks_to_scan)} Stocks", type="primary", use_container_width=True):
            scan_stocks(selected_strategy, min_score, stocks_to_scan)
    else:
        st.warning("Please select or enter stocks to scan")

    # Show results
    if 'strategy_scan_results' in st.session_state and st.session_state.strategy_scan_results:
        render_scan_results(selected_strategy)


def scan_stocks(strategy_name: str, min_score: float, symbols: List[str]):
    """Scan stocks for strategy signals."""

    strategies = st.session_state.strategies
    fetcher = st.session_state.fetcher

    strategy_map = {
        "200-Day Trend + ATH Breakout": strategies.strategy_200dma_ath_breakout,
        "52-Week High Momentum": strategies.strategy_52week_high_momentum,
        "Volatility Contraction Pattern (VCP)": strategies.strategy_vcp,
        "Cup and Handle Breakout": strategies.strategy_cup_and_handle,
        "Donchian Channel (Turtle Strategy)": strategies.strategy_donchian_turtle,
        "MA Momentum Stack": strategies.strategy_ma_momentum_stack,
        "Relative Strength Breakout": strategies.strategy_relative_strength,
        "Bollinger Band Squeeze": strategies.strategy_bollinger_squeeze,
        "Base Formation Breakout": strategies.strategy_base_breakout,
        "Stage Analysis (Weinstein)": strategies.strategy_stage_analysis,
    }

    strategy_func = strategy_map.get(strategy_name)
    if not strategy_func:
        st.error("Strategy not found")
        return

    results = []
    progress = st.progress(0)
    status = st.empty()
    scanned = 0
    errors = 0

    for i, symbol in enumerate(symbols):
        try:
            status.text(f"Scanning {symbol}... ({i+1}/{len(symbols)}) - Found: {len(results)}")
            progress.progress((i + 1) / len(symbols))

            # Get historical data
            df = fetcher.get_historical_data(symbol, period="1y")
            if df.empty or len(df) < 200:
                continue

            # Run strategy
            result = strategy_func(df, symbol)
            scanned += 1

            if result.score >= min_score:
                # Get price data
                price_data = fetcher.get_realtime_price(symbol)

                results.append({
                    'symbol': symbol,
                    'company': price_data.get('company_name', symbol),
                    'price': price_data.get('current_price', 0),
                    'change_pct': price_data.get('change_percent', 0),
                    'score': result.score,
                    'signal': result.signal.value,
                    'entry_price': result.entry_price,
                    'stop_loss': result.stop_loss,
                    'target': result.target,
                    'risk_reward': result.risk_reward,
                    'conditions_met': result.conditions_met,
                    'conditions_failed': result.conditions_failed,
                    'additional_info': result.additional_info,
                    '52w_high': price_data.get('fifty_two_week_high', 0),
                    '52w_low': price_data.get('fifty_two_week_low', 0),
                })

        except Exception as e:
            errors += 1
            continue

    progress.empty()
    status.empty()

    # Sort by score
    results = sorted(results, key=lambda x: x['score'], reverse=True)
    st.session_state.strategy_scan_results = results
    st.session_state.current_strategy_name = strategy_name

    if results:
        st.success(f"✅ Found {len(results)} stocks with entry signals (Scanned: {scanned}, Errors: {errors})")
    else:
        st.warning(f"No stocks found matching criteria (Scanned: {scanned}, Errors: {errors})")


def render_scan_results(strategy_name: str):
    """Render scan results with full analysis on click."""

    results = st.session_state.strategy_scan_results

    st.markdown(f"### 📋 Results: {len(results)} Stocks with Entry Signals")

    # Results table
    df = pd.DataFrame([{
        'Symbol': r['symbol'],
        'Company': r['company'][:25] if r['company'] else r['symbol'],
        'Price': f"₹{r['price']:,.2f}",
        'Change': f"{r['change_pct']:+.2f}%",
        'Score': f"{r['score']:.0f}/100",
        'Signal': r['signal'],
        'Entry': f"₹{r['entry_price']:,.2f}",
        'Stop Loss': f"₹{r['stop_loss']:,.2f}",
        'Target': f"₹{r['target']:,.2f}",
        'R:R': f"{r['risk_reward']:.1f}:1",
    } for r in results])

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Detailed analysis
    st.markdown("### 📊 Detailed Stock Analysis")

    selected_symbol = st.selectbox(
        "Select a stock for detailed analysis:",
        [r['symbol'] for r in results],
        format_func=lambda x: f"{x} - Score: {next((r['score'] for r in results if r['symbol'] == x), 0):.0f}"
    )

    if selected_symbol:
        result = next((r for r in results if r['symbol'] == selected_symbol), None)
        if result:
            render_stock_detail(result, strategy_name)


def render_stock_detail(result: Dict, strategy_name: str):
    """Render full stock analysis."""

    symbol = result['symbol']
    fetcher = st.session_state.fetcher
    news_analyzer = st.session_state.news_analyzer

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Chart & Entry",
        "📊 Fundamentals",
        "📰 News",
        "📋 Backtest",
        "💰 Financials"
    ])

    with tab1:
        render_chart_tab(symbol, result)

    with tab2:
        render_fundamentals_tab(symbol)

    with tab3:
        render_news_tab(symbol)

    with tab4:
        render_backtest_tab(symbol, strategy_name)

    with tab5:
        render_financials_tab(symbol)


def render_chart_tab(symbol: str, result: Dict):
    """Render chart with entry points."""

    fetcher = st.session_state.fetcher

    df = fetcher.get_historical_data(symbol, period="6mo")
    if df.empty:
        st.error("No chart data")
        return

    df = TechnicalAnalysis.add_all_indicators(df)

    # Create chart
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.05, row_heights=[0.6, 0.2, 0.2],
        subplot_titles=('Price Chart', 'Volume', 'RSI')
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='Price'
    ), row=1, col=1)

    # EMAs
    if 'EMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], name='EMA 20',
                                 line=dict(color='orange', width=1)), row=1, col=1)
    if 'EMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], name='EMA 50',
                                 line=dict(color='blue', width=1)), row=1, col=1)
    if 'SMA_200' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], name='SMA 200',
                                 line=dict(color='purple', width=1.5)), row=1, col=1)

    # Entry/SL/Target
    if result['entry_price'] > 0:
        fig.add_hline(y=result['entry_price'], line_dash="dash", line_color="green",
                      annotation_text=f"Entry: ₹{result['entry_price']:,.0f}", row=1, col=1)
    if result['stop_loss'] > 0:
        fig.add_hline(y=result['stop_loss'], line_dash="dash", line_color="red",
                      annotation_text=f"Stop: ₹{result['stop_loss']:,.0f}", row=1, col=1)
    if result['target'] > 0:
        fig.add_hline(y=result['target'], line_dash="dash", line_color="blue",
                      annotation_text=f"Target: ₹{result['target']:,.0f}", row=1, col=1)

    # Volume
    colors = ['red' if c < o else 'green' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

    # RSI
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI',
                                 line=dict(color='purple')), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    fig.update_layout(height=700, template='plotly_dark', xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Trade setup
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📈 Trade Setup")
        st.markdown(f"""
        - **Entry:** ₹{result['entry_price']:,.2f}
        - **Stop Loss:** ₹{result['stop_loss']:,.2f}
        - **Target:** ₹{result['target']:,.2f}
        - **R:R:** {result['risk_reward']:.1f}:1
        """)

    with col2:
        st.markdown("#### ✅ Conditions Met")
        for c in result['conditions_met'][:5]:
            st.markdown(f"✓ {c}")

    with col3:
        st.markdown("#### ❌ Conditions Failed")
        for c in result['conditions_failed'][:5]:
            st.markdown(f"✗ {c}")


def render_fundamentals_tab(symbol: str):
    """Render fundamentals."""

    fetcher = st.session_state.fetcher

    with st.spinner("Loading fundamentals..."):
        fund = fetcher.get_fundamentals(symbol)
        price = fetcher.get_realtime_price(symbol)

    if 'error' in fund:
        st.error("Unable to load fundamentals")
        return

    st.markdown(f"### {fund.get('company_name', symbol)}")
    st.markdown(f"**Sector:** {fund.get('sector', 'N/A')} | **Industry:** {fund.get('industry', 'N/A')}")

    val = fund.get('valuation', {})
    prof = fund.get('profitability', {})
    health = fund.get('financial_health', {})
    div = fund.get('dividends', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**Valuation**")
        st.metric("Market Cap", val.get('market_cap_formatted', 'N/A'))
        st.metric("P/E Ratio", val.get('pe_ratio', 'N/A'))
        st.metric("P/B Ratio", val.get('price_to_book', 'N/A'))
        st.metric("EV/EBITDA", val.get('ev_to_ebitda', 'N/A'))

    with col2:
        st.markdown("**Profitability**")
        st.metric("ROE", prof.get('return_on_equity', 'N/A'))
        st.metric("ROA", prof.get('return_on_assets', 'N/A'))
        st.metric("Profit Margin", prof.get('profit_margin', 'N/A'))
        st.metric("Operating Margin", prof.get('operating_margin', 'N/A'))

    with col3:
        st.markdown("**Financial Health**")
        st.metric("Debt/Equity", health.get('debt_to_equity', 'N/A'))
        st.metric("Current Ratio", health.get('current_ratio', 'N/A'))
        st.metric("Quick Ratio", health.get('quick_ratio', 'N/A'))
        st.metric("Total Cash", health.get('total_cash', 'N/A'))

    with col4:
        st.markdown("**Price Data**")
        st.metric("52W High", f"₹{price.get('fifty_two_week_high', 0):,.2f}")
        st.metric("52W Low", f"₹{price.get('fifty_two_week_low', 0):,.2f}")
        st.metric("Div Yield", div.get('dividend_yield', 'N/A'))
        st.metric("Volume", f"{price.get('volume', 0):,}")


def render_news_tab(symbol: str):
    """Render news & sentiment."""

    news_analyzer = st.session_state.news_analyzer

    st.markdown("### 📰 News & Sentiment")

    with st.spinner("Fetching news..."):
        news_items = news_analyzer.get_stock_news(symbol, num_results=8)
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
    <div style="background: {color}20; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
        <h3 style="color: {color}; margin: 0;">Sentiment: {label}</h3>
    </div>
    """, unsafe_allow_html=True)

    if not news_items:
        st.info("No recent news found")
        return

    for news in news_items:
        emoji = "🟢" if news.sentiment in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE] else "🔴" if news.sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE] else "🟡"
        border_color = "#00ff88" if news.sentiment in [Sentiment.POSITIVE, Sentiment.VERY_POSITIVE] else "#ff4757" if news.sentiment in [Sentiment.NEGATIVE, Sentiment.VERY_NEGATIVE] else "#ffa502"

        st.markdown(f"""
        <div style="background: #1a1a2e; padding: 12px; border-radius: 8px; margin: 8px 0; border-left: 4px solid {border_color};">
            <b>{emoji} {news.title}</b>
            <br><small style="color: #666;">{news.source} | Score: {news.sentiment_score:+.2f}</small>
        </div>
        """, unsafe_allow_html=True)


def render_backtest_tab(symbol: str, strategy_name: str):
    """Render backtest results."""

    st.markdown("### 📋 Backtest Results")

    if st.button(f"Run Backtest for {symbol}", key=f"bt_{symbol}"):
        with st.spinner("Running backtest..."):
            fetcher = st.session_state.fetcher
            backtester = st.session_state.backtester
            strategies = st.session_state.strategies

            strategy_map = {
                "200-Day Trend + ATH Breakout": strategies.strategy_200dma_ath_breakout,
                "52-Week High Momentum": strategies.strategy_52week_high_momentum,
                "Volatility Contraction Pattern (VCP)": strategies.strategy_vcp,
                "Cup and Handle Breakout": strategies.strategy_cup_and_handle,
                "Donchian Channel (Turtle Strategy)": strategies.strategy_donchian_turtle,
                "MA Momentum Stack": strategies.strategy_ma_momentum_stack,
                "Relative Strength Breakout": strategies.strategy_relative_strength,
                "Bollinger Band Squeeze": strategies.strategy_bollinger_squeeze,
                "Base Formation Breakout": strategies.strategy_base_breakout,
                "Stage Analysis (Weinstein)": strategies.strategy_stage_analysis,
            }

            df = fetcher.get_historical_data(symbol, period="2y")
            if df.empty or len(df) < 250:
                st.error("Insufficient data")
                return

            strategy_func = strategy_map.get(strategy_name)
            if not strategy_func:
                st.error("Strategy not found")
                return

            result = backtester.backtest_strategy(df, strategy_func, symbol)

        # Display
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Return", f"{result.total_return:+.1f}%")
        with col2:
            st.metric("Win Rate", f"{result.win_rate:.1f}%")
        with col3:
            st.metric("Sharpe Ratio", f"{result.sharpe_ratio:.2f}")
        with col4:
            st.metric("Max Drawdown", f"{result.max_drawdown:.1f}%")

        # More metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Trade Stats**")
            st.write(f"Total Trades: {result.total_trades}")
            st.write(f"Winners: {result.winning_trades}")
            st.write(f"Losers: {result.losing_trades}")

        with col2:
            st.markdown("**Risk Metrics**")
            st.write(f"Sortino: {result.sortino_ratio:.2f}")
            st.write(f"Calmar: {result.calmar_ratio:.2f}")
            st.write(f"Omega: {result.omega_ratio:.2f}")

        with col3:
            st.markdown("**Returns**")
            st.write(f"Annual: {result.annual_return:.2f}%")
            st.write(f"Benchmark: {result.benchmark_return:.2f}%")
            st.write(f"Alpha: {result.alpha:.2f}%")

        # Equity curve
        if result.equity_curve:
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=result.equity_curve, mode='lines',
                                     line=dict(color='#667eea', width=2)))
            fig.update_layout(height=300, template='plotly_dark', yaxis_title='Portfolio Value')
            st.plotly_chart(fig, use_container_width=True)


def render_financials_tab(symbol: str):
    """Render financial statements."""

    fetcher = st.session_state.fetcher

    st.markdown("### 💰 Financial Statements")

    with st.spinner("Loading financials..."):
        try:
            statements = fetcher.get_financial_statements(symbol)
        except:
            st.error("Unable to load financial statements")
            return

    if statements.get('income_statement') is not None and not statements['income_statement'].empty:
        st.markdown("#### Income Statement")
        st.dataframe(statements['income_statement'].T.head(8), use_container_width=True)

    if statements.get('balance_sheet') is not None and not statements['balance_sheet'].empty:
        st.markdown("#### Balance Sheet")
        st.dataframe(statements['balance_sheet'].T.head(8), use_container_width=True)

    if statements.get('cash_flow') is not None and not statements['cash_flow'].empty:
        st.markdown("#### Cash Flow")
        st.dataframe(statements['cash_flow'].T.head(8), use_container_width=True)
