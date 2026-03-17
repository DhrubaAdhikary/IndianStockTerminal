#!/usr/bin/env python3
"""
Indian Stock Market Data - Complete Showcase
=============================================
This script demonstrates ALL the data fetching capabilities
for the Indian Stock Market Terminal.
"""

import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

from data_fetcher import IndianStockDataFetcher

console = Console()


def print_section(title: str):
    """Print section header."""
    console.print(f"\n{'═' * 80}")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print('═' * 80)


def showcase_data_fetching_methods():
    """Explain and demonstrate how data is fetched."""

    console.print(Panel("""
[bold cyan]HOW WE FETCH REAL-TIME DATA & FUNDAMENTALS[/bold cyan]

[yellow]1. Data Sources Used:[/yellow]
   • [green]Yahoo Finance[/green] - Primary source via yfinance library
   • Provides: Real-time prices, fundamentals, historical data, financials

[yellow]2. Stock Symbol Convention:[/yellow]
   • [green]NSE stocks:[/green] Add '.NS' suffix (e.g., RELIANCE.NS, TCS.NS)
   • [green]BSE stocks:[/green] Add '.BO' suffix (e.g., RELIANCE.BO, TCS.BO)

[yellow]3. API Connection:[/yellow]
   • Free tier has ~15-20 minute delay
   • No API key required for basic data
   • Rate limits apply for heavy usage

[yellow]4. Data Available:[/yellow]
   • Real-time prices (current, open, high, low, close)
   • Volume data (current, average)
   • Fundamental metrics (P/E, P/B, EPS, Market Cap)
   • Financial statements (Income, Balance Sheet, Cash Flow)
   • Historical OHLCV data
   • Analyst recommendations

[yellow]5. Code Example:[/yellow]
   [dim]import yfinance as yf
   ticker = yf.Ticker("RELIANCE.NS")
   info = ticker.info  # All fundamental data
   history = ticker.history(period="1mo")  # Historical data[/dim]
""", title="📚 Data Fetching Guide", border_style="blue"))


def showcase_realtime_data():
    """Showcase real-time price data."""
    print_section("1. REAL-TIME PRICE DATA")

    fetcher = IndianStockDataFetcher(exchange="NSE")

    # Demonstrate for multiple stocks
    stocks = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

    table = Table(
        title="📈 Real-Time Stock Prices",
        box=box.DOUBLE_EDGE,
        show_header=True,
        header_style="bold magenta"
    )

    table.add_column("Symbol", style="cyan", width=12)
    table.add_column("Company", width=28)
    table.add_column("Price (₹)", justify="right", width=12)
    table.add_column("Change", justify="right", width=12)
    table.add_column("% Change", justify="right", width=10)
    table.add_column("Day High", justify="right", width=12)
    table.add_column("Day Low", justify="right", width=12)
    table.add_column("Volume", justify="right", width=15)

    console.print("\n[dim]Fetching real-time data for top NSE stocks...[/dim]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Loading...", total=len(stocks))

        for symbol in stocks:
            data = fetcher.get_realtime_price(symbol)
            progress.update(task, advance=1, description=f"Fetching {symbol}...")

            if "error" not in data:
                change_style = "green" if data['change'] >= 0 else "red"
                change_symbol = "▲" if data['change'] >= 0 else "▼"

                table.add_row(
                    symbol,
                    data['company_name'][:28] if data['company_name'] else "N/A",
                    f"{data['current_price']:,.2f}",
                    f"[{change_style}]{change_symbol} {abs(data['change']):,.2f}[/{change_style}]",
                    f"[{change_style}]{data['change_percent']:+.2f}%[/{change_style}]",
                    f"{data['day_high']:,.2f}",
                    f"{data['day_low']:,.2f}",
                    f"{data['volume']:,}",
                )

    console.print(table)

    # Show raw data structure for one stock
    console.print("\n[bold yellow]Raw Data Structure (RELIANCE):[/bold yellow]")
    sample = fetcher.get_realtime_price("RELIANCE")
    if "error" not in sample:
        console.print_json(json.dumps({k: v for k, v in sample.items() if k != 'error'}, indent=2, default=str))


def showcase_fundamentals():
    """Showcase fundamental data."""
    print_section("2. COMPANY FUNDAMENTALS")

    fetcher = IndianStockDataFetcher(exchange="NSE")
    symbol = "TCS"

    console.print(f"\n[dim]Fetching fundamentals for {symbol}...[/dim]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"Loading {symbol} fundamentals...", total=None)
        data = fetcher.get_fundamentals(symbol)

    if "error" in data:
        console.print(f"[red]Error: {data['error']}[/red]")
        return

    # Company Profile
    console.print(Panel(
        f"""[bold]{data['company_name']}[/bold]

Sector: {data['sector']}
Industry: {data['industry']}
Website: {data['website']}

{data['description']}""",
        title="🏢 Company Profile",
        border_style="blue"
    ))

    # Valuation Metrics
    val_table = Table(title="💰 Valuation Metrics", box=box.ROUNDED)
    val_table.add_column("Metric", style="cyan", width=25)
    val_table.add_column("Value", justify="right", width=20)

    val = data['valuation']
    val_table.add_row("Market Cap", f"₹{val['market_cap_formatted']}")
    val_table.add_row("Enterprise Value", f"₹{val['enterprise_value_formatted']}")
    val_table.add_row("P/E Ratio (TTM)", str(val['pe_ratio']))
    val_table.add_row("Forward P/E", str(val['forward_pe']))
    val_table.add_row("PEG Ratio", str(val['peg_ratio']))
    val_table.add_row("Price to Book", str(val['price_to_book']))
    val_table.add_row("Price to Sales", str(val['price_to_sales']))
    val_table.add_row("EV/EBITDA", str(val['ev_to_ebitda']))
    val_table.add_row("EV/Revenue", str(val['ev_to_revenue']))

    console.print(val_table)

    # Profitability Metrics
    prof_table = Table(title="📊 Profitability Metrics", box=box.ROUNDED)
    prof_table.add_column("Metric", style="cyan", width=25)
    prof_table.add_column("Value", justify="right", width=20)

    prof = data['profitability']
    prof_table.add_row("Profit Margin", prof['profit_margin'])
    prof_table.add_row("Operating Margin", prof['operating_margin'])
    prof_table.add_row("Gross Margin", prof['gross_margin'])
    prof_table.add_row("EBITDA Margin", prof['ebitda_margin'])
    prof_table.add_row("Return on Equity (ROE)", prof['return_on_equity'])
    prof_table.add_row("Return on Assets (ROA)", prof['return_on_assets'])

    console.print(prof_table)

    # Financial Health
    health_table = Table(title="🏦 Financial Health", box=box.ROUNDED)
    health_table.add_column("Metric", style="cyan", width=25)
    health_table.add_column("Value", justify="right", width=20)

    health = data['financial_health']
    health_table.add_row("Total Cash", f"₹{health['total_cash']}")
    health_table.add_row("Total Debt", f"₹{health['total_debt']}")
    health_table.add_row("Debt to Equity", str(health['debt_to_equity']))
    health_table.add_row("Current Ratio", str(health['current_ratio']))
    health_table.add_row("Quick Ratio", str(health['quick_ratio']))

    console.print(health_table)

    # Per Share Data
    share_table = Table(title="📈 Per Share Data", box=box.ROUNDED)
    share_table.add_column("Metric", style="cyan", width=25)
    share_table.add_column("Value", justify="right", width=20)

    ps = data['per_share']
    share_table.add_row("EPS (TTM)", f"₹{ps['eps_ttm']}")
    share_table.add_row("EPS (Forward)", f"₹{ps['eps_forward']}")
    share_table.add_row("Book Value", f"₹{ps['book_value']}")
    share_table.add_row("Revenue Per Share", f"₹{ps['revenue_per_share']}")

    console.print(share_table)

    # Dividends
    div_table = Table(title="💵 Dividend Information", box=box.ROUNDED)
    div_table.add_column("Metric", style="cyan", width=25)
    div_table.add_column("Value", justify="right", width=20)

    div = data['dividends']
    div_table.add_row("Dividend Rate", f"₹{div['dividend_rate']}")
    div_table.add_row("Dividend Yield", div['dividend_yield'])
    div_table.add_row("Payout Ratio", div['payout_ratio'])

    console.print(div_table)

    # Financials
    fin_table = Table(title="📑 Financial Summary", box=box.ROUNDED)
    fin_table.add_column("Metric", style="cyan", width=25)
    fin_table.add_column("Value", justify="right", width=20)

    fin = data['financials']
    fin_table.add_row("Total Revenue", f"₹{fin['total_revenue']}")
    fin_table.add_row("Revenue Growth", fin['revenue_growth'])
    fin_table.add_row("Gross Profit", f"₹{fin['gross_profit']}")
    fin_table.add_row("EBITDA", f"₹{fin['ebitda']}")
    fin_table.add_row("Net Income", f"₹{fin['net_income']}")
    fin_table.add_row("Earnings Growth", fin['earnings_growth'])

    console.print(fin_table)

    # Shares Info
    shares_table = Table(title="📋 Shares Information", box=box.ROUNDED)
    shares_table.add_column("Metric", style="cyan", width=25)
    shares_table.add_column("Value", justify="right", width=20)

    shares = data['shares']
    shares_table.add_row("Shares Outstanding", shares['shares_outstanding'])
    shares_table.add_row("Float Shares", shares['float_shares'])
    shares_table.add_row("Insider Ownership", shares['insider_ownership'])
    shares_table.add_row("Institutional Ownership", shares['institutional_ownership'])

    console.print(shares_table)

    # Analyst Recommendations
    analyst = data['analyst']
    if analyst['target_mean']:
        console.print(Panel(
            f"""[bold]Recommendation:[/bold] {analyst['recommendation'].upper()}

[cyan]Price Targets:[/cyan]
  • Low:  ₹{analyst['target_low']:,.2f}
  • Mean: ₹{analyst['target_mean']:,.2f}
  • High: ₹{analyst['target_high']:,.2f}

[dim]Based on {analyst['num_analysts']} analyst(s)[/dim]""",
            title="🎯 Analyst Recommendations",
            border_style="yellow"
        ))


def showcase_market_indices():
    """Showcase market indices."""
    print_section("3. MARKET INDICES")

    fetcher = IndianStockDataFetcher(exchange="NSE")

    indices = {
        "NIFTY50": "Nifty 50 - Top 50 NSE stocks",
        "SENSEX": "BSE Sensex - Top 30 BSE stocks",
        "BANKNIFTY": "Bank Nifty - Banking sector index",
    }

    table = Table(title="📊 Indian Market Indices", box=box.DOUBLE_EDGE)
    table.add_column("Index", style="cyan", width=12)
    table.add_column("Description", width=30)
    table.add_column("Value", justify="right", width=12)
    table.add_column("Change", justify="right", width=12)
    table.add_column("% Change", justify="right", width=10)

    console.print("\n[dim]Fetching market indices...[/dim]\n")

    for index_name, description in indices.items():
        data = fetcher.get_index_data(index_name)

        if "error" not in data:
            change_style = "green" if data['change'] >= 0 else "red"
            change_symbol = "▲" if data['change'] >= 0 else "▼"

            table.add_row(
                index_name,
                description,
                f"{data['current_price']:,.2f}",
                f"[{change_style}]{change_symbol} {abs(data['change']):,.2f}[/{change_style}]",
                f"[{change_style}]{data['change_percent']:+.2f}%[/{change_style}]",
            )

    console.print(table)


def showcase_historical_data():
    """Showcase historical data."""
    print_section("4. HISTORICAL DATA")

    fetcher = IndianStockDataFetcher(exchange="NSE")
    symbol = "RELIANCE"

    console.print(f"\n[dim]Fetching historical data for {symbol}...[/dim]\n")

    df = fetcher.get_historical_data(symbol, period="1mo", interval="1d")

    if not df.empty:
        table = Table(title=f"📈 {symbol} - Last 1 Month Daily Data", box=box.ROUNDED)
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Open", justify="right", width=12)
        table.add_column("High", justify="right", width=12)
        table.add_column("Low", justify="right", width=12)
        table.add_column("Close", justify="right", width=12)
        table.add_column("Volume", justify="right", width=15)

        for date, row in df.tail(10).iterrows():
            table.add_row(
                date.strftime("%Y-%m-%d"),
                f"₹{row['Open']:,.2f}",
                f"₹{row['High']:,.2f}",
                f"₹{row['Low']:,.2f}",
                f"₹{row['Close']:,.2f}",
                f"{int(row['Volume']):,}",
            )

        console.print(table)

        # Summary statistics
        console.print(Panel(
            f"""[cyan]Period:[/cyan] {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}
[cyan]Trading Days:[/cyan] {len(df)}
[cyan]Opening Price:[/cyan] ₹{df['Open'].iloc[0]:,.2f}
[cyan]Closing Price:[/cyan] ₹{df['Close'].iloc[-1]:,.2f}
[cyan]Period High:[/cyan] ₹{df['High'].max():,.2f}
[cyan]Period Low:[/cyan] ₹{df['Low'].min():,.2f}
[cyan]Average Volume:[/cyan] {int(df['Volume'].mean()):,}
[cyan]Total Volume:[/cyan] {int(df['Volume'].sum()):,}""",
            title="📊 Period Summary",
            border_style="blue"
        ))


def showcase_financial_statements():
    """Showcase financial statements."""
    print_section("5. FINANCIAL STATEMENTS")

    fetcher = IndianStockDataFetcher(exchange="NSE")
    symbol = "INFY"

    console.print(f"\n[dim]Fetching financial statements for {symbol}...[/dim]\n")

    statements = fetcher.get_financial_statements(symbol)

    # Income Statement
    if not statements['income_statement'].empty:
        income = statements['income_statement']

        console.print(Panel(
            "[bold]Key Income Statement Items (Annual)[/bold]",
            title="📑 Income Statement",
            border_style="green"
        ))

        key_items = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']

        for item in key_items:
            if item in income.index:
                console.print(f"\n[cyan]{item}:[/cyan]")
                for col in income.columns[:4]:  # Last 4 years
                    value = income.loc[item, col]
                    if value and value != 0:
                        formatted = f"₹{abs(value)/10000000:,.2f} Cr" if abs(value) >= 10000000 else f"₹{value:,.2f}"
                        console.print(f"  {col.strftime('%Y')}: {formatted}")

    # Balance Sheet
    if not statements['balance_sheet'].empty:
        balance = statements['balance_sheet']

        console.print(Panel(
            "[bold]Key Balance Sheet Items (Annual)[/bold]",
            title="📑 Balance Sheet",
            border_style="yellow"
        ))

        key_items = ['Total Assets', 'Total Liabilities Net Minority Interest', 'Stockholders Equity']

        for item in key_items:
            if item in balance.index:
                console.print(f"\n[cyan]{item}:[/cyan]")
                for col in balance.columns[:4]:
                    value = balance.loc[item, col]
                    if value and value != 0:
                        formatted = f"₹{abs(value)/10000000:,.2f} Cr" if abs(value) >= 10000000 else f"₹{value:,.2f}"
                        console.print(f"  {col.strftime('%Y')}: {formatted}")


def main():
    """Main showcase function."""
    console.print(Panel("""
[bold cyan]🇮🇳 INDIAN STOCK MARKET TERMINAL - COMPLETE DATA SHOWCASE 🇮🇳[/bold cyan]

This demonstration shows ALL the data fetching capabilities
including real-time prices, fundamentals, and financial statements.

[dim]Time: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S IST") + """[/dim]
""", border_style="blue"))

    # 1. Explain data fetching methods
    showcase_data_fetching_methods()

    # 2. Real-time data
    showcase_realtime_data()

    # 3. Fundamentals
    showcase_fundamentals()

    # 4. Market indices
    showcase_market_indices()

    # 5. Historical data
    showcase_historical_data()

    # 6. Financial statements
    showcase_financial_statements()

    console.print("\n" + "=" * 80)
    console.print("[bold green]SHOWCASE COMPLETE![/bold green]")
    console.print("=" * 80)
    console.print("""
[cyan]To run the interactive terminal:[/cyan]
  python terminal.py

[cyan]To use in your own code:[/cyan]
  from data_fetcher import IndianStockDataFetcher
  fetcher = IndianStockDataFetcher()
  data = fetcher.get_realtime_price("RELIANCE")
  fundamentals = fetcher.get_fundamentals("TCS")
""")


if __name__ == "__main__":
    main()
