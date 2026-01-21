"""
Check DataFrame columns after loading
"""
import asyncio
import aiohttp
import pandas as pd
from io import StringIO

async def main():
    url = "https://images.dhan.co/api-data/api-scrip-master-detailed.csv"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
            csv_content = await response.text()
    
    df = pd.read_csv(StringIO(csv_content), low_memory=False)
    
    print(f"DataFrame columns ({len(df.columns)}):")
    for i, col in enumerate(df.columns):
        print(f"  {i}: '{col}'")
    
    print(f"\nFirst row:")
    first_row = df.iloc[0]
    print(f"  EXCH_ID: {first_row.get('EXCH_ID')}")
    print(f"  SEGMENT: {first_row.get('SEGMENT')}")
    print(f"  SECURITY_ID: {first_row.get('SECURITY_ID')}")
    print(f"  ISIN: {first_row.get('ISIN')}")
    print(f"  SYMBOL_NAME: {first_row.get('SYMBOL_NAME')}")
    print(f"  DISPLAY_NAME: {first_row.get('DISPLAY_NAME')}")
    
    # Find RELIANCE
    print(f"\nSearching for RELIANCE (security_id=2885):")
    reliance = df[df['SECURITY_ID'] == 2885]
    if not reliance.empty:
        r = reliance.iloc[0]
        print(f"  EXCH_ID: {r['EXCH_ID']}")
        print(f"  SYMBOL_NAME: {r['SYMBOL_NAME']}")
        print(f"  DISPLAY_NAME: {r['DISPLAY_NAME']}")

asyncio.run(main())
