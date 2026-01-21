"""
Sectoral indices data fetcher for NSE India.

Fetches and analyzes sectoral index performance for institutional-grade sector analysis.
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from src.data.zerodha_client import get_zerodha_client
from src.data.nse_client import get_nse_client

logger = logging.getLogger(__name__)


# NSE Sectoral Indices
SECTORAL_INDICES = {
    "NIFTY IT": "IT",
    "NIFTY BANK": "Banking",
    "NIFTY PHARMA": "Pharma",
    "NIFTY AUTO": "Auto",
    "NIFTY FMCG": "FMCG",
    "NIFTY METAL": "Metal",
    "NIFTY REALTY": "Realty",
    "NIFTY ENERGY": "Energy",
    "NIFTY MEDIA": "Media",
    "NIFTY PSU BANK": "PSU Banks"
}


async def get_sectoral_indices_data() -> Dict[str, Any]:
    """
    Fetch current data for all sectoral indices.
    
    Returns:
        Dict mapping sector name to OHLC data
    """
    zerodha = get_zerodha_client()
    
    if not zerodha.kite:
        logger.warning("Zerodha not initialized - cannot fetch sectoral indices")
        return {}
    
    sectoral_data = {}
    
    # Fetch OHLC for all sectoral indices in parallel
    tasks = []
    for index_name in SECTORAL_INDICES.keys():
        tasks.append(zerodha.get_ohlc(index_name))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Map results to sector names
    for i, (index_name, sector_name) in enumerate(SECTORAL_INDICES.items()):
        result = results[i]
        if not isinstance(result, Exception) and result:
            sectoral_data[sector_name] = {
                **result,
                "index_name": index_name,
                "sector": sector_name
            }
    
    return sectoral_data


def calculate_relative_strength(sector_change: float, nifty_change: float) -> float:
    """
    Calculate relative strength of sector vs Nifty.
    
    Args:
        sector_change: Sector % change
        nifty_change: Nifty 50 % change
        
    Returns:
        Relative strength (positive = outperforming, negative = underperforming)
    """
    return sector_change - nifty_change


async def get_sector_breadth(sector: str, top_stocks: List[str]) -> Dict[str, Any]:
    """
    Calculate detailed breadth metrics for a sector.
    
    Args:
        sector: Sector name
        top_stocks: List of top stock symbols in sector
        
    Returns:
        Dict with advancing, declining, unchanged counts and percentage
    """
    if not top_stocks:
        return {
            "advancing": 0,
            "declining": 0,
            "unchanged": 0,
            "total": 0,
            "pct_positive": 0.0,
            "signal": "No data"
        }
    
    zerodha = get_zerodha_client()
    
    if not zerodha.kite:
        return {
            "advancing": 0,
            "declining": 0,
            "unchanged": 0,
            "total": len(top_stocks),
            "pct_positive": 0.0,
            "signal": "Data unavailable"
        }
    
    # Fetch OHLC for all stocks in sector
    tasks = [zerodha.get_ohlc(symbol) for symbol in top_stocks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    advancing = 0
    declining = 0
    unchanged = 0
    
    for result in results:
        if not isinstance(result, Exception) and result:
            change_pct = result.get("change_percent", 0)
            if change_pct > 0.05:  # > 0.05% to avoid noise
                advancing += 1
            elif change_pct < -0.05:
                declining += 1
            else:
                unchanged += 1
    
    total = advancing + declining + unchanged
    
    if total == 0:
        return {
            "advancing": 0,
            "declining": 0,
            "unchanged": 0,
            "total": 0,
            "pct_positive": 0.0,
            "signal": "No data"
        }
    
    pct_positive = (advancing / total) * 100
    
    # Generate breadth signal
    if pct_positive < 30:
        signal = "⚠️ Narrow - stock-specific, not broad-based"
    elif pct_positive > 70:
        signal = "✅ Broad - sector-wide strength"
    else:
        signal = "⚖️ Mixed - selective performance"
    
    return {
        "advancing": advancing,
        "declining": declining,
        "unchanged": unchanged,
        "total": total,
        "pct_positive": round(pct_positive, 1),
        "signal": signal
    }


def classify_sector_regime(relative_strength: float, breadth_pct: float) -> str:
    """
    Classify sector into market regime.
    
    Args:
        relative_strength: Relative strength vs Nifty (%)
        breadth_pct: Breadth percentage (0.0 to 100.0)
        
    Returns:
        Regime: "leader", "lagging", "defensive", "neutral"
    """
    # Leader: Outperforming with strong breadth
    if relative_strength > 0.5 and breadth_pct > 60:
        return "leader"
    
    # Lagging: Underperforming or weak breadth
    elif relative_strength < -0.5 or breadth_pct < 40:
        return "lagging"
    
    # Defensive: Positive but not leading
    elif relative_strength > 0 and breadth_pct > 50:
        return "defensive"
    
    # Neutral: Everything else
    else:
        return "neutral"


def get_regime_emoji(regime: str) -> str:
    """Get emoji for regime classification."""
    return {
        "leader": "🟢",
        "lagging": "🔴",
        "defensive": "🛡",
        "neutral": "🟡"
    }.get(regime, "⚪")


# Top stocks per sector (for breadth calculation)
SECTOR_TOP_STOCKS = {
    "IT": ["TCS", "INFY", "HCLTECH", "WIPRO", "TECHM"],
    "Banking": ["HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN"],
    "Pharma": ["SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "AUROPHARMA"],
    "Auto": ["MARUTI", "TATAMOTORS", "M&M", "BAJAJ-AUTO", "EICHERMOT"],
    "FMCG": ["HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR"],
    "Metal": ["TATASTEEL", "HINDALCO", "JSWSTEEL", "COALINDIA", "VEDL"],
    "Realty": ["DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "BRIGADE"],
    "Energy": ["RELIANCE", "ONGC", "BPCL", "IOC", "GAIL"],
    "Media": ["ZEEL", "SUNTV", "PVRINOX", "DISHTV", "NETWORK18"],
    "PSU Banks": ["SBIN", "PNB", "BANKBARODA", "CANBK", "UNIONBANK"]
}


async def get_sector_performance(timeframe: str = "5D") -> Dict[str, Any]:
    """
    Get comprehensive sector performance analysis (CACHE-FIRST).
    
    Architecture:
    - Reads from pre-built 'sector_snapshot' cache (populated by background worker)
    - NEVER fetches live OHLC at query time
    - Graceful degradation if cache unavailable
    
    Args:
        timeframe: "1D", "5D", or "1M" (legacy param, snapshot always uses 5D)
        
    Returns:
        Dict with sector performance, rankings, and regime classifications
    """
    import pytz
    from datetime import datetime
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    timestamp = now.strftime("%d %b %Y, %I:%M %p IST")
    
    from src.data.redis_client import get_redis_cache
    redis = get_redis_cache()
    
    try:
        await redis._ensure_connected()
        
        if redis._connected:
            # PRIORITY 1: Check for pre-built sector snapshot (from background worker)
            snapshot = await redis.get("sector_snapshot")
            if snapshot and snapshot.get("sectors"):
                logger.info("✅ Returning sector_snapshot from cache (cache-first mode)")
                return snapshot
            
            # PRIORITY 2: Check for legacy sector_performance cache
            cache_key = f"sector_performance:{timeframe}"
            cached = await redis.get(cache_key)
            if cached and cached.get("sectors"):
                logger.info(f"Returning legacy cached sector data (key: {cache_key})")
                return cached
                
    except Exception as e:
        logger.warning(f"Redis cache check failed: {e}")
    
    # GRACEFUL DEGRADATION: Return empty response with status indicator
    logger.warning("⚠️ No sector data in cache. Run: python scripts/market_data_worker.py")
    return {
        "timestamp": timestamp,
        "timeframe": timeframe,
        "sectors": [],
        "nifty_change": 0,
        "status": "stale",
        "note": "Live data temporarily unavailable. Background worker may need to be started.",
        "error": None
    }
    
    # Fetch Nifty 50 for relative strength calculation
    zerodha = get_zerodha_client()
    nifty_data = await zerodha.get_ohlc("NIFTY 50")
    
    if not nifty_data:
        logger.warning("Unable to fetch Nifty 50 data")
        nifty_change = 0
    else:
        nifty_change = nifty_data.get("change_percent", 0)
    
    # OPTIMIZATION: Fetch all breadth data in parallel
    logger.info("Fetching breadth data for all sectors in parallel...")
    breadth_tasks = []
    sector_names = list(sectoral_data.keys())
    
    for sector_name in sector_names:
        top_stocks = SECTOR_TOP_STOCKS.get(sector_name, [])
        breadth_tasks.append(get_sector_breadth(sector_name, top_stocks))
    
    breadth_results = await asyncio.gather(*breadth_tasks, return_exceptions=True)
    
    # Map breadth results to sectors
    breadth_map = {}
    for i, sector_name in enumerate(sector_names):
        result = breadth_results[i]
        if isinstance(result, Exception):
            logger.warning(f"Breadth fetch failed for {sector_name}: {result}")
            breadth_map[sector_name] = {
                "advancing": 0, "declining": 0, "unchanged": 0,
                "total": 0, "pct_positive": 0.0, "signal": "Error"
            }
        else:
            breadth_map[sector_name] = result
    
    # OPTIMIZATION: Fetch all top movers in parallel
    logger.info("Fetching top movers for all sectors in parallel...")
    top_mover_tasks = []
    top_mover_sectors = []
    
    for sector_name in sector_names:
        top_stocks = SECTOR_TOP_STOCKS.get(sector_name, [])
        if top_stocks:
            for symbol in top_stocks[:3]:  # Top 3 only
                top_mover_tasks.append(zerodha.get_ohlc(symbol))
                top_mover_sectors.append(sector_name)
    
    top_mover_results = await asyncio.gather(*top_mover_tasks, return_exceptions=True)
    
    # Map top movers to sectors
    top_movers_map = {sector: [] for sector in sector_names}
    task_idx = 0
    
    for sector_name in sector_names:
        top_stocks = SECTOR_TOP_STOCKS.get(sector_name, [])
        for i, symbol in enumerate(top_stocks[:3]):
            if task_idx < len(top_mover_results):
                result = top_mover_results[task_idx]
                if not isinstance(result, Exception) and result:
                    top_movers_map[sector_name].append({
                        "symbol": symbol,
                        "change_percent": result.get("change_percent", 0)
                    })
                task_idx += 1
    
    # Analyze each sector
    sectors_analysis = []
    
    for sector_name, data in sectoral_data.items():
        change_pct = data.get("change_percent", 0)
        
        # Calculate relative strength
        rel_strength = calculate_relative_strength(change_pct, nifty_change)
        
        # Get breadth from parallel results
        breadth = breadth_map.get(sector_name, {
            "advancing": 0, "declining": 0, "unchanged": 0,
            "total": 0, "pct_positive": 0.0, "signal": "No data"
        })
        
        # Classify regime
        regime = classify_sector_regime(rel_strength, breadth.get("pct_positive", 0))
        
        # Get top movers from parallel results
        top_movers = top_movers_map.get(sector_name, [])
        
        sectors_analysis.append({
            "name": sector_name,
            "index_name": data.get("index_name"),
            "index_value": data.get("last_price", 0),
            "prev_close": data.get("close", 0),
            "change_abs": data.get("change", 0),
            "change_pct": change_pct,
            "relative_strength": rel_strength,
            "breadth": breadth,  # Now a dict with detailed counts
            "regime": regime,
            "regime_emoji": get_regime_emoji(regime),
            "top_movers": top_movers,
            "volume": data.get("volume", 0)
        })
    
    # Sort sectors by relative strength (not absolute performance)
    sectors_sorted = sorted(sectors_analysis, key=lambda x: x["relative_strength"], reverse=True)
    
    # Categorize sectors
    leaders = [s for s in sectors_sorted if s["regime"] == "leader"]
    laggards = [s for s in sectors_sorted if s["regime"] == "lagging"]
    defensive = [s for s in sectors_sorted if s["regime"] == "defensive"]
    neutral = [s for s in sectors_sorted if s["regime"] == "neutral"]
    
    # Calculate market conviction
    # High conviction = strong breadth + clear direction
    avg_breadth = sum(s["breadth"].get("pct_positive", 0) for s in sectors_sorted) / len(sectors_sorted) if sectors_sorted else 0
    conviction = "High" if avg_breadth > 60 or avg_breadth < 30 else "Medium" if avg_breadth > 45 else "Low"
    
    result = {
        "timestamp": timestamp,
        "timeframe": timeframe,
        "timeframe_label": "Week-to-date" if timeframe == "5D" else "Today" if timeframe == "1D" else "Month-to-date",
        "data_source": "NSE Sectoral Indices via Zerodha Kite",
        "nifty_change": nifty_change,
        "nifty_value": nifty_data.get("last_price", 0) if nifty_data else 0,
        "sectors": sectors_sorted,
        "leaders": leaders,
        "laggards": laggards,
        "defensive": defensive,
        "neutral": neutral,
        "total_sectors": len(sectors_sorted),
        "market_conviction": conviction,
        "avg_breadth": round(avg_breadth, 1)
    }
    
    # Cache the result for 5 minutes
    try:
        if redis and redis._connected:
            await redis.set(cache_key, result, ttl=300)  # 5 minutes
            logger.info(f"Cached sector data for 5 minutes (key: {cache_key})")
    except Exception as e:
        logger.warning(f"Failed to cache sector data: {e}")
    
    return result


async def get_sector_catalysts(sector: str) -> str:
    """
    Get brief catalyst explanation for sector performance.
    
    Args:
        sector: Sector name
        
    Returns:
        Brief catalyst explanation (1-2 lines)
    """
    # Placeholder - can be enhanced with Perplexity API
    # For now, return generic catalysts
    catalysts = {
        "IT": "Rupee stability, deal pipeline optimism, valuation comfort",
        "Banking": "Credit growth trends, NPA cycle dynamics",
        "Pharma": "Export demand, defensive positioning",
        "Auto": "Festive demand, inventory normalization",
        "FMCG": "Rural demand recovery, pricing power",
        "Metal": "China demand, commodity price trends",
        "Realty": "Festive launches, interest rate outlook",
        "Energy": "Crude oil prices, refining margins",
        "Media": "Ad spending trends, OTT competition",
        "PSU Banks": "Government recapitalization, credit growth"
    }
    
    return catalysts.get(sector, "Market dynamics, sector rotation")
