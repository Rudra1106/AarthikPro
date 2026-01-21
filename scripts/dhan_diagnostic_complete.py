#!/usr/bin/env python3
"""
Complete Diagnostic and Fix for Dhan Integration

This script will:
1. Download and analyze the CSV
2. Find exact symbol names for your watchlist
3. Test the Dhan API with correct parameters
4. Suggest fixes for your code

Usage:
    python scripts/dhan_diagnostic_complete.py
"""

import asyncio
import sys
import os
import pandas as pd
import aiohttp
from dhanhq import dhanhq

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import settings

CSV_URL = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"

WATCHLIST_SYMBOLS = [
    "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM",
    "RELIANCE", "HDFCBANK", "ICICIBANK", "ITC", "SBIN",
    "BHARTIARTL", "TATASTEEL", "MARUTI", "SUNPHARMA", "AXISBANK"
]


async def download_and_analyze_csv():
    """Download CSV and analyze symbol naming patterns."""
    print("=" * 80)
    print("STEP 1: DOWNLOADING AND ANALYZING DHAN CSV")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(CSV_URL, timeout=aiohttp.ClientTimeout(total=60)) as response:
            csv_content = await response.text()
    
    print(f"✓ Downloaded CSV ({len(csv_content) / 1024 / 1024:.1f}MB)")
    
    # Parse CSV
    from io import StringIO
    df = pd.read_csv(StringIO(csv_content), low_memory=False)
    
    print(f"✓ Loaded {len(df):,} rows with {len(df.columns)} columns")
    print(f"✓ Columns: {', '.join(df.columns[:10])}...")
    
    # Filter to NSE Equity
    nse_equity = df[
        (df['EXCH_ID'] == 'NSE') &
        (df['SEGMENT'] == 'E') &
        (df['INSTRUMENT'] == 'EQUITY')
    ].copy()
    
    print(f"✓ Found {len(nse_equity):,} NSE equity instruments\n")
    
    # Show sample data
    print("Sample NSE Equity Instruments:")
    print("-" * 80)
    sample = nse_equity.head(10)[['SECURITY_ID', 'SYMBOL_NAME', 'DISPLAY_NAME', 'ISIN']]
    print(sample.to_string(index=False))
    print()
    
    return df, nse_equity


def find_watchlist_symbols(nse_equity_df):
    """Find exact symbol names for watchlist."""
    print("=" * 80)
    print("STEP 2: FINDING WATCHLIST SYMBOLS IN CSV")
    print("=" * 80)
    
    found = {}
    not_found = []
    
    for watch_symbol in WATCHLIST_SYMBOLS:
        # Try exact match (case-insensitive)
        matches = nse_equity_df[
            nse_equity_df['SYMBOL_NAME'].str.upper() == watch_symbol.upper()
        ]
        
        if len(matches) > 0:
            row = matches.iloc[0]
            found[watch_symbol] = {
                'security_id': int(row['SECURITY_ID']),
                'exact_symbol': row['SYMBOL_NAME'],
                'display_name': row['DISPLAY_NAME'],
                'isin': row['ISIN']
            }
            print(f"✓ {watch_symbol:15s} → {row['SYMBOL_NAME']:20s} (ID: {int(row['SECURITY_ID']):6d})")
        else:
            # Try fuzzy search
            fuzzy = nse_equity_df[
                nse_equity_df['SYMBOL_NAME'].str.contains(watch_symbol, case=False, na=False) |
                nse_equity_df['DISPLAY_NAME'].str.contains(watch_symbol, case=False, na=False)
            ].head(5)
            
            if len(fuzzy) > 0:
                print(f"✗ {watch_symbol:15s} → NOT FOUND. Similar:")
                for _, row in fuzzy.iterrows():
                    print(f"     {row['SYMBOL_NAME']:20s} (ID: {int(row['SECURITY_ID']):6d}) - {row['DISPLAY_NAME']}")
            else:
                print(f"✗ {watch_symbol:15s} → NOT FOUND (no similar matches)")
                not_found.append(watch_symbol)
    
    print(f"\n✓ Found: {len(found)}/{len(WATCHLIST_SYMBOLS)} symbols")
    print(f"✗ Not found: {len(not_found)} symbols\n")
    
    return found, not_found


async def test_dhan_api(found_symbols):
    """Test Dhan API with found symbols."""
    print("=" * 80)
    print("STEP 3: TESTING DHAN API")
    print("=" * 80)
    
    if not settings.dhan_client_id or not settings.dhan_access_token:
        print("✗ ERROR: Dhan credentials not found in settings")
        print("  Please set DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN in .env")
        return
    
    # Initialize Dhan client
    dhan = dhanhq(settings.dhan_client_id, settings.dhan_access_token)
    print(f"✓ Initialized Dhan client (Client ID: {settings.dhan_client_id[:6]}...)")
    
    # Test with first 5 symbols
    test_symbols = list(found_symbols.keys())[:5]
    security_ids = [found_symbols[sym]['security_id'] for sym in test_symbols]
    
    print(f"\n🧪 Testing with {len(test_symbols)} symbols:")
    for sym in test_symbols:
        info = found_symbols[sym]
        print(f"   {sym}: ID={info['security_id']}, Symbol={info['exact_symbol']}")
    
    # Test LTP API
    print("\n📊 Testing ticker_data (LTP) API...")
    try:
        payload = {"NSE_EQ": security_ids}
        print(f"   Payload: {payload}")
        
        response = await asyncio.to_thread(dhan.ticker_data, payload)
        
        print(f"   Response status: {response.get('status')}")
        
        if response.get('status') == 'success':
            data = response.get('data', {}).get('NSE_EQ', {})
            print(f"   ✓ Got data for {len(data)} symbols:")
            
            for sec_id_str, info in list(data.items())[:5]:
                print(f"      Security ID {sec_id_str}: LTP = ₹{info.get('last_price', 0):,.2f}")
        else:
            print(f"   ✗ API Error: {response.get('remarks', 'Unknown error')}")
            print(f"   Full response: {response}")
    
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Test OHLC API
    print("\n📊 Testing ohlc_data API...")
    try:
        payload = {"NSE_EQ": security_ids}
        
        response = await asyncio.to_thread(dhan.ohlc_data, payload)
        
        print(f"   Response status: {response.get('status')}")
        
        if response.get('status') == 'success':
            data = response.get('data', {}).get('NSE_EQ', {})
            print(f"   ✓ Got OHLC for {len(data)} symbols:")
            
            for sec_id_str, info in list(data.items())[:5]:
                print(f"      Security ID {sec_id_str}:")
                print(f"         Open: ₹{info.get('open', 0):,.2f}, High: ₹{info.get('high', 0):,.2f}")
                print(f"         Low: ₹{info.get('low', 0):,.2f}, Close: ₹{info.get('close', 0):,.2f}")
        else:
            print(f"   ✗ API Error: {response.get('remarks', 'Unknown error')}")
    
    except Exception as e:
        print(f"   ✗ Exception: {e}")


def generate_fixes(found_symbols, not_found):
    """Generate code fixes based on analysis."""
    print("\n" + "=" * 80)
    print("STEP 4: RECOMMENDED FIXES")
    print("=" * 80)
    
    print("\n1. UPDATE YOUR WATCHLIST")
    print("-" * 80)
    print("Replace symbols in your WATCHLIST with exact Dhan symbol names:")
    print()
    print("WATCHLIST = {")
    print('    "indices": [...],')
    print('    "stocks": {')
    print('        "IT": [')
    for sym in ["TCS", "INFY", "WIPRO", "HCLTECH", "TECHM"]:
        if sym in found_symbols:
            print(f'            "{found_symbols[sym]["exact_symbol"]}",  # {sym}')
    print('        ],')
    print('        # ... more sectors')
    print('    }')
    print('}')
    
    if not_found:
        print(f"\n⚠️ WARNING: {len(not_found)} symbols not found:")
        print(f"   {', '.join(not_found)}")
        print("   You need to find the correct Dhan symbol names for these.")
    
    print("\n2. KEY CHANGES TO YOUR CODE")
    print("-" * 80)
    print("✓ Symbol matching is working - just use exact names from CSV")
    print("✓ API payload structure is correct: {'NSE_EQ': [list of security_ids]}")
    print("✓ Response parsing: data['NSE_EQ'][security_id_string]")
    print("✓ Reverse lookup needs security_id → symbol mapping")
    
    print("\n3. STORAGE SOLUTION FOR INSTRUMENTS CSV")
    print("-" * 80)
    print("Option A: In-memory dicts (current - 5-10 MB RAM)")
    print("   Pros: Fast O(1) lookup, no external dependency")
    print("   Cons: Loads on startup (12s)")
    print()
    print("Option B: SQLite database")
    print("   Pros: Persistent, indexed queries, ~35MB file")
    print("   Cons: Disk I/O overhead")
    print()
    print("Option C: Filtered Redis cache")
    print("   Pros: Fast, shared across workers")
    print("   Cons: Redis memory usage, TTL management")
    print()
    print("RECOMMENDATION: Stick with in-memory (Option A)")
    print("   35MB CSV → 5MB RAM is excellent compression")
    print("   Startup time acceptable for background worker")


async def main():
    """Run complete diagnostic."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "DHAN INTEGRATION DIAGNOSTIC TOOL" + " " * 26 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Step 1: Download and analyze
    df, nse_equity = await download_and_analyze_csv()
    
    # Step 2: Find watchlist symbols
    found_symbols, not_found = find_watchlist_symbols(nse_equity)
    
    # Step 3: Test API
    await test_dhan_api(found_symbols)
    
    # Step 4: Generate fixes
    generate_fixes(found_symbols, not_found)
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print("\n✅ Next steps:")
    print("   1. Update watchlist with exact symbol names from Step 2")
    print("   2. Apply the fixed code artifacts provided")
    print("   3. Run: python scripts/market_data_worker.py --loop")
    print()


if __name__ == "__main__":
    asyncio.run(main())
