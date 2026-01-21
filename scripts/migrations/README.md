# MongoDB Schema Updates

This directory contains migration scripts and helper functions for MongoDB schema updates.

## Migrations

### 001: Add Processing State

Adds `processing_state` field to all documents in `stock_documents` collection.

**Run migration:**
```bash
python scripts/migrations/001_add_processing_state.py
```

**What it does:**
1. Adds `processing_state` field to all `stock_documents`
2. Creates indexes for efficient querying
3. Creates indexes on `stock_verticals` collection

**Schema changes:**
```javascript
// stock_documents
{
  "symbol": "RELIANCE",
  "annual_reports": [...],
  
  // NEW
  "processing_state": {
    "tier": 0,                    // 0-3
    "last_processed": null,       // ISO timestamp
    "query_count": 0,             // Number of queries
    "sections_extracted": [],     // ["business_overview", "md_and_a", ...]
    "verticals_extracted": false, // Boolean
    "pinecone_indexed": false,    // Boolean
    "processing_errors": []       // [{error, timestamp}, ...]
  }
}
```

## Helper Functions

The `mongo_helpers.py` file contains helper functions to add to `src/data/mongo_client.py`:

- `get_processing_state(symbol)` - Get processing state
- `increment_query_count(symbol)` - Increment query count
- `update_processing_state(...)` - Update processing state
- `get_verticals(symbol, fiscal_year)` - Get vertical data
- `get_stocks_by_tier(tier)` - Get stocks at specific tier
- `get_top_queried_stocks()` - Get most queried stocks

**To integrate:**
1. Copy functions from `mongo_helpers.py`
2. Add to `MongoClient` class in `src/data/mongo_client.py`
3. Import `datetime` and `List` if not already imported

## Indexes Created

### stock_documents
- `symbol` (ascending)
- `processing_state.tier` (ascending)
- `processing_state.query_count` (ascending)
- `processing_state.query_count` (descending) - for top queried

### stock_verticals
- `(symbol, fiscal_year)` (compound, fiscal_year descending)
- `isin` (ascending)

## Verification

After running migration, verify:

```python
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient("mongodb+srv://...")
db = client["PORTFOLIO_MANAGER"]

# Check processing_state exists
count = await db.stock_documents.count_documents({
    "processing_state": {"$exists": True}
})
print(f"Documents with processing_state: {count}")

# Check indexes
indexes = await db.stock_documents.index_information()
print(f"Indexes: {list(indexes.keys())}")
```

## Rollback

To remove processing_state (if needed):

```python
await db.stock_documents.update_many(
    {},
    {"$unset": {"processing_state": ""}}
)
```

## Next Steps

After migration:
1. Update `src/data/mongo_client.py` with helper functions
2. Test with a few stocks
3. Integrate with LangGraph nodes
4. Start RQ worker
