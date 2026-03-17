"""
Backtesting Engine
==================
Backtests trading strategies and calculates performance metrics.

Risk Metrics Included:
- Sharpe Ratio
- Sortino Ratio (only penalizes downside)
- Calmar Ratio (return vs drawdown)
- Omega Ratio (captures entire distribution)
- Information Ratio (alpha consistency)
- Upside Capture Ratio
- Maximum Drawdown
- Win Rate
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from trading_strategies import TradingStrategies, StrategySignal
from technical_analysis import TechnicalAnalysis


@dataclass
class BacktestResult:
    """Results from a backtest."""
    strategy_name: str
    symbol: str
    period: str

    # Trade Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    profit_factor: float

    # Return Metrics
    total_return: float
    annual_return: float
    benchmark_return: float
    alpha: float

    # Risk Metrics
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    information_ratio: float
    upside_capture: float
    downside_capture: float

    # Drawdown
    max_drawdown: float
    avg_drawdown: float
    max_drawdown_duration: int  # days

    # Trade Details
    trades: List[Dict]
    equity_curve: List[float]
    dates: List[datetime]


class Backtester:
    """
    Backtesting engine for trading strategies.
    """

    def __init__(self, initial_capital: float = 100000, risk_free_rate: float = 0.06):
        """
        Initialize backtester.

        Args:
            initial_capital: Starting capital in INR
            risk_free_rate: Annual risk-free rate (default 6% for India)
        """
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        self.strategies = TradingStrategies()

    def backtest_strategy(
        self,
        df: pd.DataFrame,
        strategy_func,
        symbol: str = "",
        holding_period: int = 20,
        stop_loss_pct: float = 0.08,
        take_profit_pct: float = 0.20
    ) -> BacktestResult:
        """
        Backtest a single strategy on historical data.

        Args:
            df: Historical OHLCV data
            strategy_func: Strategy function to test
            symbol: Stock symbol
            holding_period: Max holding period in days
            stop_loss_pct: Stop loss percentage
            take_profit_pct: Take profit percentage

        Returns:
            BacktestResult with all metrics
        """
        df = TechnicalAnalysis.add_all_indicators(df.copy())

        trades = []
        equity = self.initial_capital
        equity_curve = [equity]
        dates = [df.index[0]]

        position = None
        position_entry = None
        position_entry_price = 0

        # Walk through data
        for i in range(200, len(df) - 1):  # Start after enough data for indicators
            current_date = df.index[i]
            current_price = df['Close'].iloc[i]
            current_data = df.iloc[:i+1]

            # Check for exit if in position
            if position is not None:
                days_held = i - position_entry
                pnl_pct = (current_price - position_entry_price) / position_entry_price

                # Exit conditions
                exit_signal = False
                exit_reason = ""

                if pnl_pct <= -stop_loss_pct:
                    exit_signal = True
                    exit_reason = "Stop Loss"
                elif pnl_pct >= take_profit_pct:
                    exit_signal = True
                    exit_reason = "Take Profit"
                elif days_held >= holding_period:
                    exit_signal = True
                    exit_reason = "Holding Period"

                if exit_signal:
                    # Close position
                    exit_price = current_price
                    pnl = (exit_price - position_entry_price) / position_entry_price * 100

                    trades.append({
                        'entry_date': df.index[position_entry],
                        'exit_date': current_date,
                        'entry_price': position_entry_price,
                        'exit_price': exit_price,
                        'pnl_pct': pnl,
                        'days_held': days_held,
                        'exit_reason': exit_reason,
                        'win': pnl > 0
                    })

                    # Update equity
                    equity *= (1 + pnl / 100)
                    position = None

            # Check for entry if not in position
            if position is None:
                try:
                    result = strategy_func(current_data, symbol)

                    if result.signal in [StrategySignal.BUY, StrategySignal.STRONG_BUY]:
                        if result.score >= 60:  # Only take high conviction signals
                            position = "LONG"
                            position_entry = i
                            position_entry_price = current_price
                except:
                    pass

            equity_curve.append(equity)
            dates.append(current_date)

        # Close any open position at end
        if position is not None:
            exit_price = df['Close'].iloc[-1]
            pnl = (exit_price - position_entry_price) / position_entry_price * 100
            trades.append({
                'entry_date': df.index[position_entry],
                'exit_date': df.index[-1],
                'entry_price': position_entry_price,
                'exit_price': exit_price,
                'pnl_pct': pnl,
                'days_held': len(df) - position_entry,
                'exit_reason': 'End of Period',
                'win': pnl > 0
            })
            equity *= (1 + pnl / 100)
            equity_curve.append(equity)
            dates.append(df.index[-1])

        # Calculate metrics
        return self._calculate_metrics(
            trades=trades,
            equity_curve=equity_curve,
            dates=dates,
            df=df,
            strategy_name=strategy_func.__name__,
            symbol=symbol
        )

    def _calculate_metrics(
        self,
        trades: List[Dict],
        equity_curve: List[float],
        dates: List,
        df: pd.DataFrame,
        strategy_name: str,
        symbol: str
    ) -> BacktestResult:
        """Calculate all performance metrics."""

        # Trade statistics
        total_trades = len(trades)
        if total_trades == 0:
            return self._empty_result(strategy_name, symbol)

        winning_trades = sum(1 for t in trades if t['win'])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades * 100

        wins = [t['pnl_pct'] for t in trades if t['win']]
        losses = [t['pnl_pct'] for t in trades if not t['win']]

        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = min(losses) if losses else 0

        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        # Return metrics
        total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital * 100
        days = (dates[-1] - dates[0]).days if len(dates) > 1 else 1
        annual_return = total_return * (365 / days) if days > 0 else 0

        # Benchmark return (buy and hold)
        benchmark_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0] * 100

        # Alpha
        alpha = annual_return - benchmark_return

        # Daily returns for risk metrics
        returns = pd.Series(equity_curve).pct_change().dropna()
        benchmark_returns = df['Close'].pct_change().dropna()

        # Risk metrics
        sharpe_ratio = self._calculate_sharpe(returns)
        sortino_ratio = self._calculate_sortino(returns)
        max_drawdown, avg_drawdown, max_dd_duration = self._calculate_drawdown(equity_curve)
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        omega_ratio = self._calculate_omega(returns)
        information_ratio = self._calculate_information_ratio(returns, benchmark_returns)
        upside_capture, downside_capture = self._calculate_capture_ratios(returns, benchmark_returns)

        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            period=f"{dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}",
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            profit_factor=profit_factor,
            total_return=total_return,
            annual_return=annual_return,
            benchmark_return=benchmark_return,
            alpha=alpha,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            omega_ratio=omega_ratio,
            information_ratio=information_ratio,
            upside_capture=upside_capture,
            downside_capture=downside_capture,
            max_drawdown=max_drawdown,
            avg_drawdown=avg_drawdown,
            max_drawdown_duration=max_dd_duration,
            trades=trades,
            equity_curve=equity_curve,
            dates=dates
        )

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """Calculate Sharpe Ratio."""
        if len(returns) < 2:
            return 0
        excess_returns = returns - self.risk_free_rate / 252
        if returns.std() == 0:
            return 0
        return np.sqrt(252) * excess_returns.mean() / returns.std()

    def _calculate_sortino(self, returns: pd.Series) -> float:
        """
        Calculate Sortino Ratio.
        Only penalizes downside volatility.

        Formula: (Return - RiskFree) / DownsideDeviation
        """
        if len(returns) < 2:
            return 0

        excess_returns = returns - self.risk_free_rate / 252
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0

        downside_std = np.sqrt(np.mean(downside_returns ** 2))
        return np.sqrt(252) * excess_returns.mean() / downside_std

    def _calculate_drawdown(self, equity_curve: List[float]) -> Tuple[float, float, int]:
        """Calculate maximum drawdown, average drawdown, and duration."""
        equity = pd.Series(equity_curve)
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max * 100

        max_drawdown = drawdown.min()
        avg_drawdown = drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0

        # Calculate max drawdown duration
        in_drawdown = drawdown < 0
        if not in_drawdown.any():
            max_duration = 0
        else:
            # Find consecutive drawdown periods
            drawdown_periods = []
            current_period = 0
            for is_dd in in_drawdown:
                if is_dd:
                    current_period += 1
                else:
                    if current_period > 0:
                        drawdown_periods.append(current_period)
                    current_period = 0
            if current_period > 0:
                drawdown_periods.append(current_period)
            max_duration = max(drawdown_periods) if drawdown_periods else 0

        return max_drawdown, avg_drawdown, max_duration

    def _calculate_omega(self, returns: pd.Series, threshold: float = 0) -> float:
        """
        Calculate Omega Ratio.

        Omega = Probability(Return > threshold) / Probability(Return < threshold)
        Captures entire return distribution.
        """
        if len(returns) < 2:
            return 0

        gains = returns[returns > threshold].sum()
        losses = abs(returns[returns < threshold].sum())

        if losses == 0:
            return float('inf') if gains > 0 else 0

        return gains / losses

    def _calculate_information_ratio(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calculate Information Ratio.

        IR = Alpha / Tracking Error
        Measures consistency of alpha generation.
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0

        # Align series
        min_len = min(len(returns), len(benchmark_returns))
        returns = returns.tail(min_len)
        benchmark_returns = benchmark_returns.tail(min_len)

        active_returns = returns.values - benchmark_returns.values
        tracking_error = np.std(active_returns)

        if tracking_error == 0:
            return 0

        return np.sqrt(252) * np.mean(active_returns) / tracking_error

    def _calculate_capture_ratios(self, returns: pd.Series, benchmark_returns: pd.Series) -> Tuple[float, float]:
        """
        Calculate Upside and Downside Capture Ratios.

        Upside Capture = Strategy Return in Up Markets / Benchmark Return in Up Markets
        """
        if len(returns) < 2 or len(benchmark_returns) < 2:
            return 0, 0

        min_len = min(len(returns), len(benchmark_returns))
        returns = returns.tail(min_len).values
        benchmark_returns = benchmark_returns.tail(min_len).values

        # Up markets
        up_mask = benchmark_returns > 0
        if up_mask.sum() > 0:
            upside_capture = returns[up_mask].mean() / benchmark_returns[up_mask].mean() * 100
        else:
            upside_capture = 0

        # Down markets
        down_mask = benchmark_returns < 0
        if down_mask.sum() > 0:
            downside_capture = returns[down_mask].mean() / benchmark_returns[down_mask].mean() * 100
        else:
            downside_capture = 0

        return upside_capture, downside_capture

    def _empty_result(self, strategy_name: str, symbol: str) -> BacktestResult:
        """Return empty result for strategies with no trades."""
        return BacktestResult(
            strategy_name=strategy_name,
            symbol=symbol,
            period="N/A",
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0,
            avg_win=0,
            avg_loss=0,
            largest_win=0,
            largest_loss=0,
            profit_factor=0,
            total_return=0,
            annual_return=0,
            benchmark_return=0,
            alpha=0,
            sharpe_ratio=0,
            sortino_ratio=0,
            calmar_ratio=0,
            omega_ratio=0,
            information_ratio=0,
            upside_capture=0,
            downside_capture=0,
            max_drawdown=0,
            avg_drawdown=0,
            max_drawdown_duration=0,
            trades=[],
            equity_curve=[self.initial_capital],
            dates=[]
        )

    def backtest_all_strategies(self, df: pd.DataFrame, symbol: str = "") -> Dict[str, BacktestResult]:
        """Backtest all strategies on the same data."""
        strategies = TradingStrategies()

        strategy_funcs = {
            "200-Day Trend + ATH": strategies.strategy_200dma_ath_breakout,
            "52-Week High Momentum": strategies.strategy_52week_high_momentum,
            "VCP (Minervini)": strategies.strategy_vcp,
            "Cup and Handle": strategies.strategy_cup_and_handle,
            "Donchian Turtle": strategies.strategy_donchian_turtle,
            "MA Momentum Stack": strategies.strategy_ma_momentum_stack,
            "Relative Strength": strategies.strategy_relative_strength,
            "Bollinger Squeeze": strategies.strategy_bollinger_squeeze,
            "Base Breakout": strategies.strategy_base_breakout,
            "Stage Analysis": strategies.strategy_stage_analysis,
        }

        results = {}
        for name, func in strategy_funcs.items():
            try:
                results[name] = self.backtest_strategy(df, func, symbol)
            except Exception as e:
                results[name] = self._empty_result(name, symbol)

        return results


def format_backtest_result(result: BacktestResult) -> Dict[str, Any]:
    """Format backtest result for display."""
    return {
        "Strategy": result.strategy_name,
        "Symbol": result.symbol,
        "Period": result.period,

        # Trade Stats
        "Total Trades": result.total_trades,
        "Win Rate": f"{result.win_rate:.1f}%",
        "Avg Win": f"{result.avg_win:.2f}%",
        "Avg Loss": f"{result.avg_loss:.2f}%",
        "Profit Factor": f"{result.profit_factor:.2f}",

        # Returns
        "Total Return": f"{result.total_return:.2f}%",
        "Annual Return": f"{result.annual_return:.2f}%",
        "Alpha": f"{result.alpha:.2f}%",

        # Risk Metrics
        "Sharpe Ratio": f"{result.sharpe_ratio:.2f}",
        "Sortino Ratio": f"{result.sortino_ratio:.2f}",
        "Calmar Ratio": f"{result.calmar_ratio:.2f}",
        "Omega Ratio": f"{result.omega_ratio:.2f}",
        "Information Ratio": f"{result.information_ratio:.2f}",

        # Capture
        "Upside Capture": f"{result.upside_capture:.1f}%",
        "Downside Capture": f"{result.downside_capture:.1f}%",

        # Drawdown
        "Max Drawdown": f"{result.max_drawdown:.2f}%",
        "Max DD Duration": f"{result.max_drawdown_duration} days",
    }
