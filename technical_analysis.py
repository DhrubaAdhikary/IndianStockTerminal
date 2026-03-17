"""
Technical Analysis Module
=========================
Provides technical indicators and analysis tools for stock data.

Features:
- Moving Averages (EMA, SMA)
- RSI (Relative Strength Index)
- Support and Resistance Detection
- All-Time High/Low Detection
- Fibonacci Retracements
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any


class TechnicalAnalysis:
    """Technical analysis calculations for stock data."""

    @staticmethod
    def calculate_ema(data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            data: Price series (typically Close prices)
            period: EMA period (e.g., 20, 50, 200)

        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_sma(data: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average.

        Args:
            data: Price series
            period: SMA period

        Returns:
            SMA series
        """
        return data.rolling(window=period).mean()

    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.

        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss

        Args:
            data: Price series (typically Close prices)
            period: RSI period (default 14)

        Returns:
            RSI series (0-100)
        """
        delta = data.diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            data: Price series
            fast: Fast EMA period (default 12)
            slow: Slow EMA period (default 26)
            signal: Signal line period (default 9)

        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = data.ewm(span=fast, adjust=False).mean()
        ema_slow = data.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.

        Args:
            data: Price series
            period: SMA period (default 20)
            std_dev: Standard deviation multiplier (default 2.0)

        Returns:
            Tuple of (Upper Band, Middle Band, Lower Band)
        """
        middle = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return upper, middle, lower

    @staticmethod
    def find_support_resistance(df: pd.DataFrame, window: int = 20, threshold: float = 0.02) -> Dict[str, List[float]]:
        """
        Find support and resistance levels using local minima/maxima.

        Args:
            df: DataFrame with OHLCV data
            window: Window size for finding local extrema
            threshold: Minimum distance between levels (as percentage)

        Returns:
            Dictionary with 'support' and 'resistance' levels
        """
        highs = df['High'].values
        lows = df['Low'].values
        closes = df['Close'].values

        resistance_levels = []
        support_levels = []

        # Find local maxima for resistance
        for i in range(window, len(highs) - window):
            if highs[i] == max(highs[i - window:i + window + 1]):
                resistance_levels.append(highs[i])

        # Find local minima for support
        for i in range(window, len(lows) - window):
            if lows[i] == min(lows[i - window:i + window + 1]):
                support_levels.append(lows[i])

        # Cluster nearby levels
        resistance_levels = TechnicalAnalysis._cluster_levels(resistance_levels, threshold)
        support_levels = TechnicalAnalysis._cluster_levels(support_levels, threshold)

        # Sort and filter
        current_price = closes[-1]
        resistance_levels = sorted([r for r in resistance_levels if r > current_price])[:5]
        support_levels = sorted([s for s in support_levels if s < current_price], reverse=True)[:5]

        return {
            'support': support_levels,
            'resistance': resistance_levels
        }

    @staticmethod
    def _cluster_levels(levels: List[float], threshold: float) -> List[float]:
        """Cluster nearby price levels together."""
        if not levels:
            return []

        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            if (level - current_cluster[-1]) / current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]

        clustered.append(np.mean(current_cluster))
        return clustered

    @staticmethod
    def find_pivot_points(df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate pivot points for support/resistance.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary with pivot, support, and resistance levels
        """
        high = df['High'].iloc[-1]
        low = df['Low'].iloc[-1]
        close = df['Close'].iloc[-1]

        pivot = (high + low + close) / 3

        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)

        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)

        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }

    @staticmethod
    def find_all_time_high_low(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Find all-time high and low from the data.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            Dictionary with ATH and ATL values and dates
        """
        ath_idx = df['High'].idxmax()
        atl_idx = df['Low'].idxmin()

        return {
            'ath': {
                'price': df.loc[ath_idx, 'High'],
                'date': ath_idx
            },
            'atl': {
                'price': df.loc[atl_idx, 'Low'],
                'date': atl_idx
            }
        }

    @staticmethod
    def calculate_fibonacci_retracement(high: float, low: float) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels.

        Args:
            high: Swing high price
            low: Swing low price

        Returns:
            Dictionary with Fibonacci levels
        """
        diff = high - low

        return {
            '0.0%': high,
            '23.6%': high - (diff * 0.236),
            '38.2%': high - (diff * 0.382),
            '50.0%': high - (diff * 0.5),
            '61.8%': high - (diff * 0.618),
            '78.6%': high - (diff * 0.786),
            '100.0%': low
        }

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range.

        Args:
            df: DataFrame with OHLCV data
            period: ATR period (default 14)

        Returns:
            ATR series
        """
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    @staticmethod
    def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all technical indicators to the dataframe.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()

        # EMAs
        df['EMA_20'] = TechnicalAnalysis.calculate_ema(df['Close'], 20)
        df['EMA_50'] = TechnicalAnalysis.calculate_ema(df['Close'], 50)
        df['EMA_200'] = TechnicalAnalysis.calculate_ema(df['Close'], 200)

        # SMAs
        df['SMA_20'] = TechnicalAnalysis.calculate_sma(df['Close'], 20)
        df['SMA_50'] = TechnicalAnalysis.calculate_sma(df['Close'], 50)
        df['SMA_200'] = TechnicalAnalysis.calculate_sma(df['Close'], 200)

        # RSI
        df['RSI'] = TechnicalAnalysis.calculate_rsi(df['Close'], 14)

        # MACD
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = TechnicalAnalysis.calculate_macd(df['Close'])

        # Bollinger Bands
        df['BB_Upper'], df['BB_Middle'], df['BB_Lower'] = TechnicalAnalysis.calculate_bollinger_bands(df['Close'])

        # ATR
        df['ATR'] = TechnicalAnalysis.calculate_atr(df)

        return df

    @staticmethod
    def get_signal(df: pd.DataFrame) -> Dict[str, str]:
        """
        Generate trading signals based on indicators.

        Args:
            df: DataFrame with indicators

        Returns:
            Dictionary with signal analysis
        """
        signals = {}
        latest = df.iloc[-1]

        # EMA Signal
        if latest['Close'] > latest['EMA_20'] > latest['EMA_50'] > latest['EMA_200']:
            signals['ema_trend'] = 'STRONG BULLISH'
        elif latest['Close'] > latest['EMA_50']:
            signals['ema_trend'] = 'BULLISH'
        elif latest['Close'] < latest['EMA_20'] < latest['EMA_50'] < latest['EMA_200']:
            signals['ema_trend'] = 'STRONG BEARISH'
        elif latest['Close'] < latest['EMA_50']:
            signals['ema_trend'] = 'BEARISH'
        else:
            signals['ema_trend'] = 'NEUTRAL'

        # RSI Signal
        rsi = latest['RSI']
        if rsi > 70:
            signals['rsi'] = 'OVERBOUGHT'
        elif rsi < 30:
            signals['rsi'] = 'OVERSOLD'
        elif rsi > 50:
            signals['rsi'] = 'BULLISH'
        else:
            signals['rsi'] = 'BEARISH'

        # MACD Signal
        if latest['MACD'] > latest['MACD_Signal']:
            signals['macd'] = 'BULLISH'
        else:
            signals['macd'] = 'BEARISH'

        # Overall Signal
        bullish_count = sum(1 for v in signals.values() if 'BULLISH' in v)
        bearish_count = sum(1 for v in signals.values() if 'BEARISH' in v)

        if bullish_count > bearish_count:
            signals['overall'] = 'BUY'
        elif bearish_count > bullish_count:
            signals['overall'] = 'SELL'
        else:
            signals['overall'] = 'HOLD'

        return signals
