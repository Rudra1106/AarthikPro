"""
Deterministic analytics engine for all financial calculations.

LLM should NEVER:
- Calculate RSI, MACD, or any technical indicators
- Compare percentages or compute deltas
- Rank sectors or stocks
- Compute averages or aggregations

LLM should ONLY:
- Interpret results
- Contextualize findings
- Explain implications
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Trend direction classification."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class Magnitude(str, Enum):
    """Change magnitude classification."""
    SIGNIFICANT = "significant"  # >5%
    MODERATE = "moderate"        # 2-5%
    MINOR = "minor"              # <2%


@dataclass
class ComparisonResult:
    """Result of comparing two values."""
    current: float
    previous: float
    delta: float
    percent_change: float
    direction: str
    magnitude: Magnitude
    
    def to_dict(self) -> dict:
        return {
            "current": self.current,
            "previous": self.previous,
            "delta": self.delta,
            "percent_change": self.percent_change,
            "direction": self.direction,
            "magnitude": self.magnitude.value
        }


@dataclass
class RSIResult:
    """RSI calculation result."""
    value: float
    interpretation: str  # overbought, neutral, oversold
    trend: TrendDirection
    
    def to_dict(self) -> dict:
        return {
            "value": round(self.value, 2),
            "interpretation": self.interpretation,
            "trend": self.trend.value
        }


@dataclass
class MACDResult:
    """MACD calculation result."""
    macd: float
    signal: float
    histogram: float
    interpretation: str  # bullish_crossover, bearish_crossover, neutral
    
    def to_dict(self) -> dict:
        return {
            "macd": round(self.macd, 2),
            "signal": round(self.signal, 2),
            "histogram": round(self.histogram, 2),
            "interpretation": self.interpretation
        }


@dataclass
class SectorRank:
    """Sector ranking with performance metrics."""
    name: str
    change_percent: float
    rank: int
    breadth: float  # % of stocks positive
    momentum: str   # accelerating, decelerating, stable
    relative_strength: float  # vs benchmark
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "change_percent": round(self.change_percent, 2),
            "rank": self.rank,
            "breadth": round(self.breadth, 2),
            "momentum": self.momentum,
            "relative_strength": round(self.relative_strength, 2)
        }


class DeterministicAnalytics:
    """
    Pure Python calculations for all financial metrics.
    
    All methods are deterministic and return structured results.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def compare_metrics(self, current: float, previous: float) -> ComparisonResult:
        """
        Compare two values with percentage change and classification.
        
        Args:
            current: Current value
            previous: Previous value
            
        Returns:
            ComparisonResult with delta, percent change, direction, magnitude
        """
        if previous == 0:
            # Avoid division by zero
            delta = current
            percent_change = 100.0 if current > 0 else -100.0
        else:
            delta = current - previous
            percent_change = (delta / abs(previous)) * 100
        
        # Determine direction
        if delta > 0:
            direction = "up"
        elif delta < 0:
            direction = "down"
        else:
            direction = "flat"
        
        # Determine magnitude
        abs_pct = abs(percent_change)
        if abs_pct > 5.0:
            magnitude = Magnitude.SIGNIFICANT
        elif abs_pct > 2.0:
            magnitude = Magnitude.MODERATE
        else:
            magnitude = Magnitude.MINOR
        
        return ComparisonResult(
            current=current,
            previous=previous,
            delta=delta,
            percent_change=percent_change,
            direction=direction,
            magnitude=magnitude
        )
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[RSIResult]:
        """
        Calculate RSI using Wilder's smoothing method.
        
        Args:
            prices: List of closing prices (oldest to newest)
            period: RSI period (default 14)
            
        Returns:
            RSIResult with value, interpretation, and trend
        """
        if len(prices) < period + 1:
            self.logger.warning(f"Insufficient data for RSI calculation: {len(prices)} < {period + 1}")
            return None
        
        # Calculate price changes
        deltas = np.diff(prices)
        
        # Separate gains and losses
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate initial averages
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        # Wilder's smoothing for remaining periods
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        # Calculate RS and RSI
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Interpret RSI
        if rsi > 70:
            interpretation = "overbought"
            trend = TrendDirection.BEARISH
        elif rsi < 30:
            interpretation = "oversold"
            trend = TrendDirection.BULLISH
        else:
            interpretation = "neutral"
            trend = TrendDirection.NEUTRAL
        
        return RSIResult(value=rsi, interpretation=interpretation, trend=trend)
    
    def calculate_macd(
        self,
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Optional[MACDResult]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: List of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)
            
        Returns:
            MACDResult with MACD, signal, histogram, and interpretation
        """
        if len(prices) < slow_period + signal_period:
            self.logger.warning(f"Insufficient data for MACD: {len(prices)} < {slow_period + signal_period}")
            return None
        
        prices_array = np.array(prices)
        
        # Calculate EMAs
        fast_ema = self._calculate_ema(prices_array, fast_period)
        slow_ema = self._calculate_ema(prices_array, slow_period)
        
        # MACD line
        macd_line = fast_ema - slow_ema
        
        # Signal line (EMA of MACD)
        signal_line = self._calculate_ema(macd_line, signal_period)
        
        # Histogram
        histogram = macd_line - signal_line
        
        # Get latest values
        macd = macd_line[-1]
        signal = signal_line[-1]
        hist = histogram[-1]
        
        # Interpret MACD
        if len(histogram) > 1:
            prev_hist = histogram[-2]
            if hist > 0 and prev_hist <= 0:
                interpretation = "bullish_crossover"
            elif hist < 0 and prev_hist >= 0:
                interpretation = "bearish_crossover"
            elif hist > 0:
                interpretation = "bullish"
            elif hist < 0:
                interpretation = "bearish"
            else:
                interpretation = "neutral"
        else:
            interpretation = "neutral"
        
        return MACDResult(
            macd=macd,
            signal=signal,
            histogram=hist,
            interpretation=interpretation
        )
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """Calculate Exponential Moving Average."""
        ema = np.zeros_like(data)
        ema[0] = data[0]
        multiplier = 2 / (period + 1)
        
        for i in range(1, len(data)):
            ema[i] = (data[i] - ema[i-1]) * multiplier + ema[i-1]
        
        return ema
    
    def calculate_moving_average(self, prices: List[float], period: int) -> Optional[float]:
        """
        Calculate Simple Moving Average.
        
        Args:
            prices: List of prices
            period: MA period
            
        Returns:
            Moving average value
        """
        if len(prices) < period:
            return None
        
        return np.mean(prices[-period:])
    
    def rank_sectors(
        self,
        sector_data: Dict[str, Dict[str, Any]],
        benchmark_change: float = 0.0
    ) -> List[SectorRank]:
        """
        Rank sectors by performance with breadth and momentum analysis.
        
        Args:
            sector_data: Dict of {sector_name: {change_percent, stocks_data}}
            benchmark_change: Benchmark change % for relative strength
            
        Returns:
            List of SectorRank objects sorted by performance
        """
        ranks = []
        
        for sector_name, data in sector_data.items():
            change_pct = data.get("change_percent", 0.0)
            stocks = data.get("stocks", [])
            
            # Calculate breadth (% of stocks positive)
            if stocks:
                positive_stocks = sum(1 for s in stocks if s.get("change_percent", 0) > 0)
                breadth = (positive_stocks / len(stocks)) * 100
            else:
                breadth = 0.0
            
            # Calculate momentum (comparing recent vs earlier performance)
            momentum = self._calculate_momentum(data)
            
            # Relative strength vs benchmark
            relative_strength = change_pct - benchmark_change
            
            ranks.append(SectorRank(
                name=sector_name,
                change_percent=change_pct,
                rank=0,  # Will be assigned after sorting
                breadth=breadth,
                momentum=momentum,
                relative_strength=relative_strength
            ))
        
        # Sort by performance (descending)
        ranks.sort(key=lambda x: x.change_percent, reverse=True)
        
        # Assign ranks
        for i, rank in enumerate(ranks, 1):
            rank.rank = i
        
        return ranks
    
    def _calculate_momentum(self, sector_data: Dict[str, Any]) -> str:
        """
        Calculate momentum trend (accelerating, decelerating, stable).
        
        Args:
            sector_data: Sector performance data
            
        Returns:
            Momentum classification
        """
        # If we have historical data, compare recent vs earlier performance
        historical = sector_data.get("historical_changes", [])
        
        if len(historical) >= 2:
            recent = np.mean(historical[-2:])
            earlier = np.mean(historical[:-2]) if len(historical) > 2 else historical[0]
            
            if recent > earlier * 1.1:
                return "accelerating"
            elif recent < earlier * 0.9:
                return "decelerating"
            else:
                return "stable"
        
        return "stable"
    
    def calculate_breadth(self, stocks: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate market breadth metrics.
        
        Args:
            stocks: List of stock data with change_percent
            
        Returns:
            Dict with breadth metrics
        """
        if not stocks:
            return {"advancing": 0, "declining": 0, "unchanged": 0, "advance_decline_ratio": 0}
        
        advancing = sum(1 for s in stocks if s.get("change_percent", 0) > 0)
        declining = sum(1 for s in stocks if s.get("change_percent", 0) < 0)
        unchanged = len(stocks) - advancing - declining
        
        ad_ratio = advancing / declining if declining > 0 else float('inf')
        
        return {
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "advance_decline_ratio": ad_ratio,
            "advancing_pct": (advancing / len(stocks)) * 100,
            "declining_pct": (declining / len(stocks)) * 100
        }
    
    def calculate_volatility(self, prices: List[float], period: int = 20) -> Optional[float]:
        """
        Calculate historical volatility (standard deviation of returns).
        
        Args:
            prices: List of prices
            period: Lookback period
            
        Returns:
            Annualized volatility percentage
        """
        if len(prices) < period + 1:
            return None
        
        # Calculate returns
        returns = np.diff(prices[-period-1:]) / prices[-period-1:-1]
        
        # Calculate standard deviation
        volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized
        
        return volatility
    
    def identify_support_resistance(
        self,
        prices: List[float],
        lookback: int = 50
    ) -> Dict[str, List[float]]:
        """
        Identify support and resistance levels using local extrema.
        
        Args:
            prices: List of prices
            lookback: Lookback period
            
        Returns:
            Dict with support and resistance levels
        """
        if len(prices) < lookback:
            return {"support": [], "resistance": []}
        
        recent_prices = prices[-lookback:]
        
        # Find local minima (support)
        support_levels = []
        for i in range(2, len(recent_prices) - 2):
            if (recent_prices[i] < recent_prices[i-1] and 
                recent_prices[i] < recent_prices[i-2] and
                recent_prices[i] < recent_prices[i+1] and
                recent_prices[i] < recent_prices[i+2]):
                support_levels.append(recent_prices[i])
        
        # Find local maxima (resistance)
        resistance_levels = []
        for i in range(2, len(recent_prices) - 2):
            if (recent_prices[i] > recent_prices[i-1] and 
                recent_prices[i] > recent_prices[i-2] and
                recent_prices[i] > recent_prices[i+1] and
                recent_prices[i] > recent_prices[i+2]):
                resistance_levels.append(recent_prices[i])
        
        # Get most relevant levels (closest to current price)
        current_price = prices[-1]
        support_levels = sorted(support_levels, key=lambda x: abs(current_price - x))[:3]
        resistance_levels = sorted(resistance_levels, key=lambda x: abs(current_price - x))[:3]
        
        return {
            "support": sorted(support_levels, reverse=True),
            "resistance": sorted(resistance_levels)
        }


# Singleton instance
_analytics_engine: Optional[DeterministicAnalytics] = None


def get_analytics_engine() -> DeterministicAnalytics:
    """Get singleton analytics engine instance."""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = DeterministicAnalytics()
    return _analytics_engine
