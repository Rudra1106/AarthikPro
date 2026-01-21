"""
MongoDB Schema Migration: Add Processing State to stock_documents.

This script adds the processing_state field to all documents in the
stock_documents collection.
"""
import asyncio
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGODB_URI = "mongodb+srv://aarthikaibot:xjJ0Dh1wMmCNr5p6@aarthik.m9cjl1m.mongodb.net/"
DATABASE_NAME = "PORTFOLIO_MANAGER"


async def migrate_add_processing_state():
    """Add processing_state field to all stock_documents."""
    logger.info("Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    collection = db.stock_documents
    
    # Default processing state
    default_state = {
        "tier": 0,  # Link only
        "last_processed": None,
        "query_count": 0,
        "sections_extracted": [],
        "verticals_extracted": False,
        "pinecone_indexed": False,
        "processing_errors": []
    }
    
    # Count documents without processing_state
    count_without = await collection.count_documents({
        "processing_state": {"$exists": False}
    })
    
    logger.info(f"Found {count_without} documents without processing_state")
    
    if count_without == 0:
        logger.info("All documents already have processing_state. Nothing to do.")
        client.close()
        return
    
    # Update all documents
    logger.info("Adding processing_state to documents...")
    result = await collection.update_many(
        {"processing_state": {"$exists": False}},
        {"$set": {"processing_state": default_state}}
    )
    
    logger.info(f"Updated {result.modified_count} documents")
    
    # Verify
    count_with = await collection.count_documents({
        "processing_state": {"$exists": True}
    })
    
    logger.info(f"Verification: {count_with} documents now have processing_state")
    
    client.close()
    logger.info("Migration complete!")


async def create_indexes():
    """Create indexes for efficient querying."""
    logger.info("Creating indexes...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    # stock_documents indexes
    logger.info("Creating indexes on stock_documents...")
    await db.stock_documents.create_index("symbol")
    await db.stock_documents.create_index("processing_state.tier")
    await db.stock_documents.create_index("processing_state.query_count")
    await db.stock_documents.create_index([("processing_state.query_count", -1)])
    
    # stock_verticals indexes
    logger.info("Creating indexes on stock_verticals...")
    await db.stock_verticals.create_index([("symbol", 1), ("fiscal_year", -1)])
    await db.stock_verticals.create_index("isin")
    
    client.close()
    logger.info("Indexes created successfully!")


async def main():
    """Run migration."""
    try:
        await migrate_add_processing_state()
        await create_indexes()
        logger.info("✅ Migration completed successfully!")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
