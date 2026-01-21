#!/usr/bin/env python3
"""
MongoDB Cleanup Script
Removes raw extracted data to free space while keeping metadata
"""

import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "financial_data")

def cleanup_mongodb():
    """Clean up MongoDB to free space"""
    
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    
    print("=" * 60)
    print("MONGODB CLEANUP - RAW DATA REMOVAL")
    print("=" * 60)
    
    # Get current sizes
    stats_before = db.command("dbStats")
    print(f"\n📊 Current Database Size: {stats_before['dataSize'] / 1024 / 1024:.2f} MB")
    
    collections_to_check = ['text_chunks', 'extraction_logs', 'documents']
    
    for coll_name in collections_to_check:
        if coll_name in db.list_collection_names():
            count = db[coll_name].count_documents({})
            print(f"   {coll_name}: {count} documents")
    
    print("\n" + "=" * 60)
    print("CLEANUP OPTIONS")
    print("=" * 60)
    
    # Option 1: Delete cold data (pre-2022)
    print("\n1️⃣  Delete COLD data (pre-2022)")
    cold_count = db.text_chunks.count_documents({"temperature": "cold"})
    print(f"   Will delete: {cold_count} cold chunks")
    print(f"   Estimated space freed: ~{cold_count * 0.5:.0f} MB")
    
    # Option 2: Delete warm data (2022-2023)
    print("\n2️⃣  Delete WARM data (2022-2023)")
    warm_count = db.text_chunks.count_documents({"temperature": "warm"})
    print(f"   Will delete: {warm_count} warm chunks")
    print(f"   Estimated space freed: ~{warm_count * 0.5:.0f} MB")
    
    # Option 3: Keep only metadata, delete all text
    print("\n3️⃣  Delete ALL raw text (keep only metadata)")
    all_count = db.text_chunks.count_documents({})
    print(f"   Will delete: {all_count} text chunks")
    print(f"   Estimated space freed: ~{all_count * 0.5:.0f} MB")
    print("   ⚠️  Will keep document metadata for tracking")
    
    # Option 4: Nuclear - delete everything
    print("\n4️⃣  NUCLEAR: Delete all extraction data")
    print("   ⚠️  WARNING: This deletes EVERYTHING")
    print("   Use only if starting fresh")
    
    print("\n" + "=" * 60)
    choice = input("\nSelect option (1-4) or 'q' to quit: ").strip()
    
    if choice == 'q':
        print("❌ Cancelled")
        return
    
    # Confirm
    confirm = input(f"\n⚠️  Confirm deletion (type 'DELETE' to proceed): ").strip()
    if confirm != 'DELETE':
        print("❌ Cancelled")
        return
    
    print("\n🗑️  Starting cleanup...")
    
    if choice == '1':
        # Delete cold data
        result = db.text_chunks.delete_many({"temperature": "cold"})
        print(f"✅ Deleted {result.deleted_count} cold chunks")
        
    elif choice == '2':
        # Delete warm data
        result = db.text_chunks.delete_many({"temperature": "warm"})
        print(f"✅ Deleted {result.deleted_count} warm chunks")
        
    elif choice == '3':
        # Delete all text chunks
        result = db.text_chunks.delete_many({})
        print(f"✅ Deleted {result.deleted_count} text chunks")
        print("✅ Kept document metadata")
        
    elif choice == '4':
        # Nuclear option
        for coll in ['text_chunks', 'extraction_logs']:
            if coll in db.list_collection_names():
                result = db[coll].delete_many({})
                print(f"✅ Deleted {result.deleted_count} documents from {coll}")
    
    # Compact database
    print("\n🔄 Compacting database...")
    try:
        db.command("compact", "text_chunks")
        print("✅ Compaction complete")
    except Exception as e:
        print(f"⚠️  Compaction not available on free tier: {e}")
    
    # Get new sizes
    stats_after = db.command("dbStats")
    freed_mb = (stats_before['dataSize'] - stats_after['dataSize']) / 1024 / 1024
    
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"📊 Database size: {stats_before['dataSize'] / 1024 / 1024:.2f} MB → {stats_after['dataSize'] / 1024 / 1024:.2f} MB")
    print(f"💾 Space freed: {freed_mb:.2f} MB")
    print(f"📈 Remaining: {stats_after['dataSize'] / 1024 / 1024:.2f} MB / 512 MB")
    
    client.close()

if __name__ == "__main__":
    cleanup_mongodb()
