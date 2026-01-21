#!/usr/bin/env python3
"""
Dhan Instruments Sync Script

Syncs instruments from Dhan segment-wise API to SQLite database.
Run this daily via cron at 2 AM IST.

Usage:
    python scripts/sync_dhan_segments.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.dhan_segment_instruments import get_dhan_instruments


async def main():
    print("=" * 70)
    print("DHAN INSTRUMENTS SYNC")
    print("=" * 70)
    
    try:
        # Initialize with NSE_EQ segment only (can add BSE_EQ if needed)
        print("\n📥 Initializing instruments storage...")
        instruments = await get_dhan_instruments(segments=["NSE_EQ"])
        
        # Force sync from API
        print("\n🔄 Syncing from Dhan API...")
        await instruments.sync_from_api()
        
        # Show stats
        stats = instruments.get_stats()
        
        print("\n" + "=" * 70)
        print("SYNC COMPLETE")
        print("=" * 70)
        print(f"\n📊 Total instruments: {stats['total_instruments']:,}")
        print(f"📦 Database size: {stats['db_size_kb']:.1f} KB")
        print(f"📅 Last sync: {stats['last_sync']}")
        
        print(f"\n📈 Segments:")
        for segment, count in stats['segments'].items():
            print(f"   {segment}: {count:,} instruments")
        
        print(f"\n💾 Cache:")
        print(f"   ISIN cache: {stats['cache']['isin_cache_size']}/1000 slots")
        print(f"   Symbol cache: {stats['cache']['symbol_cache_size']}/1000 slots")
        
        print("\n✅ Sync successful!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
