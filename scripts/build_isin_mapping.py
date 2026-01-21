#!/usr/bin/env python3
"""
Auto ISIN Mapper - Build Complete Symbol to ISIN Mapping

This script:
1. Fetches NSE_EQ segment from Dhan API
2. Extracts all symbol → ISIN mappings
3. Generates Python code for dhan_symbol_mapping.py
4. Shows missing symbols from your watchlist

Usage:
    python scripts/build_isin_mapping.py
"""

import asyncio
import aiohttp
import sys
from pathlib import Path
from typing import Dict, Set
from collections import defaultdict

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

# Your current watchlist symbols (from the logs)
WATCHLIST_SYMBOLS = {
    # IT
    "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM", "MPHASIS", 
    "COFORGE", "PERSISTENT", "LTTS",
    
    # Banking
    "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "INDUSINDBK",
    "FEDERALBNK", "IDFCFIRSTB", "BANDHANBNK", "AUBANK",
    
    # PSU Banks
    "SBIN", "BANKBARODA", "CANBK", "PNB", "INDIANB", "UNIONBANK",
    
    # NBFC
    "BAJFINANCE", "BAJAJFINSV", "CHOLAFIN", "MUTHOOTFIN", 
    "SHRIRAMFIN", "POONAWALLA", "LICHSGFIN",
    
    # Metals
    "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "COALINDIA",
    "NMDC", "JINDALSTEL", "SAIL", "NATIONALUM",
    
    # Auto
    "MARUTI", "M&M", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO",
    "TVSMOTOR", "ASHOKLEY", "MOTHERSON", "BOSCHLTD", "TATAMOTORS",
    
    # Pharma
    "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "APOLLOHOSP",
    "MAXHEALTH", "FORTIS", "TORNTPHARM", "LUPIN", "AUROPHARMA",
    
    # FMCG
    "ITC", "HINDUNILVR", "NESTLEIND", "BRITANNIA", "MARICO",
    "DABUR", "GODREJCP", "COLPAL", "TATACONSUM", "VBL",
    
    # Energy
    "RELIANCE", "ONGC", "NTPC", "POWERGRID", "ADANIGREEN",
    "ADANIENSOL", "TATAPOWER", "NHPC", "SJVN", "GAIL", "BPCL",
    
    # Realty
    "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "BRIGADE",
    "LODHA", "PHOENIXLTD",
    
    # Capital Goods
    "LT", "SIEMENS", "ABB", "HAVELLS", "BHEL",
    "CUMMINSIND", "THERMAX", "VOLTAS",
    
    # Cement
    "ULTRACEMCO", "SHREECEM", "AMBUJACEM", "ACC", "DALBHARAT",
    "RAMCOCEM", "JKCEMENT", "GRASIM",
    
    # Telecom
    "BHARTIARTL", "ZEEL", "PVRINOX",
    
    # Insurance
    "SBILIFE", "HDFCLIFE", "ICICIPRULI", "LICI", "NIACL",
    
    # Consumer Durables
    "TITAN", "CROMPTON", "WHIRLPOOL", "DIXON",
    
    # Chemicals
    "PIDILITIND", "SRF", "ATUL", "DEEPAKNTR", "NAVINFLUOR",
    
    # Logistics
    "ADANIPORTS", "CONCOR", "DELHIVERY",
}


async def fetch_nse_instruments():
    """Fetch all NSE_EQ instruments from Dhan API."""
    url = "https://api.dhan.co/v2/instrument/NSE_EQ"
    
    print("📥 Fetching NSE_EQ instruments from Dhan API...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30), allow_redirects=True) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch: HTTP {response.status}")
            
            # Parse CSV
            import pandas as pd
            from io import StringIO
            csv_content = await response.text()
            df = pd.read_csv(StringIO(csv_content), low_memory=False)
            
            print(f"✅ Fetched {len(df):,} NSE_EQ instruments")
            
            return df


def build_symbol_to_isin_map(df) -> Dict[str, str]:
    """Build symbol → ISIN mapping from instruments."""
    symbol_to_isin = {}
    
    for _, row in df.iterrows():
        symbol = str(row.get('SYMBOL_NAME', '')).strip()
        isin = str(row.get('ISIN', '')).strip()
        
        if not symbol or not isin or isin == 'NA' or symbol == 'nan':
            continue
        
        # Store mapping
        symbol_to_isin[symbol] = isin
    
    print(f"✅ Built {len(symbol_to_isin):,} symbol → ISIN mappings")
    
    return symbol_to_isin


def find_watchlist_isins(symbol_to_isin: Dict[str, str]):
    """Find ISINs for watchlist symbols using fuzzy matching."""
    found = {}
    fuzzy_matches = {}
    missing = []
    
    for symbol in WATCHLIST_SYMBOLS:
        # Try exact match first
        if symbol in symbol_to_isin:
            found[symbol] = symbol_to_isin[symbol]
            continue
        
        # Fuzzy match
        symbol_upper = symbol.upper()
        matches = []
        
        for dhan_symbol, isin in symbol_to_isin.items():
            dhan_upper = dhan_symbol.upper()
            
            # Check if watchlist symbol is in Dhan symbol
            if symbol_upper in dhan_upper:
                matches.append((dhan_symbol, isin))
            # Check if Dhan symbol starts with watchlist symbol
            elif dhan_upper.startswith(symbol_upper):
                matches.append((dhan_symbol, isin))
        
        if matches:
            # Pick the shortest match (most likely correct)
            best_match = min(matches, key=lambda x: len(x[0]))
            fuzzy_matches[symbol] = best_match
            found[symbol] = best_match[1]  # Use the ISIN
        else:
            missing.append(symbol)
    
    print("\n" + "=" * 80)
    print("WATCHLIST COVERAGE ANALYSIS")
    print("=" * 80)
    
    print(f"\n✅ Found: {len(found)}/{len(WATCHLIST_SYMBOLS)} symbols")
    print(f"⚠️ Fuzzy matches: {len(fuzzy_matches)}")
    print(f"❌ Missing: {len(missing)}")
    
    if fuzzy_matches:
        print(f"\n⚠️ Fuzzy matches (verify these):")
        for symbol, (dhan_symbol, isin) in sorted(fuzzy_matches.items())[:20]:
            print(f"   {symbol:20s} → {dhan_symbol:40s} ({isin})")
    
    if missing:
        print(f"\n❌ Not found ({len(missing)}):")
        for symbol in missing:
            print(f"   {symbol}")
    
    return found, fuzzy_matches, missing


def generate_mapping_file(found: Dict[str, str], output_file: str):
    """Generate complete ISIN mapping file."""
    
    print(f"\n📝 Generating mapping file with {len(found):,} symbols...")
    
    # Generate Python code
    code = '''"""
Dhan Symbol to ISIN Mapping - Auto-Generated

Complete mapping for all watchlist symbols.
Generated from Dhan NSE_EQ segment data.

Usage:
    from src.data.dhan_symbol_mapping import SYMBOL_TO_ISIN
    isin = SYMBOL_TO_ISIN.get("RELIANCE")
"""

SYMBOL_TO_ISIN = {
'''
    
    # Sort by symbol name
    for symbol in sorted(found.keys()):
        isin = found[symbol]
        code += f'    "{symbol}": "{isin}",\n'
    
    code += '}\n\n'
    code += '# Reverse mapping\n'
    code += 'ISIN_TO_SYMBOL = {v: k for k, v in SYMBOL_TO_ISIN.items()}\n'
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(code)
    
    print(f"✅ Saved to: {output_file}")
    print(f"   Symbols: {len(found):,}")


async def main():
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "DHAN ISIN MAPPER - AUTO GENERATOR" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    # Fetch instruments
    df = await fetch_nse_instruments()
    
    # Build mapping
    symbol_to_isin = build_symbol_to_isin_map(df)
    
    # Find watchlist ISINs
    found, fuzzy_matches, missing = find_watchlist_isins(symbol_to_isin)
    
    # Generate mapping file
    output_file = "src/data/dhan_symbol_mapping.py"
    generate_mapping_file(found, output_file)
    
    print("\n✅ Done! Next steps:")
    print("   1. Review fuzzy matches above")
    print("   2. Restart market data worker to use new mappings")
    print("   3. Test with: python scripts/test_dhan_complete.py")
    
    return 0 if len(missing) == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
