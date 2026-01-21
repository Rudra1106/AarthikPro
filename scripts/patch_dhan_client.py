"""
Quick fix script to update Dhan client to use ISIN lookups
"""
import sys

# Read the current dhan_client.py
with open('/Users/rudra/Documents/AarthikAi/src/data/dhan_client.py', 'r') as f:
    content = f.read()

# Find and replace the _get_security_ids method
old_method = '''    async def _get_security_ids(self, symbols: List[str], exchange: str) -> List[int]:
        """Get security IDs for symbols using instruments cache."""
        from src.data.dhan_instruments_cache import get_dhan_instruments_cache
        
        # Initialize cache on first use
        if not self._instruments_initialized:
            cache_obj = get_dhan_instruments_cache()
            await cache_obj.initialize(self.dhan)
            self._instruments_initialized = True
            logger.info("✅ Dhan instruments cache initialized")
        
        cache = get_dhan_instruments_cache()
        ids_map = await cache.get_security_ids(symbols, exchange)
        
        if not ids_map:
            logger.warning(f"No security IDs found for symbols: {symbols[:5]}... on {exchange}")
        
        return list(ids_map.values())'''

new_method = '''    async def _get_security_ids(self, symbols: List[str], exchange: str) -> List[int]:
        """Get security IDs for symbols using ISIN-based lookup."""
        from src.data.dhan_instruments_cache import get_dhan_instruments_cache
        from src.data.dhan_symbol_mapping import SYMBOL_TO_ISIN
        
        # Initialize cache on first use
        if not self._instruments_initialized:
            cache_obj = get_dhan_instruments_cache()
            await cache_obj.initialize(self.dhan)
            self._instruments_initialized = True
            logger.info("✅ Dhan instruments cache initialized")
        
        cache = get_dhan_instruments_cache()
        security_ids = []
        found_symbols = []
        missing_symbols = []
        
        # Use ISIN-based lookup for each symbol
        for symbol in symbols:
            isin = SYMBOL_TO_ISIN.get(symbol)
            if isin:
                sec_id = await cache.get_security_id_by_isin(isin)
                if sec_id:
                    security_ids.append(sec_id)
                    found_symbols.append(symbol)
                else:
                    missing_symbols.append(f"{symbol} (ISIN: {isin})")
            else:
                # Fallback to symbol-based lookup
                sec_id = await cache.get_security_id(symbol, exchange)
                if sec_id:
                    security_ids.append(sec_id)
                    found_symbols.append(symbol)
                else:
                    missing_symbols.append(symbol)
        
        if missing_symbols:
            logger.warning(f"No security IDs found for {len(missing_symbols)} symbols: {missing_symbols[:5]}...")
        
        if found_symbols:
            logger.info(f"✓ Found security IDs for {len(found_symbols)}/{len(symbols)} symbols via ISIN lookup")
        
        return security_ids'''

if old_method in content:
    content = content.replace(old_method, new_method)
    with open('/Users/rudra/Documents/AarthikAi/src/data/dhan_client.py', 'w') as f:
        f.write(content)
    print("✅ Successfully updated dhan_client.py to use ISIN lookups")
else:
    print("❌ Could not find the method to replace")
    print("Method might have already been updated or has different formatting")
