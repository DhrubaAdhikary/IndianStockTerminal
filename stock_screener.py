"""
Stock Screener Module
=====================
Provides screening and filtering capabilities for Indian stocks.

Features:
- Custom filter queries
- Pre-built screener templates
- Multi-criteria filtering
- Sorted results
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from data_fetcher import IndianStockDataFetcher


class Operator(Enum):
    """Filter operators."""
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "="
    NEQ = "!="


@dataclass
class FilterCondition:
    """A single filter condition."""
    metric: str
    operator: Operator
    value: float

    def evaluate(self, stock_value: float) -> bool:
        """Evaluate if stock passes this condition."""
        if stock_value is None or pd.isna(stock_value):
            return False

        if self.operator == Operator.GT:
            return stock_value > self.value
        elif self.operator == Operator.GTE:
            return stock_value >= self.value
        elif self.operator == Operator.LT:
            return stock_value < self.value
        elif self.operator == Operator.LTE:
            return stock_value <= self.value
        elif self.operator == Operator.EQ:
            return stock_value == self.value
        elif self.operator == Operator.NEQ:
            return stock_value != self.value
        return False


class StockScreener:
    """
    Screen stocks based on fundamental criteria.
    """

    # Mapping of user-friendly names to data keys
    METRIC_MAPPING = {
        # Valuation
        "market_cap": ("valuation", "market_cap"),
        "market_capitalization": ("valuation", "market_cap"),
        "pe_ratio": ("valuation", "pe_ratio"),
        "pe": ("valuation", "pe_ratio"),
        "p/e": ("valuation", "pe_ratio"),
        "pb_ratio": ("valuation", "price_to_book"),
        "p/b": ("valuation", "price_to_book"),
        "price_to_book": ("valuation", "price_to_book"),
        "ev_ebitda": ("valuation", "ev_to_ebitda"),
        "ev/ebitda": ("valuation", "ev_to_ebitda"),
        "peg_ratio": ("valuation", "peg_ratio"),
        "peg": ("valuation", "peg_ratio"),

        # Profitability
        "profit_margin": ("profitability", "profit_margin"),
        "opm": ("profitability", "operating_margin"),
        "operating_margin": ("profitability", "operating_margin"),
        "gross_margin": ("profitability", "gross_margin"),
        "roe": ("profitability", "return_on_equity"),
        "return_on_equity": ("profitability", "return_on_equity"),
        "roa": ("profitability", "return_on_assets"),
        "return_on_assets": ("profitability", "return_on_assets"),
        "roce": ("profitability", "return_on_equity"),  # Approximation

        # Financial Health
        "debt_to_equity": ("financial_health", "debt_to_equity"),
        "d/e": ("financial_health", "debt_to_equity"),
        "current_ratio": ("financial_health", "current_ratio"),
        "quick_ratio": ("financial_health", "quick_ratio"),

        # Dividends
        "dividend_yield": ("dividends", "dividend_yield"),
        "payout_ratio": ("dividends", "payout_ratio"),

        # Per Share
        "eps": ("per_share", "eps_ttm"),
        "book_value": ("per_share", "book_value"),

        # Price
        "price": ("price", "current_price"),
        "current_price": ("price", "current_price"),
    }

    # Pre-built screener templates
    TEMPLATES = {
        "high_growth": {
            "name": "High Growth Stocks",
            "description": "Companies with strong revenue and profit growth",
            "filters": [
                ("market_cap", ">", 500),  # > 500 Cr
                ("roe", ">", 15),
                ("profit_margin", ">", 10),
            ]
        },
        "value_picks": {
            "name": "Value Picks",
            "description": "Undervalued stocks with strong fundamentals",
            "filters": [
                ("pe_ratio", "<", 15),
                ("pb_ratio", "<", 2),
                ("roe", ">", 12),
                ("debt_to_equity", "<", 1),
            ]
        },
        "dividend_champions": {
            "name": "Dividend Champions",
            "description": "High dividend yield with sustainable payouts",
            "filters": [
                ("dividend_yield", ">", 2),
                ("payout_ratio", "<", 70),
                ("profit_margin", ">", 10),
            ]
        },
        "low_debt": {
            "name": "Low Debt Companies",
            "description": "Companies with minimal debt",
            "filters": [
                ("debt_to_equity", "<", 0.5),
                ("current_ratio", ">", 1.5),
                ("roe", ">", 10),
            ]
        },
        "quality_stocks": {
            "name": "Quality Stocks",
            "description": "High quality companies with consistent performance",
            "filters": [
                ("market_cap", ">", 1000),
                ("roe", ">", 15),
                ("opm", ">", 15),
                ("debt_to_equity", "<", 1.5),
                ("roa", ">", 10),
            ]
        },
        "penny_stocks": {
            "name": "Penny Stocks",
            "description": "Low price stocks (high risk)",
            "filters": [
                ("price", "<", 50),
                ("market_cap", "<", 500),
            ]
        },
        "large_cap_safe": {
            "name": "Large Cap Safe",
            "description": "Large cap stocks with stable fundamentals",
            "filters": [
                ("market_cap", ">", 20000),
                ("debt_to_equity", "<", 1),
                ("roe", ">", 12),
            ]
        },
    }

    def __init__(self):
        self.fetcher = IndianStockDataFetcher(exchange="NSE")
        self.stock_universe = list(self.fetcher.POPULAR_STOCKS.keys())

    def set_universe(self, symbols: List[str]):
        """Set the stock universe to screen from."""
        self.stock_universe = [s.upper() for s in symbols]

    def add_to_universe(self, symbols: List[str]):
        """Add stocks to the universe."""
        for s in symbols:
            if s.upper() not in self.stock_universe:
                self.stock_universe.append(s.upper())

    def _parse_percent(self, value: Any) -> Optional[float]:
        """Parse percentage string to float."""
        if value is None or value == "N/A":
            return None
        if isinstance(value, str):
            return float(value.replace("%", ""))
        return float(value)

    def _get_metric_value(self, fundamentals: Dict, metric: str) -> Optional[float]:
        """Extract metric value from fundamentals data."""
        metric_lower = metric.lower().replace(" ", "_")

        if metric_lower not in self.METRIC_MAPPING:
            return None

        category, key = self.METRIC_MAPPING[metric_lower]

        if category == "price":
            # Get from price data
            return fundamentals.get("current_price")

        category_data = fundamentals.get(category, {})
        value = category_data.get(key)

        # Handle percentage strings
        if isinstance(value, str) and "%" in value:
            return self._parse_percent(value)

        # Handle "Cr" formatted values
        if isinstance(value, str) and "Cr" in value:
            return float(value.replace("₹", "").replace("Cr", "").replace(",", "").strip())

        return value if value != "N/A" else None

    def screen(
        self,
        filters: List[tuple],
        sort_by: str = "market_cap",
        ascending: bool = False,
        limit: int = 50
    ) -> pd.DataFrame:
        """
        Screen stocks based on filter criteria.

        Args:
            filters: List of tuples (metric, operator, value)
                     e.g., [("pe_ratio", "<", 20), ("roe", ">", 15)]
            sort_by: Metric to sort results by
            ascending: Sort order
            limit: Maximum number of results

        Returns:
            DataFrame with screening results
        """
        results = []

        for symbol in self.stock_universe:
            try:
                # Get fundamentals
                fund = self.fetcher.get_fundamentals(symbol)
                price_data = self.fetcher.get_realtime_price(symbol)

                if "error" in fund or "error" in price_data:
                    continue

                # Add price data to fundamentals for unified access
                fund["current_price"] = price_data.get("current_price", 0)
                fund["change_percent"] = price_data.get("change_percent", 0)

                # Check all filters
                passes_all = True
                for metric, op, value in filters:
                    metric_value = self._get_metric_value(fund, metric)

                    if metric_value is None:
                        passes_all = False
                        break

                    # Parse operator
                    if op == ">":
                        operator = Operator.GT
                    elif op == ">=":
                        operator = Operator.GTE
                    elif op == "<":
                        operator = Operator.LT
                    elif op == "<=":
                        operator = Operator.LTE
                    elif op == "=":
                        operator = Operator.EQ
                    else:
                        operator = Operator.GT

                    condition = FilterCondition(metric, operator, value)
                    if not condition.evaluate(metric_value):
                        passes_all = False
                        break

                if passes_all:
                    # Extract key metrics for display
                    result = {
                        "symbol": symbol,
                        "company": fund.get("company_name", symbol),
                        "sector": fund.get("sector", "N/A"),
                        "price": price_data.get("current_price", 0),
                        "change_pct": price_data.get("change_percent", 0),
                        "market_cap": fund.get("valuation", {}).get("market_cap", 0),
                        "market_cap_fmt": fund.get("valuation", {}).get("market_cap_formatted", "N/A"),
                        "pe_ratio": fund.get("valuation", {}).get("pe_ratio", 0),
                        "pb_ratio": fund.get("valuation", {}).get("price_to_book", 0),
                        "roe": self._parse_percent(fund.get("profitability", {}).get("return_on_equity", "0%")),
                        "roa": self._parse_percent(fund.get("profitability", {}).get("return_on_assets", "0%")),
                        "opm": self._parse_percent(fund.get("profitability", {}).get("operating_margin", "0%")),
                        "profit_margin": self._parse_percent(fund.get("profitability", {}).get("profit_margin", "0%")),
                        "debt_to_equity": fund.get("financial_health", {}).get("debt_to_equity", 0),
                        "current_ratio": fund.get("financial_health", {}).get("current_ratio", 0),
                        "dividend_yield": self._parse_percent(fund.get("dividends", {}).get("dividend_yield", "0%")),
                        "eps": fund.get("per_share", {}).get("eps_ttm", 0),
                        "book_value": fund.get("per_share", {}).get("book_value", 0),
                    }
                    results.append(result)

            except Exception as e:
                continue

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Sort
        sort_col = sort_by.lower().replace(" ", "_")
        if sort_col in df.columns:
            df = df.sort_values(by=sort_col, ascending=ascending)

        return df.head(limit).reset_index(drop=True)

    def screen_template(self, template_name: str, limit: int = 50) -> pd.DataFrame:
        """Screen using a pre-built template."""
        if template_name not in self.TEMPLATES:
            raise ValueError(f"Unknown template: {template_name}")

        template = self.TEMPLATES[template_name]
        return self.screen(template["filters"], limit=limit)

    def parse_query(self, query: str) -> List[tuple]:
        """
        Parse a natural language query into filter conditions.

        Example:
            "Market Cap > 500 AND PE < 20 AND ROE > 15"

        Returns:
            List of filter tuples
        """
        filters = []

        # Split by AND
        conditions = query.upper().replace("AND", "&").split("&")

        for condition in conditions:
            condition = condition.strip()
            if not condition:
                continue

            # Parse operators
            for op in [">=", "<=", ">", "<", "=", "!="]:
                if op in condition:
                    parts = condition.split(op)
                    if len(parts) == 2:
                        metric = parts[0].strip().lower().replace(" ", "_")
                        try:
                            value = float(parts[1].strip().replace("%", ""))
                            filters.append((metric, op, value))
                        except ValueError:
                            pass
                    break

        return filters

    def get_available_metrics(self) -> List[str]:
        """Get list of available metrics for screening."""
        return list(self.METRIC_MAPPING.keys())

    def get_templates(self) -> Dict[str, Dict]:
        """Get available screener templates."""
        return self.TEMPLATES


# Extended stock universe for screening
EXTENDED_UNIVERSE = [
    # Nifty 50
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
    "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "TITAN",
    "SUNPHARMA", "BAJFINANCE", "WIPRO", "HCLTECH", "TATAMOTORS",
    "TATASTEEL", "ADANIENT", "POWERGRID", "NTPC", "ONGC",
    "ULTRACEMCO", "JSWSTEEL", "BAJAJFINSV", "TECHM", "INDUSINDBK",
    "NESTLEIND", "GRASIM", "HDFCLIFE", "DRREDDY", "COALINDIA",
    "SBILIFE", "CIPLA", "BRITANNIA", "EICHERMOT", "APOLLOHOSP",
    "DIVISLAB", "BPCL", "TATACONSUM", "HEROMOTOCO", "M&M",
    "ADANIPORTS", "HINDALCO", "BAJAJ-AUTO", "SHRIRAMFIN", "LTIM",

    # Additional popular stocks
    "VEDL", "ZOMATO", "PAYTM", "NYKAA", "IRCTC",
    "TATAPOWER", "ADANIGREEN", "ADANIPOWER", "JINDALSTEL", "SAIL",
    "BANKBARODA", "PNB", "CANBK", "IDFCFIRSTB", "FEDERALBNK",
    "PIDILITIND", "HAVELLS", "VOLTAS", "CROMPTON", "BLUESTARCO",
    "DMART", "TRENT", "PAGEIND", "MUTHOOTFIN", "CHOLAFIN",
    "PFC", "RECLTD", "IRFC", "NHPC", "SJVN",
    "HAL", "BEL", "BHEL", "COCHINSHIP", "MAZAGON",
    "POLYCAB", "KPITTECH", "PERSISTENT", "COFORGE", "MPHASIS",
]
