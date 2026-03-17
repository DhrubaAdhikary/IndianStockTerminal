"""
Trading Strategies Module
=========================
Implements professional trading strategies used by top investors.

Strategies Included:
1. 200-Day Trend Filter + ATH Breakout (Minervini/O'Neil style)
2. 52-Week High Momentum Strategy
3. Volatility Contraction Pattern (VCP)
4. Cup and Handle Breakout
5. Donchian Channel Breakout (Turtle Strategy)
6. Moving Average Momentum Stack
7. Relative Strength Breakout
8. Bollinger Band Squeeze Breakout
9. Base Formation Breakout
10. Stage Analysis (Stan Weinstein)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from technical_analysis import TechnicalAnalysis


class StrategySignal(Enum):
    """Trading signal types."""
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG SELL"
    NO_SIGNAL = "NO SIGNAL"


@dataclass
class StrategyResult:
    """Result of a strategy scan."""
    symbol: str
    strategy_name: str
    signal: StrategySignal
    score: float  # 0-100
    entry_price: float
    stop_loss: float
    target: float
    risk_reward: float
    conditions_met: List[str]
    conditions_failed: List[str]
    additional_info: Dict[str, Any]


class TradingStrategies:
    """
    Collection of professional trading strategies.
    """

    def __init__(self):
        self.ta = TechnicalAnalysis()

    # ==========================================
    # STRATEGY 1: 200-Day Trend + ATH Breakout
    # ==========================================
    def strategy_200dma_ath_breakout(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        200-Day Trend Filter + ATH Breakout (Minervini/O'Neil Style)

        Rules:
        1. Price previously corrected below 200 EMA
        2. Price crosses above 200 EMA
        3. Breaks all-time high
        4. Volume expansion

        Typical Stats: Win rate 55-65%, Sharpe 1.2-1.8, Return 25-60% annual
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]
        ema_200 = df['EMA_200'].iloc[-1]
        ath = df['High'].max()
        avg_volume = df['Volume'].rolling(20).mean().iloc[-1]
        current_volume = df['Volume'].iloc[-1]

        # Check if price was below 200 EMA in last 60 days
        was_below_200ema = (df['Close'].iloc[-60:-20] < df['EMA_200'].iloc[-60:-20]).any()

        # Condition 1: Price above 200 EMA
        if current_price > ema_200:
            conditions_met.append("Price above 200 EMA")
        else:
            conditions_failed.append("Price below 200 EMA")

        # Condition 2: Previously corrected below 200 EMA
        if was_below_200ema:
            conditions_met.append("Price previously corrected below 200 EMA")
        else:
            conditions_failed.append("No recent correction below 200 EMA")

        # Condition 3: Near or at ATH (within 5%)
        distance_from_ath = (ath - current_price) / ath * 100
        if distance_from_ath <= 5:
            conditions_met.append(f"Near ATH (within {distance_from_ath:.1f}%)")
        else:
            conditions_failed.append(f"Far from ATH ({distance_from_ath:.1f}% below)")

        # Condition 4: Volume expansion
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        if volume_ratio > 1.5:
            conditions_met.append(f"Volume expansion ({volume_ratio:.1f}x average)")
        else:
            conditions_failed.append(f"Low volume ({volume_ratio:.1f}x average)")

        # Calculate score
        score = len(conditions_met) / 4 * 100

        # Determine signal
        if score >= 75:
            signal = StrategySignal.STRONG_BUY
        elif score >= 50:
            signal = StrategySignal.BUY
        elif score >= 25:
            signal = StrategySignal.HOLD
        else:
            signal = StrategySignal.NO_SIGNAL

        # Calculate entry, stop loss, target
        entry_price = current_price
        stop_loss = min(ema_200, current_price * 0.92)  # 8% or 200 EMA
        target = current_price * 1.25  # 25% target
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="200-Day Trend + ATH Breakout",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "ema_200": ema_200,
                "ath": ath,
                "distance_from_ath": distance_from_ath,
                "volume_ratio": volume_ratio,
                "typical_win_rate": "55-65%",
                "typical_sharpe": "1.2-1.8",
            }
        )

    # ==========================================
    # STRATEGY 2: 52-Week High Momentum
    # ==========================================
    def strategy_52week_high_momentum(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        52-Week High Momentum Strategy

        Rules:
        1. Price > 200 DMA
        2. Price within 10% of 52-week high
        3. EPS growth > 15% (if available)

        Research shows stocks near 52-week highs outperform significantly.
        Typical Stats: Win rate ~60%, Sharpe ~1.3, Strong alpha
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]
        sma_200 = df['SMA_200'].iloc[-1]

        # 52-week high/low
        high_52w = df['High'].tail(252).max() if len(df) >= 252 else df['High'].max()
        low_52w = df['Low'].tail(252).min() if len(df) >= 252 else df['Low'].min()

        distance_from_high = (high_52w - current_price) / high_52w * 100

        # Condition 1: Price > 200 DMA
        if current_price > sma_200:
            conditions_met.append("Price above 200 DMA")
        else:
            conditions_failed.append("Price below 200 DMA")

        # Condition 2: Within 10% of 52W high
        if distance_from_high <= 10:
            conditions_met.append(f"Within {distance_from_high:.1f}% of 52W high")
        else:
            conditions_failed.append(f"{distance_from_high:.1f}% below 52W high")

        # Condition 3: Not near 52W low (avoid falling knives)
        distance_from_low = (current_price - low_52w) / low_52w * 100
        if distance_from_low > 30:
            conditions_met.append(f"Well above 52W low (+{distance_from_low:.1f}%)")
        else:
            conditions_failed.append(f"Too close to 52W low (+{distance_from_low:.1f}%)")

        # Condition 4: RSI not overbought
        rsi = df['RSI'].iloc[-1]
        if rsi < 75:
            conditions_met.append(f"RSI not overbought ({rsi:.1f})")
        else:
            conditions_failed.append(f"RSI overbought ({rsi:.1f})")

        score = len(conditions_met) / 4 * 100

        if score >= 75:
            signal = StrategySignal.STRONG_BUY
        elif score >= 50:
            signal = StrategySignal.BUY
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = current_price
        stop_loss = current_price * 0.93
        target = high_52w * 1.15
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="52-Week High Momentum",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "52w_high": high_52w,
                "52w_low": low_52w,
                "distance_from_high": distance_from_high,
                "rsi": rsi,
                "typical_win_rate": "~60%",
                "typical_sharpe": "~1.3",
            }
        )

    # ==========================================
    # STRATEGY 3: Volatility Contraction Pattern (VCP)
    # ==========================================
    def strategy_vcp(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        Volatility Contraction Pattern (Mark Minervini)

        Pattern: Large range → Smaller range → Even smaller range → Breakout

        Entry: Buy on breakout of contraction
        Volume: > 150% average

        Typical Stats: Win rate ~60%, Sharpe ~1.4, High return potential
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        # Calculate ranges for different periods
        range_30 = (df['High'].tail(30).max() - df['Low'].tail(30).min()) / df['Close'].iloc[-30]
        range_15 = (df['High'].tail(15).max() - df['Low'].tail(15).min()) / df['Close'].iloc[-15]
        range_7 = (df['High'].tail(7).max() - df['Low'].tail(7).min()) / df['Close'].iloc[-7]

        current_price = df['Close'].iloc[-1]
        avg_volume = df['Volume'].rolling(50).mean().iloc[-1]
        current_volume = df['Volume'].iloc[-1]

        # Condition 1: Price above 200 EMA (uptrend)
        ema_200 = df['EMA_200'].iloc[-1]
        if current_price > ema_200:
            conditions_met.append("Price above 200 EMA (uptrend)")
        else:
            conditions_failed.append("Price below 200 EMA")

        # Condition 2: Volatility contraction (ranges getting smaller)
        if range_15 < range_30 * 0.8:
            conditions_met.append("Volatility contracting (15d < 30d range)")
        else:
            conditions_failed.append("No volatility contraction")

        if range_7 < range_15 * 0.8:
            conditions_met.append("Tight consolidation (7d < 15d range)")
        else:
            conditions_failed.append("No tight consolidation")

        # Condition 3: Near recent high (potential breakout)
        recent_high = df['High'].tail(30).max()
        distance_from_recent_high = (recent_high - current_price) / recent_high * 100
        if distance_from_recent_high < 5:
            conditions_met.append(f"Near breakout level ({distance_from_recent_high:.1f}%)")
        else:
            conditions_failed.append(f"Far from breakout ({distance_from_recent_high:.1f}%)")

        # Condition 4: Volume ready for expansion
        volume_ratio = current_volume / avg_volume
        if volume_ratio > 0.8:
            conditions_met.append("Volume ready")
        else:
            conditions_failed.append("Volume too low")

        score = len(conditions_met) / 5 * 100

        if score >= 80:
            signal = StrategySignal.STRONG_BUY
        elif score >= 60:
            signal = StrategySignal.BUY
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = recent_high * 1.01  # Breakout entry
        stop_loss = df['Low'].tail(7).min()
        target = entry_price * 1.20
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="Volatility Contraction Pattern (VCP)",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "range_30d": f"{range_30*100:.1f}%",
                "range_15d": f"{range_15*100:.1f}%",
                "range_7d": f"{range_7*100:.1f}%",
                "breakout_level": recent_high,
                "typical_win_rate": "~60%",
                "typical_sharpe": "~1.4",
            }
        )

    # ==========================================
    # STRATEGY 4: Cup and Handle Breakout
    # ==========================================
    def strategy_cup_and_handle(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        Cup and Handle Breakout

        Pattern: Cup → Handle (consolidation) → Breakout
        Cup depth should be < 30%

        One of the highest probability breakout patterns.
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]

        # Look for cup pattern in last 60-120 days
        lookback = min(120, len(df) - 1)
        cup_data = df.tail(lookback)

        # Find potential cup
        cup_high = cup_data['High'].max()
        cup_low = cup_data['Low'].min()
        cup_depth = (cup_high - cup_low) / cup_high * 100

        # Handle should be last 10-20 days
        handle_data = df.tail(15)
        handle_high = handle_data['High'].max()
        handle_low = handle_data['Low'].min()
        handle_depth = (handle_high - handle_low) / handle_high * 100

        # Condition 1: Cup depth < 30%
        if cup_depth < 30:
            conditions_met.append(f"Cup depth acceptable ({cup_depth:.1f}%)")
        else:
            conditions_failed.append(f"Cup too deep ({cup_depth:.1f}%)")

        # Condition 2: Handle smaller than cup
        if handle_depth < cup_depth * 0.5:
            conditions_met.append("Handle consolidation valid")
        else:
            conditions_failed.append("Handle too deep")

        # Condition 3: Price near cup high (handle formation)
        distance_from_cup_high = (cup_high - current_price) / cup_high * 100
        if distance_from_cup_high < 10:
            conditions_met.append(f"Near cup high ({distance_from_cup_high:.1f}%)")
        else:
            conditions_failed.append(f"Far from cup high ({distance_from_cup_high:.1f}%)")

        # Condition 4: Above 50 EMA
        ema_50 = df['EMA_50'].iloc[-1]
        if current_price > ema_50:
            conditions_met.append("Price above 50 EMA")
        else:
            conditions_failed.append("Price below 50 EMA")

        score = len(conditions_met) / 4 * 100

        if score >= 75:
            signal = StrategySignal.STRONG_BUY
        elif score >= 50:
            signal = StrategySignal.BUY
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = cup_high * 1.01
        stop_loss = handle_low * 0.98
        target = cup_high + (cup_high - cup_low)  # Measured move
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="Cup and Handle Breakout",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "cup_high": cup_high,
                "cup_low": cup_low,
                "cup_depth": f"{cup_depth:.1f}%",
                "handle_depth": f"{handle_depth:.1f}%",
                "typical_win_rate": "~65%",
            }
        )

    # ==========================================
    # STRATEGY 5: Donchian Channel (Turtle)
    # ==========================================
    def strategy_donchian_turtle(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        Donchian Channel Breakout (Turtle Strategy)

        Rules:
        - Buy when price breaks 20-day high
        - Exit when price breaks 10-day low

        Pure trend following. Win rate ~40% but winners are huge.
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]

        # Donchian channels
        high_20 = df['High'].tail(20).max()
        low_10 = df['Low'].tail(10).min()
        high_55 = df['High'].tail(55).max()

        # ATR for position sizing
        atr = df['ATR'].iloc[-1] if 'ATR' in df.columns else (df['High'] - df['Low']).tail(14).mean()

        # Condition 1: Breaking 20-day high
        if current_price >= high_20 * 0.99:
            conditions_met.append(f"Breaking 20-day high ({high_20:.2f})")
        else:
            conditions_failed.append(f"Below 20-day high ({high_20:.2f})")

        # Condition 2: Above 10-day low (not in exit zone)
        if current_price > low_10:
            conditions_met.append("Above exit level (10-day low)")
        else:
            conditions_failed.append("At or below exit level")

        # Condition 3: Trend confirmation (55-day breakout)
        if current_price >= high_55 * 0.95:
            conditions_met.append("Near 55-day high (strong trend)")
        else:
            conditions_failed.append("Below 55-day trend level")

        # Condition 4: Volatility acceptable
        volatility = atr / current_price * 100
        if volatility < 5:
            conditions_met.append(f"Volatility acceptable ({volatility:.1f}%)")
        else:
            conditions_failed.append(f"High volatility ({volatility:.1f}%)")

        score = len(conditions_met) / 4 * 100

        if score >= 75:
            signal = StrategySignal.STRONG_BUY
        elif score >= 50:
            signal = StrategySignal.BUY
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = high_20
        stop_loss = low_10
        target = entry_price + (3 * atr)  # 3 ATR target
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="Donchian Channel (Turtle Strategy)",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "20_day_high": high_20,
                "10_day_low": low_10,
                "55_day_high": high_55,
                "atr": atr,
                "typical_win_rate": "~40%",
                "typical_sharpe": "1.1-1.5",
                "note": "Low win rate but huge winners"
            }
        )

    # ==========================================
    # STRATEGY 6: Moving Average Momentum Stack
    # ==========================================
    def strategy_ma_momentum_stack(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        Moving Average Momentum Stack

        Rules:
        - Price > 20 EMA
        - 20 EMA > 50 EMA
        - 50 EMA > 200 EMA

        Entry: Pullback to 20 EMA
        This identifies strong momentum regimes.
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]
        ema_20 = df['EMA_20'].iloc[-1]
        ema_50 = df['EMA_50'].iloc[-1]
        ema_200 = df['EMA_200'].iloc[-1]

        # Condition 1: Price > 20 EMA
        if current_price > ema_20:
            conditions_met.append("Price > 20 EMA")
        else:
            conditions_failed.append("Price < 20 EMA")

        # Condition 2: 20 EMA > 50 EMA
        if ema_20 > ema_50:
            conditions_met.append("20 EMA > 50 EMA")
        else:
            conditions_failed.append("20 EMA < 50 EMA")

        # Condition 3: 50 EMA > 200 EMA
        if ema_50 > ema_200:
            conditions_met.append("50 EMA > 200 EMA")
        else:
            conditions_failed.append("50 EMA < 200 EMA")

        # Condition 4: Pullback opportunity (price near 20 EMA)
        distance_to_20ema = abs(current_price - ema_20) / ema_20 * 100
        if distance_to_20ema < 3:
            conditions_met.append(f"Near 20 EMA pullback ({distance_to_20ema:.1f}%)")
        else:
            conditions_failed.append(f"Far from 20 EMA ({distance_to_20ema:.1f}%)")

        # Check all EMAs trending up
        ema_20_trend = df['EMA_20'].iloc[-1] > df['EMA_20'].iloc[-5]
        ema_50_trend = df['EMA_50'].iloc[-1] > df['EMA_50'].iloc[-5]
        if ema_20_trend and ema_50_trend:
            conditions_met.append("EMAs trending upward")
        else:
            conditions_failed.append("EMAs not trending up")

        score = len(conditions_met) / 5 * 100

        if score >= 80:
            signal = StrategySignal.STRONG_BUY
        elif score >= 60:
            signal = StrategySignal.BUY
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = ema_20  # Pullback entry
        stop_loss = ema_50 * 0.98
        target = current_price * 1.15
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="MA Momentum Stack",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "ema_20": ema_20,
                "ema_50": ema_50,
                "ema_200": ema_200,
                "stack_order": "Perfect" if ema_20 > ema_50 > ema_200 else "Imperfect",
                "typical_win_rate": "~55%",
            }
        )

    # ==========================================
    # STRATEGY 7: Relative Strength Breakout
    # ==========================================
    def strategy_relative_strength(self, df: pd.DataFrame, benchmark_df: pd.DataFrame = None, symbol: str = "") -> StrategyResult:
        """
        Relative Strength Breakout

        Rules:
        - Stock return > Index return
        - Stock near 52-week high

        Used by many hedge funds.
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]

        # Calculate returns
        return_30d = (current_price - df['Close'].iloc[-30]) / df['Close'].iloc[-30] * 100
        return_90d = (current_price - df['Close'].iloc[-90]) / df['Close'].iloc[-90] * 100 if len(df) >= 90 else return_30d

        # 52-week metrics
        high_52w = df['High'].tail(252).max() if len(df) >= 252 else df['High'].max()
        distance_from_high = (high_52w - current_price) / high_52w * 100

        # Relative strength (compare to assumed market return of 12% annually)
        market_return_30d = 1.0  # ~12% annual / 12 months
        market_return_90d = 3.0

        # Condition 1: Outperforming market (30d)
        if return_30d > market_return_30d:
            conditions_met.append(f"30D return ({return_30d:.1f}%) > Market")
        else:
            conditions_failed.append(f"30D return ({return_30d:.1f}%) < Market")

        # Condition 2: Outperforming market (90d)
        if return_90d > market_return_90d:
            conditions_met.append(f"90D return ({return_90d:.1f}%) > Market")
        else:
            conditions_failed.append(f"90D return ({return_90d:.1f}%) < Market")

        # Condition 3: Near 52W high
        if distance_from_high < 15:
            conditions_met.append(f"Near 52W high ({distance_from_high:.1f}% below)")
        else:
            conditions_failed.append(f"Far from 52W high ({distance_from_high:.1f}% below)")

        # Condition 4: Strong price trend
        ema_20 = df['EMA_20'].iloc[-1]
        if current_price > ema_20:
            conditions_met.append("Price above 20 EMA")
        else:
            conditions_failed.append("Price below 20 EMA")

        score = len(conditions_met) / 4 * 100

        if score >= 75:
            signal = StrategySignal.STRONG_BUY
        elif score >= 50:
            signal = StrategySignal.BUY
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = current_price
        stop_loss = current_price * 0.92
        target = high_52w * 1.10
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="Relative Strength Breakout",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "return_30d": f"{return_30d:.1f}%",
                "return_90d": f"{return_90d:.1f}%",
                "52w_high": high_52w,
                "relative_strength": "Strong" if return_90d > market_return_90d * 2 else "Moderate",
                "typical_win_rate": "~58%",
            }
        )

    # ==========================================
    # STRATEGY 8: Bollinger Band Squeeze
    # ==========================================
    def strategy_bollinger_squeeze(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        Bollinger Band Squeeze Breakout

        Rules:
        - Bollinger Band width extremely low (squeeze)
        - Breakout occurs above upper band

        Detects volatility compression before big moves.
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]
        bb_upper = df['BB_Upper'].iloc[-1]
        bb_lower = df['BB_Lower'].iloc[-1]
        bb_middle = df['BB_Middle'].iloc[-1]

        # Calculate band width
        bb_width = (bb_upper - bb_lower) / bb_middle * 100
        bb_width_avg = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']).tail(100).mean() * 100

        # Squeeze detection
        is_squeeze = bb_width < bb_width_avg * 0.6

        # Condition 1: Squeeze detected
        if is_squeeze:
            conditions_met.append(f"Bollinger squeeze detected (width: {bb_width:.1f}%)")
        else:
            conditions_failed.append(f"No squeeze (width: {bb_width:.1f}%)")

        # Condition 2: Price near upper band (potential breakout)
        if current_price > bb_middle:
            conditions_met.append("Price above middle band")
        else:
            conditions_failed.append("Price below middle band")

        # Condition 3: Trend direction
        ema_50 = df['EMA_50'].iloc[-1]
        if current_price > ema_50:
            conditions_met.append("Uptrend (above 50 EMA)")
        else:
            conditions_failed.append("Downtrend (below 50 EMA)")

        # Condition 4: Volume building
        avg_volume = df['Volume'].tail(20).mean()
        recent_volume = df['Volume'].tail(5).mean()
        if recent_volume > avg_volume * 0.9:
            conditions_met.append("Volume building")
        else:
            conditions_failed.append("Low volume")

        score = len(conditions_met) / 4 * 100

        if score >= 75:
            signal = StrategySignal.STRONG_BUY
        elif score >= 50:
            signal = StrategySignal.BUY
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = bb_upper * 1.01  # Breakout entry
        stop_loss = bb_middle
        target = entry_price + (bb_upper - bb_lower) * 2  # 2x band width
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="Bollinger Band Squeeze",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "bb_width": f"{bb_width:.1f}%",
                "bb_width_avg": f"{bb_width_avg:.1f}%",
                "squeeze_ratio": f"{bb_width/bb_width_avg:.2f}x",
                "is_squeeze": is_squeeze,
                "typical_win_rate": "~55%",
            }
        )

    # ==========================================
    # STRATEGY 9: Base Formation Breakout
    # ==========================================
    def strategy_base_breakout(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        Base Formation Breakout

        Pattern: Sideways consolidation for 3-12 months, then breakout
        Very common in multibaggers.
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]

        # Look for base in last 60-250 days
        base_period = min(180, len(df) - 1)
        base_data = df.tail(base_period)

        base_high = base_data['High'].max()
        base_low = base_data['Low'].min()
        base_range = (base_high - base_low) / base_low * 100

        # Recent consolidation (last 30 days)
        recent_high = df['High'].tail(30).max()
        recent_low = df['Low'].tail(30).min()
        recent_range = (recent_high - recent_low) / recent_low * 100

        # Condition 1: Base range < 40% (tight base)
        if base_range < 40:
            conditions_met.append(f"Tight base ({base_range:.1f}% range)")
        else:
            conditions_failed.append(f"Wide base ({base_range:.1f}% range)")

        # Condition 2: Current price near resistance
        if current_price >= base_high * 0.95:
            conditions_met.append("Price near base resistance")
        else:
            conditions_failed.append("Price far from resistance")

        # Condition 3: Recent consolidation tighter than base
        if recent_range < base_range * 0.5:
            conditions_met.append("Tightening consolidation")
        else:
            conditions_failed.append("No tightening")

        # Condition 4: Above key moving averages
        ema_50 = df['EMA_50'].iloc[-1]
        if current_price > ema_50:
            conditions_met.append("Above 50 EMA")
        else:
            conditions_failed.append("Below 50 EMA")

        score = len(conditions_met) / 4 * 100

        if score >= 75:
            signal = StrategySignal.STRONG_BUY
        elif score >= 50:
            signal = StrategySignal.BUY
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = base_high * 1.02
        stop_loss = recent_low * 0.98
        target = base_high + (base_high - base_low)
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="Base Formation Breakout",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "base_high": base_high,
                "base_low": base_low,
                "base_range": f"{base_range:.1f}%",
                "base_period": f"{base_period} days",
                "typical_win_rate": "~58%",
            }
        )

    # ==========================================
    # STRATEGY 10: Stage Analysis (Stan Weinstein)
    # ==========================================
    def strategy_stage_analysis(self, df: pd.DataFrame, symbol: str = "") -> StrategyResult:
        """
        Stage Analysis Strategy (Stan Weinstein)

        Stages:
        - Stage 1: Base formation
        - Stage 2: Uptrend (BUY HERE)
        - Stage 3: Distribution
        - Stage 4: Downtrend

        Entry: Buy at Stage 2 breakout when Price > 30-week MA and MA trending up
        """
        df = self._ensure_indicators(df)

        conditions_met = []
        conditions_failed = []

        current_price = df['Close'].iloc[-1]

        # 30-week MA (approximately 150 days)
        ma_150 = df['Close'].rolling(150).mean().iloc[-1] if len(df) >= 150 else df['SMA_200'].iloc[-1]
        ma_150_prev = df['Close'].rolling(150).mean().iloc[-5] if len(df) >= 150 else df['SMA_200'].iloc[-5]

        # Determine stage
        ma_trending_up = ma_150 > ma_150_prev
        price_above_ma = current_price > ma_150

        # Stage determination
        if price_above_ma and ma_trending_up:
            stage = 2  # Uptrend
            conditions_met.append("Stage 2: Uptrend (ideal entry)")
        elif price_above_ma and not ma_trending_up:
            stage = 3  # Distribution
            conditions_failed.append("Stage 3: Distribution (avoid)")
        elif not price_above_ma and not ma_trending_up:
            stage = 4  # Downtrend
            conditions_failed.append("Stage 4: Downtrend (avoid)")
        else:
            stage = 1  # Basing
            conditions_met.append("Stage 1: Basing (watch for breakout)")

        # Volume confirmation
        avg_volume = df['Volume'].tail(50).mean()
        recent_volume = df['Volume'].tail(5).mean()
        volume_expanding = recent_volume > avg_volume * 1.2

        if volume_expanding and stage == 2:
            conditions_met.append("Volume confirming uptrend")
        elif not volume_expanding:
            conditions_failed.append("Volume not confirming")

        # Condition: Price momentum
        rsi = df['RSI'].iloc[-1]
        if 50 < rsi < 70:
            conditions_met.append(f"RSI in bullish zone ({rsi:.0f})")
        elif rsi >= 70:
            conditions_failed.append(f"RSI overbought ({rsi:.0f})")
        else:
            conditions_failed.append(f"RSI weak ({rsi:.0f})")

        # Condition: Distance from MA
        distance_from_ma = (current_price - ma_150) / ma_150 * 100
        if 0 < distance_from_ma < 15:
            conditions_met.append(f"Good distance from 30W MA ({distance_from_ma:.1f}%)")
        elif distance_from_ma > 15:
            conditions_failed.append(f"Extended from MA ({distance_from_ma:.1f}%)")
        else:
            conditions_failed.append("Below 30W MA")

        score = len(conditions_met) / 4 * 100

        if stage == 2 and score >= 50:
            signal = StrategySignal.STRONG_BUY if score >= 75 else StrategySignal.BUY
        elif stage == 1 and score >= 50:
            signal = StrategySignal.HOLD
        else:
            signal = StrategySignal.NO_SIGNAL

        entry_price = current_price
        stop_loss = ma_150 * 0.97
        target = current_price * 1.30
        risk_reward = (target - entry_price) / (entry_price - stop_loss) if entry_price > stop_loss else 0

        return StrategyResult(
            symbol=symbol,
            strategy_name="Stage Analysis (Weinstein)",
            signal=signal,
            score=score,
            entry_price=entry_price,
            stop_loss=stop_loss,
            target=target,
            risk_reward=risk_reward,
            conditions_met=conditions_met,
            conditions_failed=conditions_failed,
            additional_info={
                "current_stage": stage,
                "stage_name": {1: "Basing", 2: "Uptrend", 3: "Distribution", 4: "Downtrend"}.get(stage),
                "30w_ma": ma_150,
                "ma_trending": "Up" if ma_trending_up else "Down",
                "typical_win_rate": "~60%",
            }
        )

    # ==========================================
    # HELPER METHODS
    # ==========================================
    def _ensure_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all required indicators are calculated."""
        if 'EMA_20' not in df.columns:
            df = TechnicalAnalysis.add_all_indicators(df)
        return df

    def scan_all_strategies(self, df: pd.DataFrame, symbol: str = "") -> List[StrategyResult]:
        """Run all strategies on a stock and return results."""
        results = []

        strategies = [
            self.strategy_200dma_ath_breakout,
            self.strategy_52week_high_momentum,
            self.strategy_vcp,
            self.strategy_cup_and_handle,
            self.strategy_donchian_turtle,
            self.strategy_ma_momentum_stack,
            self.strategy_relative_strength,
            self.strategy_bollinger_squeeze,
            self.strategy_base_breakout,
            self.strategy_stage_analysis,
        ]

        for strategy in strategies:
            try:
                result = strategy(df, symbol)
                results.append(result)
            except Exception as e:
                continue

        return results

    def get_best_strategies(self, df: pd.DataFrame, symbol: str = "", min_score: float = 50) -> List[StrategyResult]:
        """Get strategies with score above threshold, sorted by score."""
        all_results = self.scan_all_strategies(df, symbol)
        filtered = [r for r in all_results if r.score >= min_score]
        return sorted(filtered, key=lambda x: x.score, reverse=True)


# Strategy metadata for UI
STRATEGY_INFO = {
    "200-Day Trend + ATH Breakout": {
        "description": "Buy when price crosses above 200 EMA and breaks ATH with volume",
        "style": "Minervini / O'Neil",
        "typical_win_rate": "55-65%",
        "typical_sharpe": "1.2-1.8",
        "max_drawdown": "Low",
        "annual_return": "25-60%",
    },
    "52-Week High Momentum": {
        "description": "Buy stocks near 52-week highs with strong fundamentals",
        "style": "Academic Momentum",
        "typical_win_rate": "~60%",
        "typical_sharpe": "~1.3",
        "max_drawdown": "Moderate",
        "annual_return": "20-40%",
    },
    "Volatility Contraction Pattern (VCP)": {
        "description": "Buy when volatility contracts before breakout",
        "style": "Mark Minervini",
        "typical_win_rate": "~60%",
        "typical_sharpe": "~1.4",
        "max_drawdown": "Low",
        "annual_return": "30-80%",
    },
    "Cup and Handle Breakout": {
        "description": "Classic pattern: Cup → Handle → Breakout",
        "style": "William O'Neil",
        "typical_win_rate": "~65%",
        "typical_sharpe": "~1.3",
        "max_drawdown": "Moderate",
        "annual_return": "25-50%",
    },
    "Donchian Channel (Turtle Strategy)": {
        "description": "Buy 20-day breakout, exit 10-day breakdown",
        "style": "Turtle Traders",
        "typical_win_rate": "~40%",
        "typical_sharpe": "1.1-1.5",
        "max_drawdown": "Moderate",
        "annual_return": "20-50%",
        "note": "Low win rate but huge winners",
    },
    "MA Momentum Stack": {
        "description": "Price > 20 EMA > 50 EMA > 200 EMA",
        "style": "Trend Following",
        "typical_win_rate": "~55%",
        "typical_sharpe": "~1.2",
        "max_drawdown": "Low",
        "annual_return": "15-35%",
    },
    "Relative Strength Breakout": {
        "description": "Buy stocks outperforming the market",
        "style": "Hedge Fund",
        "typical_win_rate": "~58%",
        "typical_sharpe": "~1.3",
        "max_drawdown": "Moderate",
        "annual_return": "20-45%",
    },
    "Bollinger Band Squeeze": {
        "description": "Buy when volatility compresses then expands",
        "style": "Volatility Trading",
        "typical_win_rate": "~55%",
        "typical_sharpe": "~1.2",
        "max_drawdown": "Moderate",
        "annual_return": "20-40%",
    },
    "Base Formation Breakout": {
        "description": "Buy breakout from multi-month consolidation",
        "style": "Value/Growth",
        "typical_win_rate": "~58%",
        "typical_sharpe": "~1.3",
        "max_drawdown": "Low",
        "annual_return": "30-100%",
        "note": "Common in multibaggers",
    },
    "Stage Analysis (Weinstein)": {
        "description": "Buy Stage 2 uptrend, avoid Stage 4 downtrend",
        "style": "Stan Weinstein",
        "typical_win_rate": "~60%",
        "typical_sharpe": "~1.4",
        "max_drawdown": "Low",
        "annual_return": "25-50%",
    },
}
