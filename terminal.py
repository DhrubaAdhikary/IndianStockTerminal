#!/usr/bin/env python3
"""
Indian Stock Market Terminal - Bloomberg-style Interface
=========================================================
A comprehensive terminal for viewing Indian stock market data.

Features:
- Real-time stock prices (NSE/BSE)
- Company fundamentals and financials
- Market indices (NIFTY 50, SENSEX, Bank NIFTY)
- Historical price charts
- Sector analysis
- Watchlist management
"""

import sys
from datetime import datetime
from typing import Optional
import pandas as pd

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt
from rich.style import Style

try:
    import plotext as plt
except ImportError:
    plt = None

from data_fetcher import IndianStockDataFetcher


class IndianStockTerminal:
    """Bloomberg-style terminal for Indian Stock Market."""

    def __init__(self):
        self.console = Console()
        self.fetcher = IndianStockDataFetcher(exchange="NSE")
        self.watchlist = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

    def print_header(self):
        """Print the terminal header."""
        header = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🇮🇳 INDIAN STOCK MARKET TERMINAL 🇮🇳                        ║
║                     Bloomberg-style Financial Data                           ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        self.console.print(header, style="bold blue")
        self.console.print(f"  📅 {datetime.now().strftime('%A, %B %d, %Y %H:%M:%S IST')}", style="dim")
        self.console.print()

    def display_market_overview(self):
        """Display market indices overview."""
        self.console.print("\n[bold cyan]═══ MARKET OVERVIEW ═══[/bold cyan]\n")

        indices = ["NIFTY50", "SENSEX", "BANKNIFTY"]

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Index", style="cyan", width=15)
        table.add_column("Value", justify="right", width=12)
        table.add_column("Change", justify="right", width=12)
        table.add_column("% Change", justify="right", width=10)
        table.add_column("Day High", justify="right", width=12)
        table.add_column("Day Low", justify="right", width=12)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Fetching market data...", total=None)

            for index_name in indices:
                data = self.fetcher.get_index_data(index_name)

                if "error" not in data:
                    change_style = "green" if data['change'] >= 0 else "red"
                    change_symbol = "▲" if data['change'] >= 0 else "▼"

                    table.add_row(
                        index_name,
                        f"{data['current_price']:,.2f}",
                        f"[{change_style}]{change_symbol} {abs(data['change']):,.2f}[/{change_style}]",
                        f"[{change_style}]{data['change_percent']:+.2f}%[/{change_style}]",
                        f"{data['day_high']:,.2f}",
                        f"{data['day_low']:,.2f}",
                    )
                else:
                    table.add_row(index_name, "Error", "-", "-", "-", "-")

        self.console.print(table)

    def display_stock_quote(self, symbol: str):
        """Display detailed stock quote."""
        self.console.print(f"\n[bold cyan]═══ STOCK QUOTE: {symbol.upper()} ═══[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Fetching data for {symbol}...", total=None)
            data = self.fetcher.get_realtime_price(symbol)

        if "error" in data:
            self.console.print(f"[red]Error: {data['error']}[/red]")
            return

        # Price Panel
        change_style = "green" if data['change'] >= 0 else "red"
        change_symbol = "▲" if data['change'] >= 0 else "▼"

        price_text = Text()
        price_text.append(f"₹{data['current_price']:,.2f}", style="bold white on blue")
        price_text.append(f"  {change_symbol} ₹{abs(data['change']):,.2f} ({data['change_percent']:+.2f}%)", style=change_style)

        # Create info table
        info_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        info_table.add_column("Label", style="dim")
        info_table.add_column("Value", style="bold")

        info_table.add_row("Company", data['company_name'])
        info_table.add_row("Exchange", data['exchange'])
        info_table.add_row("Previous Close", f"₹{data['previous_close']:,.2f}")
        info_table.add_row("Open", f"₹{data['open']:,.2f}")
        info_table.add_row("Day High", f"₹{data['day_high']:,.2f}")
        info_table.add_row("Day Low", f"₹{data['day_low']:,.2f}")
        info_table.add_row("52W High", f"₹{data['fifty_two_week_high']:,.2f}")
        info_table.add_row("52W Low", f"₹{data['fifty_two_week_low']:,.2f}")
        info_table.add_row("Volume", f"{data['volume']:,}")
        info_table.add_row("Avg Volume", f"{data['average_volume']:,}")
        info_table.add_row("Market State", data['market_state'])
        info_table.add_row("Last Updated", data['last_updated'])

        panel = Panel(
            info_table,
            title=f"[bold]{symbol.upper()}[/bold] - {price_text}",
            border_style="blue",
        )
        self.console.print(panel)

    def display_fundamentals(self, symbol: str):
        """Display company fundamentals."""
        self.console.print(f"\n[bold cyan]═══ FUNDAMENTALS: {symbol.upper()} ═══[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Fetching fundamentals for {symbol}...", total=None)
            data = self.fetcher.get_fundamentals(symbol)

        if "error" in data:
            self.console.print(f"[red]Error: {data['error']}[/red]")
            return

        # Company Info Panel
        company_panel = Panel(
            f"""[bold]{data['company_name']}[/bold]

[cyan]Sector:[/cyan] {data['sector']}
[cyan]Industry:[/cyan] {data['industry']}
[cyan]Website:[/cyan] {data['website']}

[dim]{data['description']}[/dim]""",
            title="Company Profile",
            border_style="blue",
        )
        self.console.print(company_panel)

        # Valuation Table
        val_table = Table(title="📊 Valuation Metrics", box=box.ROUNDED)
        val_table.add_column("Metric", style="cyan")
        val_table.add_column("Value", justify="right")

        val = data['valuation']
        val_table.add_row("Market Cap", f"₹{val['market_cap_formatted']}")
        val_table.add_row("Enterprise Value", f"₹{val['enterprise_value_formatted']}")
        val_table.add_row("P/E Ratio (TTM)", str(val['pe_ratio']))
        val_table.add_row("Forward P/E", str(val['forward_pe']))
        val_table.add_row("PEG Ratio", str(val['peg_ratio']))
        val_table.add_row("Price/Book", str(val['price_to_book']))
        val_table.add_row("Price/Sales", str(val['price_to_sales']))
        val_table.add_row("EV/EBITDA", str(val['ev_to_ebitda']))

        # Profitability Table
        prof_table = Table(title="💰 Profitability", box=box.ROUNDED)
        prof_table.add_column("Metric", style="cyan")
        prof_table.add_column("Value", justify="right")

        prof = data['profitability']
        prof_table.add_row("Profit Margin", prof['profit_margin'])
        prof_table.add_row("Operating Margin", prof['operating_margin'])
        prof_table.add_row("Gross Margin", prof['gross_margin'])
        prof_table.add_row("EBITDA Margin", prof['ebitda_margin'])
        prof_table.add_row("Return on Equity", prof['return_on_equity'])
        prof_table.add_row("Return on Assets", prof['return_on_assets'])

        # Financial Health Table
        health_table = Table(title="🏦 Financial Health", box=box.ROUNDED)
        health_table.add_column("Metric", style="cyan")
        health_table.add_column("Value", justify="right")

        health = data['financial_health']
        health_table.add_row("Total Cash", f"₹{health['total_cash']}")
        health_table.add_row("Total Debt", f"₹{health['total_debt']}")
        health_table.add_row("Debt/Equity", str(health['debt_to_equity']))
        health_table.add_row("Current Ratio", str(health['current_ratio']))
        health_table.add_row("Quick Ratio", str(health['quick_ratio']))

        # Per Share Table
        share_table = Table(title="📈 Per Share Data", box=box.ROUNDED)
        share_table.add_column("Metric", style="cyan")
        share_table.add_column("Value", justify="right")

        ps = data['per_share']
        share_table.add_row("EPS (TTM)", f"₹{ps['eps_ttm']}")
        share_table.add_row("EPS (Forward)", f"₹{ps['eps_forward']}")
        share_table.add_row("Book Value", f"₹{ps['book_value']}")
        share_table.add_row("Revenue/Share", f"₹{ps['revenue_per_share']}")

        # Dividend Table
        div_table = Table(title="💵 Dividends", box=box.ROUNDED)
        div_table.add_column("Metric", style="cyan")
        div_table.add_column("Value", justify="right")

        div = data['dividends']
        div_table.add_row("Dividend Rate", f"₹{div['dividend_rate']}")
        div_table.add_row("Dividend Yield", div['dividend_yield'])
        div_table.add_row("Payout Ratio", div['payout_ratio'])

        # Display tables in columns
        self.console.print(Columns([val_table, prof_table]))
        self.console.print(Columns([health_table, share_table, div_table]))

        # Analyst Recommendations
        analyst = data['analyst']
        if analyst['target_mean']:
            analyst_panel = Panel(
                f"""[bold]Analyst Consensus:[/bold] {analyst['recommendation'].upper()}
[cyan]Price Targets:[/cyan]
  Low: ₹{analyst['target_low']:,.2f}  |  Mean: ₹{analyst['target_mean']:,.2f}  |  High: ₹{analyst['target_high']:,.2f}
[dim]Based on {analyst['num_analysts']} analyst(s)[/dim]""",
                title="📊 Analyst Recommendations",
                border_style="yellow",
            )
            self.console.print(analyst_panel)

    def display_price_chart(self, symbol: str, period: str = "1mo"):
        """Display price chart in terminal."""
        if plt is None:
            self.console.print("[yellow]Install plotext for charts: pip install plotext[/yellow]")
            return

        self.console.print(f"\n[bold cyan]═══ PRICE CHART: {symbol.upper()} ({period}) ═══[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Fetching historical data...", total=None)
            df = self.fetcher.get_historical_data(symbol, period=period)

        if df.empty:
            self.console.print("[red]No data available[/red]")
            return

        # Prepare data - use numeric x-axis to avoid date parsing issues
        prices = df['Close'].tolist()
        x_values = list(range(len(prices)))

        # Get date labels for display
        start_date = df.index[0].strftime("%Y-%m-%d")
        end_date = df.index[-1].strftime("%Y-%m-%d")

        # Calculate stats
        start_price = prices[0]
        end_price = prices[-1]
        change = end_price - start_price
        change_pct = (change / start_price) * 100
        high = max(prices)
        low = min(prices)

        # Plot
        plt.clear_figure()
        plt.plot(x_values, prices, marker="braille")
        plt.title(f"{symbol.upper()} - {start_date} to {end_date}")
        plt.xlabel(f"Trading Days ({len(prices)} days)")
        plt.ylabel("Price (INR)")
        plt.theme("dark")
        plt.plot_size(80, 20)
        plt.show()

        # Print summary below chart
        change_style = "green" if change >= 0 else "red"
        change_symbol = "▲" if change >= 0 else "▼"
        self.console.print(f"\n[bold]Summary:[/bold] {start_date} → {end_date}")
        self.console.print(f"  Open: ₹{start_price:,.2f}  |  Close: ₹{end_price:,.2f}  |  [{change_style}]{change_symbol} {change_pct:+.2f}%[/{change_style}]")
        self.console.print(f"  High: ₹{high:,.2f}  |  Low: ₹{low:,.2f}")

    def display_watchlist(self):
        """Display watchlist with current prices."""
        self.console.print("\n[bold cyan]═══ WATCHLIST ═══[/bold cyan]\n")

        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("Symbol", style="cyan", width=12)
        table.add_column("Company", width=25)
        table.add_column("Price", justify="right", width=12)
        table.add_column("Change", justify="right", width=12)
        table.add_column("% Change", justify="right", width=10)
        table.add_column("Volume", justify="right", width=15)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Fetching watchlist data...", total=None)

            for symbol in self.watchlist:
                data = self.fetcher.get_realtime_price(symbol)

                if "error" not in data:
                    change_style = "green" if data['change'] >= 0 else "red"
                    change_symbol = "▲" if data['change'] >= 0 else "▼"

                    table.add_row(
                        symbol,
                        data['company_name'][:25],
                        f"₹{data['current_price']:,.2f}",
                        f"[{change_style}]{change_symbol} {abs(data['change']):,.2f}[/{change_style}]",
                        f"[{change_style}]{data['change_percent']:+.2f}%[/{change_style}]",
                        f"{data['volume']:,}",
                    )
                else:
                    table.add_row(symbol, "Error", "-", "-", "-", "-")

        self.console.print(table)

    def display_sector_analysis(self):
        """Display sector-wise analysis."""
        self.console.print("\n[bold cyan]═══ SECTOR LEADERS ═══[/bold cyan]\n")

        sectors = {
            "IT": ["TCS", "INFY", "WIPRO", "HCLTECH"],
            "Banking": ["HDFCBANK", "ICICIBANK", "SBIN", "KOTAKBANK", "AXISBANK"],
            "Energy": ["RELIANCE", "ONGC", "NTPC", "POWERGRID"],
            "Auto": ["MARUTI", "TATAMOTORS"],
            "FMCG": ["HINDUNILVR", "ITC"],
        }

        for sector, stocks in sectors.items():
            self.console.print(f"\n[bold yellow]{sector}[/bold yellow]")

            table = Table(box=box.SIMPLE, show_header=True)
            table.add_column("Symbol", style="cyan", width=12)
            table.add_column("Price", justify="right", width=12)
            table.add_column("Change %", justify="right", width=10)

            for symbol in stocks[:3]:  # Top 3 per sector
                data = self.fetcher.get_realtime_price(symbol)
                if "error" not in data:
                    change_style = "green" if data['change'] >= 0 else "red"
                    table.add_row(
                        symbol,
                        f"₹{data['current_price']:,.2f}",
                        f"[{change_style}]{data['change_percent']:+.2f}%[/{change_style}]",
                    )

            self.console.print(table)

    def display_financial_statements(self, symbol: str):
        """Display financial statements."""
        self.console.print(f"\n[bold cyan]═══ FINANCIAL STATEMENTS: {symbol.upper()} ═══[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Fetching financial statements...", total=None)
            statements = self.fetcher.get_financial_statements(symbol)

        # Income Statement
        if not statements['income_statement'].empty:
            self.console.print("\n[bold yellow]Income Statement (Annual)[/bold yellow]")
            income = statements['income_statement']

            # Select key metrics
            key_metrics = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
            for metric in key_metrics:
                if metric in income.index:
                    values = income.loc[metric]
                    self.console.print(f"  {metric}:")
                    for date, value in values.items():
                        if pd.notna(value):
                            formatted = self._format_number(value)
                            self.console.print(f"    {date.strftime('%Y')}: ₹{formatted}")

    def _format_number(self, num: float) -> str:
        """Format number in Indian style."""
        if abs(num) >= 10000000:
            return f"{num/10000000:,.2f} Cr"
        elif abs(num) >= 100000:
            return f"{num/100000:,.2f} L"
        else:
            return f"{num:,.2f}"

    def show_help(self):
        """Show help information."""
        help_text = """
[bold cyan]═══ AVAILABLE COMMANDS ═══[/bold cyan]

[yellow]Market Overview:[/yellow]
  market, overview, m     - Show market indices

[yellow]Stock Data:[/yellow]
  quote <symbol>          - Get stock quote (e.g., quote RELIANCE)
  fund <symbol>           - Get fundamentals (e.g., fund TCS)
  chart <symbol> [period] - Show price chart (periods: 1d,5d,1mo,3mo,6mo,1y)
  fin <symbol>            - Show financial statements

[yellow]Watchlist:[/yellow]
  watchlist, w            - Show watchlist
  add <symbol>            - Add to watchlist
  remove <symbol>         - Remove from watchlist

[yellow]Analysis:[/yellow]
  sectors                 - Show sector analysis

[yellow]Other:[/yellow]
  help, h                 - Show this help
  clear, cls              - Clear screen
  exit, quit, q           - Exit terminal

[dim]Example: quote INFY | fund HDFCBANK | chart TCS 3mo[/dim]
        """
        self.console.print(help_text)

    def run(self):
        """Run the interactive terminal."""
        self.print_header()
        self.display_market_overview()
        self.show_help()

        while True:
            try:
                self.console.print()
                command = Prompt.ask("[bold green]TERMINAL[/bold green]").strip().lower()

                if not command:
                    continue

                parts = command.split()
                cmd = parts[0]
                args = parts[1:] if len(parts) > 1 else []

                if cmd in ["exit", "quit", "q"]:
                    self.console.print("[yellow]Goodbye! Happy Trading![/yellow]")
                    break

                elif cmd in ["help", "h"]:
                    self.show_help()

                elif cmd in ["clear", "cls"]:
                    self.console.clear()
                    self.print_header()

                elif cmd in ["market", "overview", "m"]:
                    self.display_market_overview()

                elif cmd == "quote" and args:
                    self.display_stock_quote(args[0])

                elif cmd == "fund" and args:
                    self.display_fundamentals(args[0])

                elif cmd == "chart" and args:
                    period = args[1] if len(args) > 1 else "1mo"
                    self.display_price_chart(args[0], period)

                elif cmd == "fin" and args:
                    self.display_financial_statements(args[0])

                elif cmd in ["watchlist", "w"]:
                    self.display_watchlist()

                elif cmd == "add" and args:
                    symbol = args[0].upper()
                    if symbol not in self.watchlist:
                        self.watchlist.append(symbol)
                        self.console.print(f"[green]Added {symbol} to watchlist[/green]")
                    else:
                        self.console.print(f"[yellow]{symbol} already in watchlist[/yellow]")

                elif cmd == "remove" and args:
                    symbol = args[0].upper()
                    if symbol in self.watchlist:
                        self.watchlist.remove(symbol)
                        self.console.print(f"[green]Removed {symbol} from watchlist[/green]")
                    else:
                        self.console.print(f"[yellow]{symbol} not in watchlist[/yellow]")

                elif cmd == "sectors":
                    self.display_sector_analysis()

                else:
                    self.console.print(f"[red]Unknown command: {command}. Type 'help' for commands.[/red]")

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")


def main():
    """Main entry point."""
    terminal = IndianStockTerminal()
    terminal.run()


if __name__ == "__main__":
    main()
