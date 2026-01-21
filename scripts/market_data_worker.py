#!/usr/bin/env python3
"""
Background Market Data Worker for AarthikAI.

This worker fetches OHLC data from Dhan API at regular intervals
and caches it in Redis. Chatbot queries read from cache only.

Usage:
    python scripts/market_data_worker.py          # Run once
    python scripts/market_data_worker.py --loop   # Run continuously

Architecture:
    Dhan API → (batch fetching) → Redis → Chatbot (read-only)
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
import pytz

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.dhan_client import get_dhan_client
from src.data.redis_client import get_redis_cache

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Watchlist: All symbols to fetch OHLC for
# Organized by priority and sector for comprehensive coverage
WATCHLIST = {
    # Major Indices (fetch first - highest priority)
    "indices": [
        "NIFTY 50",
        "NIFTY BANK",
        "NIFTY IT",
        "NIFTY METAL",
        "NIFTY FMCG",
        "NIFTY PHARMA",
        "NIFTY AUTO",
        "NIFTY REALTY",
        "NIFTY ENERGY",
        "NIFTY PSU BANK",
        "NIFTY MEDIA",
        "NIFTY INFRA",
        "NIFTY FIN SERVICE",
    ],
    
    # Nifty 100 constituents organized by sector
    "stocks": {
        "IT": [
            "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", 
            "LTIM", "MPHASIS", "COFORGE", "PERSISTENT", "LTTS"
        ],
        "Banking": [
            "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "INDUSINDBK",
            "FEDERALBNK", "IDFCFIRSTB", "BANDHANBNK", "AUBANK"
        ],
        "PSU Banks": [
            "SBIN", "BANKBARODA", "CANBK", "PNB", "INDIANB", "UNIONBANK"
        ],
        "NBFC & Finance": [
            "BAJFINANCE", "BAJAJFINSV", "CHOLAFIN", "MUTHOOTFIN", 
            "SHRIRAMFIN", "POONAWALLA", "LICHSGFIN"
        ],
        "Metal & Mining": [
            "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "COALINDIA",
            "NMDC", "JINDALSTEL", "SAIL", "NATIONALUM"
        ],
        "Auto & Auto Ancillary": [
            "MARUTI", "M&M", "BAJAJ-AUTO", "EICHERMOT",
            "HEROMOTOCO", "TVSMOTOR", "ASHOKLEY", "MOTHERSON", "BOSCHLTD"
        ],
        "Pharma & Healthcare": [
            "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
            "MAXHEALTH", "FORTIS", "TORNTPHARM", "LUPIN", "AUROPHARMA"
        ],
        "FMCG": [
            "ITC", "HINDUNILVR", "NESTLEIND", "BRITANNIA", "MARICO",
            "DABUR", "GODREJCP", "COLPAL", "TATACONSUM", "VBL"
        ],
        "Energy & Power": [
            "RELIANCE", "ONGC", "NTPC", "POWERGRID", "ADANIGREEN",
            "ADANIENSOL", "TATAPOWER", "NHPC", "SJVN", "GAIL"
        ],
        "Realty & Infrastructure": [
            "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "BRIGADE",
            "LODHA", "PHOENIXLTD"
        ],
        "Capital Goods & Engineering": [
            "LT", "SIEMENS", "ABB", "HAVELLS", "BHEL",
            "CUMMINSIND", "THERMAX", "VOLTAS"
        ],
        "Cement & Construction": [
            "ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "DALBHARAT",
            "RAMCOCEM", "JKCEMENT"
        ],
        "Telecom & Media": [
            "BHARTIARTL", "ZEEL", "PVRINOX"
        ],
        "Insurance": [
            "SBILIFE", "HDFCLIFE", "ICICIPRULI", "LICI", "NIACL"
        ],
        "Consumer Durables": [
            "TITAN", "VOLTAS", "CROMPTON", "WHIRLPOOL", "DIXON"
        ],
        "Chemicals": [
            "PIDILITIND", "SRF", "ATUL", "DEEPAKNTR", "NAVINFLUOR"
        ],
        "Logistics & Transport": [
            "ADANIPORTS", "CONCOR", "DELHIVERY"
        ],
    }
}

# Batch size for Dhan API (can handle up to 1000 instruments)
BATCH_SIZE = 50

# Cache TTL (seconds)
CACHE_TTL = 300  # 5 minutes


def get_all_symbols() -> list:
    """Get flat list of all symbols to fetch."""
    symbols = list(WATCHLIST["indices"])
    for sector_stocks in WATCHLIST["stocks"].values():
        symbols.extend(sector_stocks)
    # Remove duplicates while preserving order
    return list(dict.fromkeys(symbols))


async def fetch_and_cache_ohlc_batch(symbols: list) -> dict:
    """Fetch OHLC for multiple symbols in batch and cache them."""
    dhan = get_dhan_client()
    redis = get_redis_cache()
    
    results = {"success": 0, "failed": 0}
    
    try:
        # Batch fetch OHLC from Dhan (much faster than sequential)
        logger.info(f"Fetching OHLC for {len(symbols)} symbols from Dhan...")
        ohlc_data = await dhan.get_ohlc(symbols, exchange="NSE_EQ")
        
        if ohlc_data:
            # Cache each symbol's data
            for symbol, data in ohlc_data.items():
                cache_key = f"ohlc:NSE:{symbol}"
                await redis.set(cache_key, data, ttl=CACHE_TTL)
                
                logger.debug(f"✓ {symbol}: ₹{data.get('last_price', 0):,.2f} ({data.get('change_percent', 0):+.2f}%)")
                results["success"] += 1
            
            # Track failed symbols
            failed_symbols = set(symbols) - set(ohlc_data.keys())
            results["failed"] = len(failed_symbols)
            
            if failed_symbols:
                logger.warning(f"✗ No data for: {', '.join(list(failed_symbols)[:5])}...")
        else:
            logger.warning(f"✗ No data returned for batch")
            results["failed"] = len(symbols)
            
    except Exception as e:
        logger.error(f"✗ Batch fetch error: {str(e)[:100]}")
        results["failed"] = len(symbols)
    
    return results


async def build_sector_snapshot():
    """Build and cache aggregated sector snapshot with retry logic."""
    redis = get_redis_cache()
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Read cached OHLC data for indices
    sectors = []
    
    # Map indices to stock sector names (must match WATCHLIST["stocks"] keys)
    index_map = {
        "NIFTY IT": "IT",
        "NIFTY BANK": "Banking",
        "NIFTY METAL": "Metal & Mining",
        "NIFTY AUTO": "Auto & Auto Ancillary",
        "NIFTY PHARMA": "Pharma & Healthcare",
        "NIFTY FMCG": "FMCG",
        "NIFTY ENERGY": "Energy & Power",
        "NIFTY REALTY": "Realty & Infrastructure",
        "NIFTY PSU BANK": "PSU Banks",
        "NIFTY MEDIA": "Telecom & Media",
        "NIFTY FIN SERVICE": "NBFC & Finance",
        "NIFTY INFRA": "Capital Goods & Engineering",
    }
    
    # Get Nifty 50 for relative strength (with retry)
    nifty_data = None
    for attempt in range(3):
        nifty_data = await redis.get("ohlc:NSE:NIFTY 50")
        if nifty_data:
            break
        await asyncio.sleep(0.5)
    
    if not nifty_data:
        logger.warning("⚠️ Could not fetch NIFTY 50 data for relative strength calculation")
        nifty_change = 0
    else:
        nifty_change = nifty_data.get("change_percent", 0)
    
    for index_name, sector_name in index_map.items():
        cache_key = f"ohlc:NSE:{index_name}"
        
        # Retry logic for sector index
        data = None
        for attempt in range(2):
            data = await redis.get(cache_key)
            if data:
                break
            await asyncio.sleep(0.3)
        
        if not data:
            logger.warning(f"⚠️ Skipping {sector_name}: no cached data for {index_name}")
            continue
            
        change_pct = data.get("change_percent", 0)
        rel_strength = change_pct - nifty_change
        
        # Get breadth from sector stocks
        sector_stocks = WATCHLIST["stocks"].get(sector_name, [])
        advancing = 0
        total = 0
        top_movers = []
        
        for stock in sector_stocks:
            stock_data = await redis.get(f"ohlc:NSE:{stock}")
            if stock_data:
                total += 1
                stock_change = stock_data.get("change_percent", 0)
                if stock_change > 0.05:
                    advancing += 1
                top_movers.append({
                    "symbol": stock,
                    "change_percent": stock_change
                })
        
        # Sort top movers by change
        top_movers.sort(key=lambda x: x["change_percent"], reverse=True)
        
        # Classify regime
        if rel_strength > 1 and advancing / max(total, 1) > 0.5:
            regime = "leader"
            emoji = "🟢"
        elif rel_strength < -1:
            regime = "lagging"
            emoji = "🔴"
        else:
            regime = "neutral"
            emoji = "⚪"
        
        sectors.append({
            "name": sector_name,
            "index_name": index_name,
            "change_pct": change_pct,
            "relative_strength": round(rel_strength, 2),
            "breadth": {
                "advancing": advancing,
                "declining": total - advancing,
                "total": total,
                "pct_positive": advancing / max(total, 1) * 100
            },
            "regime": regime,
            "regime_emoji": emoji,
            "top_movers": top_movers[:3]
        })
    
    # Sort by relative strength
    sectors.sort(key=lambda x: x["relative_strength"], reverse=True)
    
    # Build snapshot
    snapshot = {
        "timestamp": now.strftime("%d %b %Y, %I:%M %p IST"),
        "timeframe": "5D",
        "nifty_change": nifty_change,
        "sectors": sectors,
        "status": "live" if sectors else "stale",
        "updated_at": now.isoformat()
    }
    
    # Cache snapshot
    await redis.set("sector_snapshot", snapshot, ttl=CACHE_TTL)
    logger.info(f"📊 Sector snapshot updated: {len(sectors)} sectors cached")
    
    return snapshot


async def run_update_cycle():
    """Run one complete update cycle using batch fetching."""
    all_symbols = get_all_symbols()
    
    # Separate indices from stocks (indices might need different handling)
    indices = [s for s in all_symbols if s.startswith("NIFTY") or s == "SENSEX"]
    stocks = [s for s in all_symbols if s not in indices]
    
    logger.info(f"🔄 Starting update cycle: {len(stocks)} stocks, {len(indices)} indices")
    
    # Get Dhan client
    dhan = get_dhan_client()
    
    total_success = 0
    total_failed = 0
    
    # Process stocks in batches (Dhan supports up to 1000 per request)
    for i in range(0, len(stocks), BATCH_SIZE):
        batch = stocks[i:i + BATCH_SIZE]
        logger.info(f"Processing batch {i//BATCH_SIZE + 1}/{(len(stocks)-1)//BATCH_SIZE + 1} ({len(batch)} symbols)")
        
        results = await fetch_and_cache_ohlc_batch(batch)
        total_success += results["success"]
        total_failed += results["failed"]
        
        # Small delay between batches
        if i + BATCH_SIZE < len(stocks):
            await asyncio.sleep(0.5)
    
    # Process indices using intraday API
    if indices:
        logger.info(f"Processing {len(indices)} indices using intraday API...")
        try:
            # Use new intraday OHLC method for indices
            index_data = await dhan.get_intraday_ohlc_for_indices(indices)
            
            if index_data:
                # Cache each index's data
                redis = get_redis_cache()
                for index_name, data in index_data.items():
                    cache_key = f"ohlc:NSE:{index_name}"
                    await redis.set(cache_key, data, ttl=CACHE_TTL)
                    logger.debug(f"✓ {index_name}: {data.get('last_price', 0):,.2f} ({data.get('change_percent', 0):+.2f}%)")
                    total_success += 1
                
                logger.info(f"✅ Fetched {len(index_data)} indices successfully")
            else:
                logger.warning(f"⚠️ No index data returned")
                total_failed += len(indices)
        except Exception as e:
            logger.error(f"❌ Error fetching indices: {e}")
            total_failed += len(indices)
    
    logger.info(f"✅ OHLC update complete: {total_success} success, {total_failed} failed")
    
    # Build sector snapshot
    await build_sector_snapshot()
    
    return {"success": total_success, "failed": total_failed}


async def cache_market_news():
    """
    Cache market news from Indian API.
    
    Fetches latest market news and caches in Redis with 4-hour TTL.
    Scheduled to run 4 times daily: 9 AM, 12 PM, 3 PM, 6 PM IST.
    """
    try:
        from src.data.indian_api_client import get_indian_api_client
        
        logger.info("📰 Fetching market news from Indian API...")
        
        # Get Redis client
        redis = get_redis_cache()
        
        indian_api = get_indian_api_client()
        news_items = await indian_api.get_market_news(limit=20)
        
        if news_items:
            # Cache in Redis (use "market_news" key for consistency)
            await redis.set(
                "market_news",
                news_items,
                ttl=14400  # 4 hours
            )
            
            logger.info(f"✅ Cached {len(news_items)} market news items")
            
            # Log first headline for verification
            if news_items:
                first_headline = news_items[0].get("title", "N/A")
                logger.info(f"   Top headline: {first_headline[:80]}...")
        else:
            logger.warning("⚠️ No news items fetched from Indian API")
            
    except Exception as e:
        logger.error(f"❌ Failed to cache market news: {e}")


async def run_continuous(interval_seconds: int = 120):
    """Run continuous update loop."""
    logger.info(f"🚀 Starting continuous mode (interval: {interval_seconds}s)")
    
    # Track last news fetch hour to avoid duplicates
    last_news_hour = None
    
    while True:
        try:
            # Run OHLC update cycle
            await run_update_cycle()
            
            # Check if it's time to fetch news (4 times daily: 9, 12, 15, 18 IST)
            IST = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(IST)
            current_hour = current_time.hour
            
            # News refresh hours
            news_hours = [9, 11, 12, 15, 18]
            
            if current_hour in news_hours and current_hour != last_news_hour:
                logger.info(f"📰 News refresh time ({current_hour}:00 IST)")
                await cache_market_news()
                last_news_hour = current_hour
            
            logger.info(f"💤 Sleeping for {interval_seconds}s...")
            await asyncio.sleep(interval_seconds)
            
        except KeyboardInterrupt:
            logger.info("🛑 Stopping worker...")
            break
        except Exception as e:
            logger.error(f"❌ Cycle failed: {e}")
            await asyncio.sleep(10)  # Brief pause before retry


async def main():
    """Main entry point."""
    # Check for loop mode
    loop_mode = "--loop" in sys.argv
    
    if loop_mode:
        await run_continuous(interval_seconds=120)  # 2 minutes
    else:
        await run_update_cycle()


if __name__ == "__main__":
    asyncio.run(main())
