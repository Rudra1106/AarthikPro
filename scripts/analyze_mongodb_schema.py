"""
MongoDB Database Schema Analyzer.

Connects to the production MongoDB database and analyzes the structure
of all stock-related collections to ensure complete data utilization.
"""
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient


async def analyze_database():
    """Analyze MongoDB database structure."""
    
    # Connect to MongoDB
    MONGODB_URI = "mongodb+srv://aarthikaibot:xjJ0Dh1wMmCNr5p6@aarthik.m9cjl1m.mongodb.net/PORTFOLIO_MANAGER"
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client["PORTFOLIO_MANAGER"]
    
    print("="*80)
    print("MONGODB DATABASE ANALYSIS")
    print("="*80)
    
    # List all collections
    collections = await db.list_collection_names()
    print(f"\n📁 Total Collections: {len(collections)}")
    print(f"Collections: {', '.join(collections)}\n")
    
    # Analyze key collections
    target_collections = [
        "stock_corporate_actions",
        "stock_documents", 
        "stock_financials",
        "stock_generals"
    ]
    
    for collection_name in target_collections:
        if collection_name not in collections:
            print(f"⚠️  Collection '{collection_name}' not found!")
            continue
        
        await analyze_collection(db, collection_name)
    
    await client.close()


async def analyze_collection(db, collection_name: str):
    """Analyze a specific collection."""
    collection = db[collection_name]
    
    print("="*80)
    print(f"📊 COLLECTION: {collection_name}")
    print("="*80)
    
    # Get document count
    count = await collection.count_documents({})
    print(f"\n📈 Total Documents: {count:,}")
    
    # Get sample document
    sample = await collection.find_one({})
    
    if not sample:
        print("❌ No documents found in collection")
        return
    
    # Analyze schema
    print(f"\n🔍 Schema Analysis:")
    print(f"Top-level fields: {len(sample.keys())}")
    
    # Print field structure
    print(f"\n📋 Field Structure:")
    for key, value in sample.items():
        if key == "_id":
            continue
        
        value_type = type(value).__name__
        
        if isinstance(value, dict):
            print(f"  • {key}: {value_type} ({len(value)} keys)")
            # Show nested keys
            nested_keys = list(value.keys())[:5]
            print(f"    └─ Keys: {', '.join(nested_keys)}{'...' if len(value) > 5 else ''}")
        
        elif isinstance(value, list):
            list_len = len(value)
            print(f"  • {key}: {value_type} ({list_len} items)")
            if list_len > 0:
                first_item = value[0]
                if isinstance(first_item, dict):
                    item_keys = list(first_item.keys())[:5]
                    print(f"    └─ Item keys: {', '.join(item_keys)}{'...' if len(first_item) > 5 else ''}")
                else:
                    print(f"    └─ Item type: {type(first_item).__name__}")
        
        else:
            # Show sample value for primitives
            sample_value = str(value)[:50]
            print(f"  • {key}: {value_type} = {sample_value}{'...' if len(str(value)) > 50 else ''}")
    
    # Special handling for stock_documents
    if collection_name == "stock_documents":
        await analyze_stock_documents(collection, sample)
    
    # Special handling for stock_financials
    elif collection_name == "stock_financials":
        await analyze_stock_financials(collection, sample)
    
    # Special handling for stock_generals
    elif collection_name == "stock_generals":
        await analyze_stock_generals(collection, sample)
    
    # Special handling for stock_corporate_actions
    elif collection_name == "stock_corporate_actions":
        await analyze_stock_corporate_actions(collection, sample)
    
    print()


async def analyze_stock_documents(collection, sample: Dict):
    """Analyze stock_documents collection in detail."""
    print(f"\n🔎 DETAILED ANALYSIS: stock_documents")
    
    # Check for annual_reports
    if "annual_reports" in sample:
        reports = sample["annual_reports"]
        print(f"\n  📄 Annual Reports: {len(reports)} reports")
        if reports:
            print(f"     Sample: {reports[0]}")
    
    # Check for concalls
    if "concalls" in sample:
        concalls = sample["concalls"]
        print(f"\n  📞 Concalls: {len(concalls)} concalls")
        if concalls:
            print(f"     Sample: {concalls[0]}")
    
    # Check for announcements
    if "announcements" in sample or "recent_announcements" in sample:
        announcements = sample.get("announcements") or sample.get("recent_announcements", [])
        print(f"\n  📢 Announcements: {len(announcements)} announcements")
        if announcements:
            print(f"     Sample: {announcements[0] if isinstance(announcements[0], str) else announcements[0]}")
    
    # Count documents with each field
    total_docs = await collection.count_documents({})
    with_reports = await collection.count_documents({"annual_reports": {"$exists": True, "$ne": []}})
    with_concalls = await collection.count_documents({"concalls": {"$exists": True, "$ne": []}})
    with_announcements = await collection.count_documents({
        "$or": [
            {"announcements": {"$exists": True, "$ne": []}},
            {"recent_announcements": {"$exists": True, "$ne": []}}
        ]
    })
    
    print(f"\n  📊 Coverage:")
    print(f"     Documents with annual_reports: {with_reports}/{total_docs} ({with_reports/total_docs*100:.1f}%)")
    print(f"     Documents with concalls: {with_concalls}/{total_docs} ({with_concalls/total_docs*100:.1f}%)")
    print(f"     Documents with announcements: {with_announcements}/{total_docs} ({with_announcements/total_docs*100:.1f}%)")


async def analyze_stock_financials(collection, sample: Dict):
    """Analyze stock_financials collection in detail."""
    print(f"\n🔎 DETAILED ANALYSIS: stock_financials")
    
    # Check for key financial data
    financial_fields = [
        "quarter_results",
        "yoy_results",
        "profit_loss_stats",
        "balancesheet",
        "cashflow",
        "ratios",
        "shareholding_pattern_quarterly",
        "shareholding_pattern_yearly"
    ]
    
    print(f"\n  📊 Available Financial Data:")
    for field in financial_fields:
        if field in sample:
            value = sample[field]
            if isinstance(value, list):
                print(f"     ✅ {field}: {len(value)} records")
            elif isinstance(value, dict):
                print(f"     ✅ {field}: {len(value)} keys")
            else:
                print(f"     ✅ {field}: {type(value).__name__}")
        else:
            print(f"     ❌ {field}: Not found")


async def analyze_stock_generals(collection, sample: Dict):
    """Analyze stock_generals collection in detail."""
    print(f"\n🔎 DETAILED ANALYSIS: stock_generals")
    
    # Check for key general info fields
    general_fields = [
        "isin",
        "display_name",
        "description",
        "industry",
        "sector",
        "market_cap",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield",
        "week_52_high",
        "week_52_low"
    ]
    
    print(f"\n  📊 Available General Info:")
    for field in general_fields:
        if field in sample:
            value = sample[field]
            print(f"     ✅ {field}: {str(value)[:50]}")
        else:
            print(f"     ❌ {field}: Not found")


async def analyze_stock_corporate_actions(collection, sample: Dict):
    """Analyze stock_corporate_actions collection in detail."""
    print(f"\n🔎 DETAILED ANALYSIS: stock_corporate_actions")
    
    # Check for action types
    action_fields = [
        "dividends",
        "splits",
        "bonus",
        "rights",
        "buyback"
    ]
    
    print(f"\n  📊 Available Corporate Actions:")
    for field in action_fields:
        if field in sample:
            value = sample[field]
            if isinstance(value, list):
                print(f"     ✅ {field}: {len(value)} actions")
                if value:
                    print(f"        Sample: {value[0]}")
            else:
                print(f"     ✅ {field}: {type(value).__name__}")
        else:
            print(f"     ❌ {field}: Not found")


if __name__ == "__main__":
    asyncio.run(analyze_database())
