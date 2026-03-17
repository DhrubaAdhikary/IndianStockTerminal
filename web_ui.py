"""
Indian Stock Market Terminal - Web UI
=====================================
A TradingView-style interactive web interface for Indian stocks.

Features:
- Interactive candlestick charts with Plotly
- Technical indicators (EMA, RSI, MACD, Bollinger Bands)
- Support and Resistance levels
- All-Time High/Low markers
- Point-to-point gain measurement
- Real-time stock data and fundamentals

Run with: streamlit run web_ui.py
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from data_fetcher import IndianStockDataFetcher
from technical_analysis import TechnicalAnalysis

# Page configuration
st.set_page_config(
    page_title="Indian Stock Terminal",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for TradingView-like dark theme
st.markdown("""
<style>
    /* Dark theme styling */
    .stApp {
        background-color: #131722;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1e222d;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: bold;
    }

    /* Headers */
    h1, h2, h3 {
        color: #d1d4dc !important;
    }

    /* Price up/down colors */
    .price-up {
        color: #26a69a !important;
        font-weight: bold;
    }

    .price-down {
        color: #ef5350 !important;
        font-weight: bold;
    }

    /* Custom metric box */
    .metric-box {
        background-color: #1e222d;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
    }

    /* Stock info header */
    .stock-header {
        background: linear-gradient(135deg, #1e222d 0%, #2a2e39 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    /* Signal badges */
    .signal-bullish {
        background-color: #26a69a;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }

    .signal-bearish {
        background-color: #ef5350;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }

    .signal-neutral {
        background-color: #787b86;
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1e222d;
        border-radius: 4px;
        color: #d1d4dc;
        padding: 10px 20px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #2962ff;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'fetcher' not in st.session_state:
    st.session_state.fetcher = IndianStockDataFetcher(exchange="NSE")

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

if 'selected_stock' not in st.session_state:
    st.session_state.selected_stock = "RELIANCE"

if 'measurement_points' not in st.session_state:
    st.session_state.measurement_points = []


def format_large_number(num: float) -> str:
    """Format number in Indian style (Cr, L)."""
    if not num or num == 0:
        return "N/A"
    abs_num = abs(num)
    sign = "-" if num < 0 else ""
    if abs_num >= 10000000:
        return f"{sign}₹{abs_num/10000000:,.2f} Cr"
    elif abs_num >= 100000:
        return f"{sign}₹{abs_num/100000:,.2f} L"
    elif abs_num >= 1000:
        return f"{sign}₹{abs_num/1000:,.2f} K"
    else:
        return f"{sign}₹{abs_num:,.2f}"


def get_signal_color(signal: str) -> str:
    """Get color class for signal."""
    if 'BULLISH' in signal or signal == 'BUY':
        return 'signal-bullish'
    elif 'BEARISH' in signal or signal == 'SELL':
        return 'signal-bearish'
    else:
        return 'signal-neutral'


def create_candlestick_chart(
    df: pd.DataFrame,
    symbol: str,
    show_ema20: bool = True,
    show_ema50: bool = True,
    show_ema200: bool = True,
    show_volume: bool = True,
    show_rsi: bool = True,
    show_support_resistance: bool = True,
    show_ath_atl: bool = True,
    show_bollinger: bool = False,
    measurement_mode: bool = False
) -> go.Figure:
    """
    Create interactive candlestick chart with indicators.
    """
    # Add technical indicators
    df = TechnicalAnalysis.add_all_indicators(df)

    # Determine number of rows for subplots
    rows = 1
    row_heights = [0.7]

    if show_rsi:
        rows += 1
        row_heights.append(0.15)

    if show_volume:
        rows += 1
        row_heights.append(0.15)

    # Create subplots
    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=[f'{symbol} Price', 'RSI' if show_rsi else None, 'Volume' if show_volume else None]
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350',
            increasing_fillcolor='#26a69a',
            decreasing_fillcolor='#ef5350',
        ),
        row=1, col=1
    )

    # EMAs
    if show_ema20 and 'EMA_20' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['EMA_20'],
                name='EMA 20',
                line=dict(color='#f7931a', width=1.5),
                hovertemplate='EMA 20: ₹%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    if show_ema50 and 'EMA_50' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['EMA_50'],
                name='EMA 50',
                line=dict(color='#2962ff', width=1.5),
                hovertemplate='EMA 50: ₹%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    if show_ema200 and 'EMA_200' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['EMA_200'],
                name='EMA 200',
                line=dict(color='#9c27b0', width=2),
                hovertemplate='EMA 200: ₹%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    # Bollinger Bands
    if show_bollinger and 'BB_Upper' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['BB_Upper'],
                name='BB Upper',
                line=dict(color='rgba(128, 128, 128, 0.5)', width=1),
                hovertemplate='BB Upper: ₹%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['BB_Lower'],
                name='BB Lower',
                line=dict(color='rgba(128, 128, 128, 0.5)', width=1),
                fill='tonexty',
                fillcolor='rgba(128, 128, 128, 0.1)',
                hovertemplate='BB Lower: ₹%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    # Support and Resistance
    if show_support_resistance:
        sr_levels = TechnicalAnalysis.find_support_resistance(df)

        for i, resistance in enumerate(sr_levels['resistance'][:3]):
            fig.add_hline(
                y=resistance,
                line_dash="dash",
                line_color="#ef5350",
                line_width=1,
                annotation_text=f"R{i+1}: ₹{resistance:,.2f}",
                annotation_position="right",
                row=1, col=1
            )

        for i, support in enumerate(sr_levels['support'][:3]):
            fig.add_hline(
                y=support,
                line_dash="dash",
                line_color="#26a69a",
                line_width=1,
                annotation_text=f"S{i+1}: ₹{support:,.2f}",
                annotation_position="right",
                row=1, col=1
            )

    # All-Time High/Low
    if show_ath_atl:
        ath_atl = TechnicalAnalysis.find_all_time_high_low(df)

        # ATH line
        fig.add_hline(
            y=ath_atl['ath']['price'],
            line_dash="dot",
            line_color="#ffd700",
            line_width=2,
            annotation_text=f"ATH: ₹{ath_atl['ath']['price']:,.2f}",
            annotation_position="right",
            annotation_font_color="#ffd700",
            row=1, col=1
        )

        # ATL line
        fig.add_hline(
            y=ath_atl['atl']['price'],
            line_dash="dot",
            line_color="#ff6b6b",
            line_width=2,
            annotation_text=f"ATL: ₹{ath_atl['atl']['price']:,.2f}",
            annotation_position="right",
            annotation_font_color="#ff6b6b",
            row=1, col=1
        )

    # RSI
    current_row = 2
    if show_rsi and 'RSI' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['RSI'],
                name='RSI',
                line=dict(color='#7c4dff', width=1.5),
                hovertemplate='RSI: %{y:.2f}<extra></extra>'
            ),
            row=current_row, col=1
        )

        # RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", line_width=1, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", line_width=1, row=current_row, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#787b86", line_width=1, row=current_row, col=1)

        # RSI background zones
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239, 83, 80, 0.1)", line_width=0, row=current_row, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="rgba(38, 166, 154, 0.1)", line_width=0, row=current_row, col=1)

        current_row += 1

    # Volume
    if show_volume:
        colors = ['#26a69a' if close >= open else '#ef5350'
                  for close, open in zip(df['Close'], df['Open'])]

        fig.add_trace(
            go.Bar(
                x=df.index, y=df['Volume'],
                name='Volume',
                marker_color=colors,
                hovertemplate='Volume: %{y:,.0f}<extra></extra>'
            ),
            row=current_row, col=1
        )

    # Update layout for dark theme
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#131722',
        plot_bgcolor='#131722',
        font=dict(color='#d1d4dc'),
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(30, 34, 45, 0.8)',
            bordercolor='#363a45',
            borderwidth=1
        ),
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        dragmode='zoom' if not measurement_mode else 'select',
    )

    # Update axes
    fig.update_xaxes(
        gridcolor='#363a45',
        showgrid=True,
        zeroline=False,
    )

    fig.update_yaxes(
        gridcolor='#363a45',
        showgrid=True,
        zeroline=False,
        side='right'
    )

    # Update RSI y-axis range
    if show_rsi:
        fig.update_yaxes(range=[0, 100], row=2, col=1)

    return fig


def render_sidebar():
    """Render the sidebar with commands and controls."""
    with st.sidebar:
        st.markdown("## 🇮🇳 Indian Stock Terminal")
        st.markdown("---")

        # Stock Search
        st.markdown("### 🔍 Stock Search")

        # Popular stocks dropdown
        popular_stocks = list(st.session_state.fetcher.POPULAR_STOCKS.keys())
        selected = st.selectbox(
            "Select Stock",
            options=popular_stocks,
            index=popular_stocks.index(st.session_state.selected_stock) if st.session_state.selected_stock in popular_stocks else 0,
            format_func=lambda x: f"{x} - {st.session_state.fetcher.POPULAR_STOCKS.get(x, x)[:20]}"
        )

        # Custom symbol input
        custom_symbol = st.text_input("Or enter symbol:", placeholder="e.g., TATASTEEL")

        if custom_symbol:
            st.session_state.selected_stock = custom_symbol.upper()
        else:
            st.session_state.selected_stock = selected

        st.markdown("---")

        # Time Period
        st.markdown("### 📅 Time Period")
        period = st.selectbox(
            "Select Period",
            options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
            index=2,
            format_func=lambda x: {
                "1mo": "1 Month",
                "3mo": "3 Months",
                "6mo": "6 Months",
                "1y": "1 Year",
                "2y": "2 Years",
                "5y": "5 Years",
                "max": "All Time"
            }.get(x, x)
        )

        st.markdown("---")

        # Chart Indicators
        st.markdown("### 📊 Indicators")

        col1, col2 = st.columns(2)
        with col1:
            show_ema20 = st.checkbox("EMA 20", value=True)
            show_ema50 = st.checkbox("EMA 50", value=True)
            show_ema200 = st.checkbox("EMA 200", value=True)

        with col2:
            show_rsi = st.checkbox("RSI", value=True)
            show_volume = st.checkbox("Volume", value=True)
            show_bollinger = st.checkbox("Bollinger", value=False)

        st.markdown("---")

        # Analysis Tools
        st.markdown("### 🔧 Analysis Tools")
        show_sr = st.checkbox("Support/Resistance", value=True)
        show_ath_atl = st.checkbox("ATH/ATL Lines", value=True)
        measurement_mode = st.checkbox("📏 Measurement Mode", value=False)

        if measurement_mode:
            st.info("Click on two points on the chart to measure gain/loss between them.")
            if st.button("Clear Measurements"):
                st.session_state.measurement_points = []

        st.markdown("---")

        # Watchlist
        st.markdown("### ⭐ Watchlist")
        for stock in st.session_state.watchlist:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(stock, key=f"watch_{stock}", use_container_width=True):
                    st.session_state.selected_stock = stock
                    st.rerun()
            with col2:
                if st.button("❌", key=f"remove_{stock}"):
                    st.session_state.watchlist.remove(stock)
                    st.rerun()

        # Add to watchlist
        new_stock = st.text_input("Add to watchlist:", placeholder="Symbol")
        if new_stock and st.button("Add ➕"):
            if new_stock.upper() not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_stock.upper())
                st.rerun()

        st.markdown("---")

        # Commands Reference
        with st.expander("📖 Keyboard Shortcuts"):
            st.markdown("""
            - **Scroll**: Zoom in/out
            - **Click + Drag**: Pan chart
            - **Double-click**: Reset zoom
            - **Hover**: See OHLCV data
            """)

        return period, show_ema20, show_ema50, show_ema200, show_rsi, show_volume, show_bollinger, show_sr, show_ath_atl, measurement_mode


def render_stock_header(price_data: Dict[str, Any], fundamentals: Dict[str, Any]):
    """Render the stock header with key metrics."""
    st.markdown('<div class="stock-header">', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

    with col1:
        st.markdown(f"### {price_data.get('company_name', price_data['symbol'])}")
        st.markdown(f"**{price_data['symbol']}** | {price_data.get('exchange', 'NSE')}")

    with col2:
        current_price = price_data.get('current_price', 0)
        change = price_data.get('change', 0)
        change_pct = price_data.get('change_percent', 0)

        color = "#26a69a" if change >= 0 else "#ef5350"
        arrow = "▲" if change >= 0 else "▼"

        st.markdown(f"<h2 style='color: {color}; margin: 0;'>₹{current_price:,.2f}</h2>", unsafe_allow_html=True)
        st.markdown(f"<span style='color: {color};'>{arrow} ₹{abs(change):,.2f} ({change_pct:+.2f}%)</span>", unsafe_allow_html=True)

    with col3:
        st.metric("Day High", f"₹{price_data.get('day_high', 0):,.2f}")

    with col4:
        st.metric("Day Low", f"₹{price_data.get('day_low', 0):,.2f}")

    with col5:
        st.metric("Volume", f"{price_data.get('volume', 0):,}")

    st.markdown('</div>', unsafe_allow_html=True)


def render_fundamentals_panel(fundamentals: Dict[str, Any]):
    """Render the fundamentals panel."""
    if "error" in fundamentals:
        st.error(f"Error loading fundamentals: {fundamentals['error']}")
        return

    st.markdown("### 📊 Key Fundamentals")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**Valuation**")
        val = fundamentals.get('valuation', {})
        st.metric("Market Cap", val.get('market_cap_formatted', 'N/A'))
        st.metric("P/E Ratio", val.get('pe_ratio', 'N/A'))
        st.metric("P/B Ratio", val.get('price_to_book', 'N/A'))
        st.metric("EV/EBITDA", val.get('ev_to_ebitda', 'N/A'))

    with col2:
        st.markdown("**Profitability**")
        prof = fundamentals.get('profitability', {})
        st.metric("Profit Margin", prof.get('profit_margin', 'N/A'))
        st.metric("ROE", prof.get('return_on_equity', 'N/A'))
        st.metric("ROA", prof.get('return_on_assets', 'N/A'))
        st.metric("Operating Margin", prof.get('operating_margin', 'N/A'))

    with col3:
        st.markdown("**Per Share**")
        ps = fundamentals.get('per_share', {})
        st.metric("EPS (TTM)", f"₹{ps.get('eps_ttm', 'N/A')}")
        st.metric("Book Value", f"₹{ps.get('book_value', 'N/A')}")
        div = fundamentals.get('dividends', {})
        st.metric("Dividend Yield", div.get('dividend_yield', 'N/A'))
        st.metric("Payout Ratio", div.get('payout_ratio', 'N/A'))

    with col4:
        st.markdown("**Financial Health**")
        health = fundamentals.get('financial_health', {})
        st.metric("Debt/Equity", health.get('debt_to_equity', 'N/A'))
        st.metric("Current Ratio", health.get('current_ratio', 'N/A'))
        st.metric("Total Cash", health.get('total_cash', 'N/A'))
        st.metric("Total Debt", health.get('total_debt', 'N/A'))


def render_signals_panel(df: pd.DataFrame):
    """Render trading signals panel."""
    df_with_indicators = TechnicalAnalysis.add_all_indicators(df)
    signals = TechnicalAnalysis.get_signal(df_with_indicators)

    st.markdown("### 🎯 Trading Signals")

    cols = st.columns(5)

    with cols[0]:
        signal_class = get_signal_color(signals.get('overall', 'NEUTRAL'))
        st.markdown(f"""
        <div style='text-align: center; padding: 10px; background-color: #1e222d; border-radius: 8px;'>
            <p style='color: #787b86; margin: 0;'>Overall Signal</p>
            <span class='{signal_class}'>{signals.get('overall', 'N/A')}</span>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        signal_class = get_signal_color(signals.get('ema_trend', 'NEUTRAL'))
        st.markdown(f"""
        <div style='text-align: center; padding: 10px; background-color: #1e222d; border-radius: 8px;'>
            <p style='color: #787b86; margin: 0;'>EMA Trend</p>
            <span class='{signal_class}'>{signals.get('ema_trend', 'N/A')}</span>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        signal_class = get_signal_color(signals.get('rsi', 'NEUTRAL'))
        st.markdown(f"""
        <div style='text-align: center; padding: 10px; background-color: #1e222d; border-radius: 8px;'>
            <p style='color: #787b86; margin: 0;'>RSI Signal</p>
            <span class='{signal_class}'>{signals.get('rsi', 'N/A')}</span>
        </div>
        """, unsafe_allow_html=True)

    with cols[3]:
        signal_class = get_signal_color(signals.get('macd', 'NEUTRAL'))
        st.markdown(f"""
        <div style='text-align: center; padding: 10px; background-color: #1e222d; border-radius: 8px;'>
            <p style='color: #787b86; margin: 0;'>MACD Signal</p>
            <span class='{signal_class}'>{signals.get('macd', 'N/A')}</span>
        </div>
        """, unsafe_allow_html=True)

    with cols[4]:
        # Current RSI value
        latest_rsi = df_with_indicators['RSI'].iloc[-1]
        rsi_color = "#ef5350" if latest_rsi > 70 else "#26a69a" if latest_rsi < 30 else "#787b86"
        st.markdown(f"""
        <div style='text-align: center; padding: 10px; background-color: #1e222d; border-radius: 8px;'>
            <p style='color: #787b86; margin: 0;'>RSI Value</p>
            <span style='color: {rsi_color}; font-weight: bold; font-size: 1.2em;'>{latest_rsi:.1f}</span>
        </div>
        """, unsafe_allow_html=True)


def render_measurement_tool(df: pd.DataFrame):
    """Render the point-to-point measurement tool."""
    st.markdown("### 📏 Gain/Loss Calculator")

    col1, col2, col3 = st.columns(3)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=df.index[0].date(),
            min_value=df.index[0].date(),
            max_value=df.index[-1].date()
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=df.index[-1].date(),
            min_value=df.index[0].date(),
            max_value=df.index[-1].date()
        )

    # Find nearest dates in data
    start_idx = df.index.get_indexer([pd.Timestamp(start_date)], method='nearest')[0]
    end_idx = df.index.get_indexer([pd.Timestamp(end_date)], method='nearest')[0]

    start_price = df.iloc[start_idx]['Close']
    end_price = df.iloc[end_idx]['Close']

    gain = end_price - start_price
    gain_pct = (gain / start_price) * 100

    with col3:
        color = "#26a69a" if gain >= 0 else "#ef5350"
        arrow = "▲" if gain >= 0 else "▼"

        st.markdown(f"""
        <div style='text-align: center; padding: 20px; background-color: #1e222d; border-radius: 8px;'>
            <p style='color: #787b86; margin: 0;'>Gain/Loss</p>
            <h3 style='color: {color}; margin: 5px 0;'>{arrow} ₹{abs(gain):,.2f}</h3>
            <p style='color: {color}; margin: 0; font-size: 1.2em;'>{gain_pct:+.2f}%</p>
        </div>
        """, unsafe_allow_html=True)

    # Details
    st.markdown(f"""
    **Period Analysis:**
    - Start: {df.index[start_idx].strftime('%Y-%m-%d')} @ ₹{start_price:,.2f}
    - End: {df.index[end_idx].strftime('%Y-%m-%d')} @ ₹{end_price:,.2f}
    - Trading Days: {end_idx - start_idx}
    """)


def render_market_overview():
    """Render market indices overview."""
    st.markdown("### 📈 Market Overview")

    indices = ["NIFTY50", "SENSEX", "BANKNIFTY"]
    cols = st.columns(len(indices))

    for i, index_name in enumerate(indices):
        with cols[i]:
            data = st.session_state.fetcher.get_index_data(index_name)
            if "error" not in data:
                color = "#26a69a" if data['change'] >= 0 else "#ef5350"
                arrow = "▲" if data['change'] >= 0 else "▼"

                st.markdown(f"""
                <div style='text-align: center; padding: 15px; background-color: #1e222d; border-radius: 8px;'>
                    <p style='color: #787b86; margin: 0;'>{index_name}</p>
                    <h3 style='color: #d1d4dc; margin: 5px 0;'>{data['current_price']:,.2f}</h3>
                    <p style='color: {color}; margin: 0;'>{arrow} {data['change_percent']:+.2f}%</p>
                </div>
                """, unsafe_allow_html=True)


def main():
    """Main application."""
    # Render sidebar and get settings
    period, show_ema20, show_ema50, show_ema200, show_rsi, show_volume, show_bollinger, show_sr, show_ath_atl, measurement_mode = render_sidebar()

    symbol = st.session_state.selected_stock

    # Main content area
    st.markdown(f"# 📊 {symbol} Analysis")

    # Market Overview
    render_market_overview()

    st.markdown("---")

    # Fetch data
    with st.spinner(f"Loading data for {symbol}..."):
        price_data = st.session_state.fetcher.get_realtime_price(symbol)
        fundamentals = st.session_state.fetcher.get_fundamentals(symbol)
        df = st.session_state.fetcher.get_historical_data(symbol, period=period)

    if df.empty:
        st.error(f"No data available for {symbol}")
        return

    # Stock Header
    render_stock_header(price_data, fundamentals)

    # Trading Signals
    render_signals_panel(df)

    st.markdown("---")

    # Main Chart
    st.markdown("### 📈 Price Chart")

    fig = create_candlestick_chart(
        df=df,
        symbol=symbol,
        show_ema20=show_ema20,
        show_ema50=show_ema50,
        show_ema200=show_ema200,
        show_volume=show_volume,
        show_rsi=show_rsi,
        show_support_resistance=show_sr,
        show_ath_atl=show_ath_atl,
        show_bollinger=show_bollinger,
        measurement_mode=measurement_mode
    )

    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape'],
        'modeBarButtonsToRemove': ['lasso2d']
    })

    st.markdown("---")

    # Measurement Tool
    render_measurement_tool(df)

    st.markdown("---")

    # Tabs for additional info
    tab1, tab2, tab3 = st.tabs(["📊 Fundamentals", "📈 Technical Levels", "📋 Price Data"])

    with tab1:
        render_fundamentals_panel(fundamentals)

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Support & Resistance Levels")
            sr = TechnicalAnalysis.find_support_resistance(df)

            st.markdown("**Resistance Levels:**")
            for i, r in enumerate(sr['resistance'][:5]):
                st.markdown(f"- R{i+1}: ₹{r:,.2f}")

            st.markdown("**Support Levels:**")
            for i, s in enumerate(sr['support'][:5]):
                st.markdown(f"- S{i+1}: ₹{s:,.2f}")

        with col2:
            st.markdown("#### Fibonacci Retracement")
            ath_atl = TechnicalAnalysis.find_all_time_high_low(df)
            fib = TechnicalAnalysis.calculate_fibonacci_retracement(
                ath_atl['ath']['price'],
                ath_atl['atl']['price']
            )

            for level, price in fib.items():
                st.markdown(f"- **{level}**: ₹{price:,.2f}")

    with tab3:
        st.markdown("#### Recent Price Data")
        display_df = df.tail(20)[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        display_df.index = display_df.index.strftime('%Y-%m-%d')
        display_df = display_df.round(2)
        st.dataframe(display_df, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown(
        f"<p style='text-align: center; color: #787b86;'>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST | Data from Yahoo Finance</p>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
