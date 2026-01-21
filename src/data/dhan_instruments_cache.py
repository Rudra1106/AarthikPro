"""
Dhan Instruments Cache - Optimized Segmentwise API Version

Key improvements over previous version:
1. Uses Dhan's segmentwise API instead of 35MB full CSV
2. Downloads only needed segments (NSE_EQ, BSE_EQ)
3. Faster initialization (~2s vs ~12s)
4. Smaller download (~3MB vs ~35MB)
5. ISIN-based lookups with reverse mapping
"""

import asyncio
import logging
import pandas as pd
import aiohttp
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from io import StringIO

logger = logging.getLogger(__name__)


class DhanInstrumentsCache:
    """
    Production-grade instruments cache using Dhan's segmentwise API.
    
    Features:
    - Segmentwise downloads (NSE_EQ, BSE_EQ)
    - ISIN-based primary lookup
    - Symbol-based fallback
    - Reverse lookup (security_id → symbol)
    - Memory efficient (~2MB)
    """
    
    # Dhan segmentwise API endpoints
    SEGMENT_URLS = {
        "NSE_EQ": "https://api.dhan.co/v2/instrument/NSE_EQ",
        "BSE_EQ": "https://api.dhan.co/v2/instrument/BSE_EQ",
    }
    
    def __init__(self):
        # Primary lookup: ISIN → security_id (NSE preferred)
        self._isin_to_id: Dict[str, int] = {}
        
        # Forward lookup: symbol → security_id
        self._instruments: Dict[str, Dict[str, int]] = {}  # {exchange: {symbol: security_id}}
        
        # Reverse lookup: security_id → symbol (for response parsing)
        self._id_to_symbol: Dict[str, Dict[int, str]] = {}  # {exchange: {security_id: symbol}}
        
        self._last_refresh: Optional[datetime] = None
        self._refresh_lock = asyncio.Lock()
    
    async def initialize(self, dhan_client=None):
        """Initialize cache by downloading segmentwise CSVs."""
        async with self._refresh_lock:
            if self._isin_to_id and self._last_refresh:
                return
            
            logger.info("Initializing Dhan instruments cache (segmentwise API)...")
            
            try:
                async with aiohttp.ClientSession() as session:
                    # Download segments in parallel
                    tasks = []
                    for segment, url in self.SEGMENT_URLS.items():
                        tasks.append(self._download_segment(session, segment, url))
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    total_instruments = 0
                    for segment, result in zip(self.SEGMENT_URLS.keys(), results):
                        if isinstance(result, Exception):
                            logger.error(f"Failed to download {segment}: {result}")
                        else:
                            df, size_mb = result
                            count = await self._process_segment(segment, df)
                            total_instruments += count
                            logger.info(f"✓ {segment}: {count:,} instruments ({size_mb:.1f}MB)")
                
                self._last_refresh = datetime.now()
                
                nse_count = len(self._instruments.get('NSE_EQ', {}))
                bse_count = len(self._instruments.get('BSE_EQ', {}))
                isin_count = len(self._isin_to_id)
                
                logger.info(f"✅ Loaded {isin_count:,} ISINs, {nse_count:,} NSE symbols, {bse_count:,} BSE symbols")
                logger.info(f"Memory usage: ~{(isin_count + nse_count + bse_count) * 50 / 1024 / 1024:.1f}MB")
                
            except Exception as e:
                logger.error(f"Failed to initialize instruments cache: {e}")
                import traceback
                traceback.print_exc()
                raise
    
    async def _download_segment(self, session: aiohttp.ClientSession, segment: str, url: str) -> Tuple[pd.DataFrame, float]:
        """Download a single segment CSV."""
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30), allow_redirects=True) as response:
            if response.status != 200:
                raise Exception(f"HTTP {response.status}")
            
            csv_content = await response.text()
            size_mb = len(csv_content) / 1024 / 1024
            
            # Parse CSV
            df = pd.read_csv(StringIO(csv_content), low_memory=False)
            
            return df, size_mb
    
    async def _process_segment(self, segment: str, df: pd.DataFrame) -> int:
        """Process a segment DataFrame and populate caches."""
        count = 0
        
        # Determine exchange key
        if segment == "NSE_EQ":
            exchange_key = "NSE_EQ"
        elif segment == "BSE_EQ":
            exchange_key = "BSE_EQ"
        else:
            return 0
        
        # Initialize dicts
        if exchange_key not in self._instruments:
            self._instruments[exchange_key] = {}
        if exchange_key not in self._id_to_symbol:
            self._id_to_symbol[exchange_key] = {}
        
        # Process rows - detailed CSV has SECURITY_ID, SYMBOL_NAME, ISIN
        for _, row in df.iterrows():
            try:
                # Column names from DETAILED CSV (not compact)
                security_id = int(row['SECURITY_ID'])
                symbol = str(row['SYMBOL_NAME']).strip()
                isin = row.get('ISIN')  # ISIN column available in detailed CSV
                
                if pd.isna(security_id) or pd.isna(symbol) or symbol == 'nan':
                    continue
                
                # Build ISIN lookup (NSE preferred over BSE)
                if not pd.isna(isin) and isin != 'NA':
                    isin_str = str(isin).strip()
                    # NSE takes priority over BSE for ISIN mapping
                    if isin_str not in self._isin_to_id or segment.startswith('NSE'):
                        self._isin_to_id[isin_str] = security_id
                
                # Forward lookup
                self._instruments[exchange_key][symbol] = security_id
                
                # Reverse lookup
                self._id_to_symbol[exchange_key][security_id] = symbol
                
                count += 1
                
            except (KeyError, ValueError) as e:
                continue
        
        return count
    
    def search_symbol(self, symbol: str, exchange: str = "NSE_EQ", limit: int = 10) -> List[Tuple[str, int]]:
        """Search for symbols matching the query (fuzzy search)."""
        if exchange not in self._instruments:
            return []
        
        symbol_upper = symbol.upper()
        matches = []
        
        for sym, sec_id in self._instruments[exchange].items():
            if symbol_upper in sym.upper():
                matches.append((sym, sec_id))
                if len(matches) >= limit:
                    break
        
        return matches
    
    async def get_security_id_by_isin(self, isin: str) -> Optional[int]:
        """
        Get security ID by ISIN.
        
        Note: Since compact CSV doesn't have ISIN, this relies on
        the ISIN mapping file (dhan_symbol_mapping.py) being used
        in the Dhan client.
        """
        if not isin or isin == 'NA':
            return None
        return self._isin_to_id.get(isin.upper())
    
    async def get_security_id(self, symbol: str, exchange: str = "NSE_EQ", isin: Optional[str] = None) -> Optional[int]:
        """Get security ID for a symbol."""
        # Check if refresh needed
        if self._last_refresh and (datetime.now() - self._last_refresh) > timedelta(hours=24):
            logger.info("Instruments cache expired, refreshing...")
            asyncio.create_task(self._refresh_cache())
        
        # PRIORITY 1: ISIN lookup (if provided)
        if isin:
            sec_id = await self.get_security_id_by_isin(isin)
            if sec_id:
                return sec_id
        
        # PRIORITY 2: NSE_EQ symbol lookup
        if 'NSE_EQ' in self._instruments:
            sec_id = self._instruments['NSE_EQ'].get(symbol)
            if sec_id:
                return sec_id
            
            # Try uppercase
            sec_id = self._instruments['NSE_EQ'].get(symbol.upper())
            if sec_id:
                return sec_id
        
        # PRIORITY 3: BSE_EQ fallback
        if 'BSE_EQ' in self._instruments:
            sec_id = self._instruments['BSE_EQ'].get(symbol)
            if sec_id:
                return sec_id
            
            sec_id = self._instruments['BSE_EQ'].get(symbol.upper())
            if sec_id:
                return sec_id
        
        # Log failed lookup with suggestions
        matches = self.search_symbol(symbol, exchange, limit=5)
        if matches:
            suggestions = [f"{s} ({sid})" for s, sid in matches[:3]]
            logger.warning(f"Symbol '{symbol}' not found. Similar: {', '.join(suggestions)}")
        else:
            logger.warning(f"Symbol '{symbol}' not found and no similar matches")
        
        return None
    
    async def get_security_ids(self, symbols: list, exchange: str = "NSE_EQ") -> Dict[str, int]:
        """Get security IDs for multiple symbols."""
        result = {}
        not_found = []
        
        # Check NSE first
        if 'NSE_EQ' in self._instruments:
            for symbol in symbols:
                sec_id = self._instruments['NSE_EQ'].get(symbol)
                if not sec_id:
                    sec_id = self._instruments['NSE_EQ'].get(symbol.upper())
                
                if sec_id:
                    result[symbol] = sec_id
                else:
                    not_found.append(symbol)
        
        # Check BSE for remaining
        if 'BSE_EQ' in self._instruments and not_found:
            remaining = []
            for symbol in not_found:
                sec_id = self._instruments['BSE_EQ'].get(symbol)
                if not sec_id:
                    sec_id = self._instruments['BSE_EQ'].get(symbol.upper())
                
                if sec_id:
                    result[symbol] = sec_id
                else:
                    remaining.append(symbol)
            not_found = remaining
        
        # Log failures
        if not_found:
            logger.warning(f"Failed to find {len(not_found)} symbols: {not_found[:5]}...")
        
        return result
    
    def get_symbol_from_id(self, security_id: int, exchange: str = "NSE_EQ") -> Optional[str]:
        """Get symbol from security ID (reverse lookup)."""
        if exchange in self._id_to_symbol:
            return self._id_to_symbol[exchange].get(security_id)
        return None
    
    async def _refresh_cache(self):
        """Background refresh of instruments cache."""
        async with self._refresh_lock:
            try:
                self._isin_to_id.clear()
                self._instruments.clear()
                self._id_to_symbol.clear()
                self._last_refresh = None
                await self.initialize()
            except Exception as e:
                logger.error(f"Failed to refresh instruments cache: {e}")


# Singleton instance
_dhan_instruments_cache: Optional[DhanInstrumentsCache] = None


def get_dhan_instruments_cache() -> DhanInstrumentsCache:
    """Get singleton instruments cache instance."""
    global _dhan_instruments_cache
    if _dhan_instruments_cache is None:
        _dhan_instruments_cache = DhanInstrumentsCache()
    return _dhan_instruments_cache
