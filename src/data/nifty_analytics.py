"""
Nifty 50 Analytics Module

Provides institutional-grade analysis for Nifty 50 index including:
- Top contributors by weight
- Sectoral performance breakdown
- Technical indicators (DMAs, RSI)
- Volatility context (India VIX)
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
import logging
from datetime import datetime, timedelta

from src.data.zerodha_client import get_zerodha_client
from src.data.redis_client import get_redis_cache

logger = logging.getLogger(__name__)


# Nifty 50 Top 10 Constituents by Weight (as of Dec 2024)
# Source: NSE India official weightage
NIFTY_50_TOP_CONSTITUENTS = [
    {"symbol": "RELIANCE", "weight": 10.12, "sector": "Energy"},
    {"symbol": "HDFCBANK", "weight": 9.85, "sector": "Banking"},
    {"symbol": "ICICIBANK", "weight": 7.64, "sector": "Banking"},
    {"symbol": "INFY", "weight": 6.23, "sector": "IT"},
    {"symbol": "TCS", "weight": 5.89, "sector": "IT"},
    {"symbol": "ITC", "weight": 4.76, "sector": "FMCG"},
    {"symbol": "BHARTIARTL", "weight": 4.52, "sector": "Telecom"},
    {"symbol": "KOTAKBANK", "weight": 4.18, "sector": "Banking"},
    {"symbol": "LT", "weight": 3.95, "sector": "Capital Goods"},
    {"symbol": "HINDUNILVR", "weight": 3.72, "sector": "FMCG"},
]

# Extended list for sectoral analysis (top 30 for better sector coverage)
NIFTY_50_EXTENDED = NIFTY_50_TOP_CONSTITUENTS + [
    {"symbol": "SBIN", "weight": 3.45, "sector": "Banking"},
    {"symbol": "BAJFINANCE", "weight": 3.21, "sector": "Financial Services"},
    {"symbol": "AXISBANK", "weight": 2.98, "sector": "Banking"},
    {"symbol": "ASIANPAINT", "weight": 2.76, "sector": "Consumer Durables"},
    {"symbol": "MARUTI", "weight": 2.54, "sector": "Automobile"},
    {"symbol": "HCLTECH", "weight": 2.43, "sector": "IT"},
    {"symbol": "WIPRO", "weight": 2.12, "sector": "IT"},
    {"symbol": "SUNPHARMA", "weight": 2.08, "sector": "Pharma"},
    {"symbol": "TITAN", "weight": 1.95, "sector": "Consumer Durables"},
    {"symbol": "ULTRACEMCO", "weight": 1.87, "sector": "Cement"},
]


async def get_nifty_constituents(top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Get top N Nifty 50 constituents by weight.
    
    Args:
        top_n: Number of top constituents to return (default: 10)
        
    Returns:
        List of dicts with symbol, weight, sector
    """
    return NIFTY_50_TOP_CONSTITUENTS[:top_n]


async def calculate_top_contributors(
    constituent_data: List[Dict[str, Any]],
    top_n: int = 3
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate top positive and negative contributors to index movement.
    
    Contribution = Weight × Change %
    
    Args:
        constituent_data: List of dicts with symbol, weight, change_percent
        top_n: Number of top contributors to return for each side
        
    Returns:
        Dict with 'positive' and 'negative' lists of top contributors
    """
    # Calculate contribution for each stock
    contributions = []
    for stock in constituent_data:
        if "change_percent" in stock and "weight" in stock:
            contribution = (stock["weight"] / 100) * stock["change_percent"]
            contributions.append({
                "symbol": stock["symbol"],
                "sector": stock.get("sector", "Unknown"),
                "change_percent": stock["change_percent"],
                "weight": stock["weight"],
                "contribution": round(contribution, 3)
            })
    
    # Sort by contribution
    contributions.sort(key=lambda x: x["contribution"], reverse=True)
    
    # Split into positive and negative
    positive = [c for c in contributions if c["contribution"] > 0][:top_n]
    negative = [c for c in contributions if c["contribution"] < 0][:top_n]
    
    return {
        "positive": positive,
        "negative": negative
    }


async def get_sectoral_breakdown(
    constituent_data: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate sector-wise performance breakdown.
    
    Args:
        constituent_data: List of dicts with symbol, sector, change_percent, weight
        
    Returns:
        Dict mapping sector -> {change_pct, stocks, total_weight}
    """
    sectors = {}
    
    for stock in constituent_data:
        sector = stock.get("sector", "Unknown")
        change_pct = stock.get("change_percent", 0)
        weight = stock.get("weight", 0)
        symbol = stock["symbol"]
        
        if sector not in sectors:
            sectors[sector] = {
                "stocks": [],
                "total_weight": 0,
                "weighted_change": 0
            }
        
        sectors[sector]["stocks"].append(symbol)
        sectors[sector]["total_weight"] += weight
        sectors[sector]["weighted_change"] += (weight * change_pct)
    
    # Calculate average change for each sector
    for sector in sectors:
        total_weight = sectors[sector]["total_weight"]
        if total_weight > 0:
            sectors[sector]["change_pct"] = round(
                sectors[sector]["weighted_change"] / total_weight, 2
            )
        else:
            sectors[sector]["change_pct"] = 0
        
        # Clean up intermediate calculation
        del sectors[sector]["weighted_change"]
    
    return sectors


async def calculate_moving_averages(
    historical_data: List[Dict[str, Any]],
    periods: List[int] = [20, 50, 200]
) -> Dict[str, float]:
    """
    Calculate moving averages from historical data.
    
    Args:
        historical_data: List of OHLC candles with 'close' price
        periods: List of periods for DMAs (default: [20, 50, 200])
        
    Returns:
        Dict mapping period -> DMA value
    """
    if not historical_data:
        return {}
    
    # Extract close prices (most recent first)
    closes = [candle["close"] for candle in historical_data]
    closes.reverse()  # Oldest to newest
    
    dmas = {}
    for period in periods:
        if len(closes) >= period:
            dma = sum(closes[-period:]) / period
            dmas[f"{period}_dma"] = round(dma, 2)
    
    return dmas


async def calculate_rsi(
    historical_data: List[Dict[str, Any]],
    period: int = 14
) -> Optional[float]:
    """
    Calculate RSI (Relative Strength Index) using Wilder's smoothing method.
    
    Args:
        historical_data: List of OHLC candles with 'close' price
        period: RSI period (default: 14)
        
    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if not historical_data or len(historical_data) < period + 1:
        return None
    
    try:
        import pandas as pd
        import gc
        
        # Extract close prices
        closes = [candle["close"] for candle in historical_data]
        df = pd.DataFrame({"close": closes})
        
        # Calculate price changes
        delta = df["close"].diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calculate Wilder's smoothed averages
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        
        # Apply Wilder's smoothing for subsequent values
        for i in range(period, len(df)):
            avg_gain.iloc[i] = (avg_gain.iloc[i-1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i-1] * (period - 1) + loss.iloc[i]) / period
        
        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Return latest RSI value
        latest_rsi = rsi.iloc[-1]
        return round(float(latest_rsi), 2) if pd.notna(latest_rsi) else None
        
    except Exception as e:
        logger.error(f"Error calculating RSI: {e}")
        return None


async def calculate_macd(
    historical_data: List[Dict[str, Any]],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Optional[Dict[str, float]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).
    
    Args:
        historical_data: List of OHLC candles with 'close' price
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
        
    Returns:
        Dict with macd, signal, histogram values or None
    """
    if not historical_data or len(historical_data) < slow_period + signal_period:
        return None
    
    try:
        import pandas as pd
        
        # Extract close prices
        closes = [candle["close"] for candle in historical_data]
        df = pd.DataFrame({"close": closes})
        
        # Calculate EMAs
        ema_fast = df["close"].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df["close"].ewm(span=slow_period, adjust=False).mean()
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Histogram
        histogram = macd_line - signal_line
        
        # Return latest values
        return {
            "macd": round(float(macd_line.iloc[-1]), 2),
            "signal": round(float(signal_line.iloc[-1]), 2),
            "histogram": round(float(histogram.iloc[-1]), 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating MACD: {e}")
        return None


async def calculate_bollinger_bands(
    historical_data: List[Dict[str, Any]],
    period: int = 20,
    std_dev: float = 2.0
) -> Optional[Dict[str, float]]:
    """
    Calculate Bollinger Bands.
    
    Args:
        historical_data: List of OHLC candles with 'close' price
        period: Moving average period (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)
        
    Returns:
        Dict with upper, middle, lower band values or None
    """
    if not historical_data or len(historical_data) < period:
        return None
    
    try:
        import pandas as pd
        
        # Extract close prices
        closes = [candle["close"] for candle in historical_data]
        df = pd.DataFrame({"close": closes})
        
        # Calculate SMA (middle band)
        sma = df["close"].rolling(window=period).mean()
        
        # Calculate standard deviation
        std = df["close"].rolling(window=period).std()
        
        # Calculate bands
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        # Return latest values
        return {
            "upper": round(float(upper_band.iloc[-1]), 2),
            "middle": round(float(sma.iloc[-1]), 2),
            "lower": round(float(lower_band.iloc[-1]), 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {e}")
        return None



async def get_india_vix() -> Optional[Dict[str, Any]]:
    """
    Get India VIX (volatility index) from Zerodha.
    
    Returns:
        Dict with vix_value, classification, interpretation
    """
    cache = get_redis_cache()
    cache_key = "india_vix"
    
    # Check cache first (15 min TTL)
    cached_vix = await cache.get(cache_key)
    if cached_vix is not None:
        logger.debug("Cache hit for India VIX")
        return cached_vix
    
    zerodha = get_zerodha_client()
    
    try:
        # Fetch India VIX from Zerodha
        vix_data = await zerodha.get_ohlc("INDIA VIX", exchange="NSE")
        
        if not vix_data:
            return None
        
        vix_value = vix_data.get("last_price", 0)
        
        # Classify volatility
        if vix_value < 13:
            classification = "low"
            interpretation = "Low volatility supports range-bound upside"
        elif vix_value < 20:
            classification = "medium"
            interpretation = "Moderate volatility indicates cautious sentiment"
        else:
            classification = "high"
            interpretation = "High volatility signals increased market risk"
        
        result = {
            "vix_value": round(vix_value, 2),
            "classification": classification,
            "interpretation": interpretation,
            "change_percent": vix_data.get("change_percent", 0)
        }
        
        # Cache for 15 minutes
        await cache.set(cache_key, result, ttl=900)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching India VIX: {e}")
        return None


async def get_technical_indicators(
    symbol: str = "NIFTY 50",
    exchange: str = "NSE"
) -> Dict[str, Any]:
    """
    Get comprehensive technical indicators for Nifty 50.
    
    Includes:
    - Moving averages (20, 50, 200 DMA)
    - RSI (14-period)
    - MACD (12, 26, 9)
    - Trend analysis
    
    Args:
        symbol: Index symbol (default: "NIFTY 50")
        exchange: Exchange (default: "NSE")
        
    Returns:
        Dict with technical indicators
    """
    cache = get_redis_cache()
    cache_key = f"technical_indicators:{symbol}"
    
    # Check cache (15 min TTL)
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for technical indicators: {symbol}")
        return cached
    
    zerodha = get_zerodha_client()
    
    try:
        # Fetch historical data (last 300 days to ensure 200+ trading days for 200-DMA)
        historical = await zerodha.get_historical(
            symbol=symbol,
            days=300,
            interval="day",
            exchange=exchange
        )
        
        if not historical or len(historical) < 20:
            logger.warning(f"Insufficient historical data for {symbol}")
            return {}
        
        # Calculate DMAs
        dmas = await calculate_moving_averages(historical, periods=[20, 50, 200])
        
        # Calculate RSI
        rsi = await calculate_rsi(historical, period=14)
        
        # Calculate MACD
        macd_data = await calculate_macd(historical)
        
        # Get current price
        current_data = await zerodha.get_ohlc(symbol, exchange=exchange)
        current_price = current_data.get("last_price", 0) if current_data else 0
        
        # Determine trend
        trend = "neutral"
        if current_price > 0:
            if "20_dma" in dmas and "50_dma" in dmas:
                if current_price > dmas["20_dma"] and current_price > dmas["50_dma"]:
                    trend = "bullish"
                elif current_price < dmas["20_dma"] and current_price < dmas["50_dma"]:
                    trend = "bearish"
        
        result = {
            **dmas,
            "rsi": rsi,
            "macd": macd_data.get("macd") if macd_data else None,
            "macd_signal": macd_data.get("signal") if macd_data else None,
            "macd_histogram": macd_data.get("histogram") if macd_data else None,
            "trend": trend,
            "current_price": current_price
        }
        
        # Cache for 15 minutes
        await cache.set(cache_key, result, ttl=900)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating technical indicators for {symbol}: {e}")
        return {}


async def fetch_constituent_performance(
    top_n: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch live performance data for top Nifty 50 constituents.
    
    Args:
        top_n: Number of top constituents to fetch
        
    Returns:
        List of dicts with symbol, weight, sector, OHLC data
    """
    cache = get_redis_cache()
    cache_key = f"nifty_constituents_performance:{top_n}"
    
    # Check cache (10 min TTL)
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug("Cache hit for constituent performance")
        return cached
    
    constituents = await get_nifty_constituents(top_n)
    zerodha = get_zerodha_client()
    
    # Fetch OHLC for all constituents in parallel
    symbols = [c["symbol"] for c in constituents]
    
    try:
        # Fetch OHLC data
        tasks = [zerodha.get_ohlc(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Merge with constituent data
        enriched = []
        for i, constituent in enumerate(constituents):
            result = results[i]
            
            if isinstance(result, Exception):
                logger.warning(f"Error fetching {constituent['symbol']}: {result}")
                continue
            
            if result:
                enriched.append({
                    **constituent,
                    "last_price": result.get("last_price", 0),
                    "change": result.get("change", 0),
                    "change_percent": result.get("change_percent", 0),
                    "volume": result.get("volume", 0)
                })
        
        # Cache for 10 minutes
        await cache.set(cache_key, enriched, ttl=600)
        
        return enriched
        
    except Exception as e:
        logger.error(f"Error fetching constituent performance: {e}")
        return []
