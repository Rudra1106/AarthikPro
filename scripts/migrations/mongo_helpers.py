"""
Helper functions for MongoDB document processing state management.

Add these to src/data/mongo_client.py
"""

# Add to MongoClient class:

async def get_processing_state(self, symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get processing state for a stock.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Processing state dict or None
    """
    doc = await self.stock_documents.find_one(
        {"symbol": symbol},
        {"processing_state": 1}
    )
    
    if doc:
        return doc.get("processing_state", {
            "tier": 0,
            "last_processed": None,
            "query_count": 0,
            "sections_extracted": [],
            "verticals_extracted": False,
            "pinecone_indexed": False,
            "processing_errors": []
        })
    
    return None


async def increment_query_count(self, symbol: str) -> int:
    """
    Increment query count for a stock.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        New query count
    """
    result = await self.stock_documents.find_one_and_update(
        {"symbol": symbol},
        {"$inc": {"processing_state.query_count": 1}},
        return_document=True
    )
    
    if result:
        return result.get("processing_state", {}).get("query_count", 0)
    
    return 0


async def update_processing_state(
    self,
    symbol: str,
    tier: Optional[int] = None,
    sections_extracted: Optional[List[str]] = None,
    verticals_extracted: Optional[bool] = None,
    pinecone_indexed: Optional[bool] = None
) -> bool:
    """
    Update processing state for a stock.
    
    Args:
        symbol: Stock symbol
        tier: Processing tier (0-3)
        sections_extracted: List of extracted section names
        verticals_extracted: Whether verticals were extracted
        pinecone_indexed: Whether indexed in Pinecone
        
    Returns:
        True if updated successfully
    """
    update_fields = {
        "processing_state.last_processed": datetime.now().isoformat()
    }
    
    if tier is not None:
        update_fields["processing_state.tier"] = tier
    if sections_extracted is not None:
        update_fields["processing_state.sections_extracted"] = sections_extracted
    if verticals_extracted is not None:
        update_fields["processing_state.verticals_extracted"] = verticals_extracted
    if pinecone_indexed is not None:
        update_fields["processing_state.pinecone_indexed"] = pinecone_indexed
    
    result = await self.stock_documents.update_one(
        {"symbol": symbol},
        {"$set": update_fields}
    )
    
    return result.modified_count > 0


async def get_verticals(
    self, symbol: str, fiscal_year: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Get vertical/segment information for a stock.
    
    Args:
        symbol: Stock symbol
        fiscal_year: Fiscal year (e.g., "FY2024"). If None, gets latest.
        
    Returns:
        Verticals document or None
    """
    query = {"symbol": symbol}
    
    if fiscal_year:
        query["fiscal_year"] = fiscal_year
    
    # Sort by fiscal_year descending to get latest
    doc = await self.db.stock_verticals.find_one(
        query,
        sort=[("fiscal_year", -1)]
    )
    
    return doc


async def get_stocks_by_tier(self, tier: int, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get stocks at a specific processing tier.
    
    Args:
        tier: Processing tier (0-3)
        limit: Maximum number of results
        
    Returns:
        List of stock documents
    """
    cursor = self.stock_documents.find(
        {"processing_state.tier": tier}
    ).limit(limit)
    
    return await cursor.to_list(length=limit)


async def get_top_queried_stocks(self, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get most queried stocks (candidates for tier upgrade).
    
    Args:
        limit: Maximum number of results
        
    Returns:
        List of stock documents sorted by query count
    """
    cursor = self.stock_documents.find().sort(
        "processing_state.query_count", -1
    ).limit(limit)
    
    return await cursor.to_list(length=limit)
