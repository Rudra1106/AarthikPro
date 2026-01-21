"""
One-time script to preload Dhan instruments into Redis.

This downloads the Dhan CSV once and caches all NSE_EQ symbols in Redis.
Run this once, then the instruments cache will be instant.

Usage:
    python scripts/preload_dhan_instruments.py
"""

import asyncio
import sys
from pathlib import Path
import csv
import aiohttp

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.redis_client import get_redis_cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def preload_instruments():
    """Download Dhan CSV and cache all NSE equity instruments."""
    
    url = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
    redis = get_redis_cache()
    
    logger.info("Downloading Dhan instruments CSV...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                logger.error(f"Failed to download CSV: {response.status}")
                return False
            
            content = await response.text()
            logger.info(f"Downloaded {len(content) / 1024 / 1024:.1f}MB CSV")
    
    # Parse CSV
    lines = content.split('\n')
    reader = csv.DictReader(lines)
    
    nse_count = 0
    bse_count = 0
    
    logger.info("Parsing and caching instruments...")
    
    for row in reader:
        exch_id = row.get('EXCH_ID')
        segment = row.get('SEGMENT')
        security_id = row.get('SECURITY_ID')
        symbol_name = row.get('SYMBOL_NAME')
        
        if not all([exch_id, segment, security_id, symbol_name]):
            continue
        
        # Cache NSE Equity
        if exch_id == 'NSE' and segment == 'E':
            cache_key = f"dhan:instruments:NSE_EQ:{symbol_name}"
            await redis.set(cache_key, int(security_id), ttl=86400 * 7)  # 7 days
            nse_count += 1
        
        # Cache BSE Equity
        elif exch_id == 'BSE' and segment == 'E':
            cache_key = f"dhan:instruments:BSE_EQ:{symbol_name}"
            await redis.set(cache_key, int(security_id), ttl=86400 * 7)
            bse_count += 1
    
    logger.info(f"✅ Cached {nse_count} NSE symbols and {bse_count} BSE symbols")
    logger.info(f"Cache TTL: 7 days")
    
    # Test a few symbols
    logger.info("\nTesting cached symbols:")
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'WIPRO', 'HDFCBANK']
    
    for symbol in test_symbols:
        sec_id = await redis.get(f"dhan:instruments:NSE_EQ:{symbol}")
        logger.info(f"  {symbol}: {sec_id}")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(preload_instruments())
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
