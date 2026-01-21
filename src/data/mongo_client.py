"""
MongoDB client for structured financial data.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.config import settings


class MongoClient:
    """
    MongoDB client for querying structured financial data.
    
    Collections:
    - financial_statements: Quarterly and annual financial data (756+ docs)
    - tables: Detailed financial tables from PDFs (34,259 docs)
    - corporate_actions: Dividends, splits, bonuses, rights (496 docs)
    - companies: Company master data (48 docs)
    - historic_stats: Legacy quarterly financials (kept for backward compatibility)
    - stock_details: Legacy company metadata (kept for backward compatibility)
    """
    
    def __init__(self):
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)
        self.db: AsyncIOMotorDatabase = self.client[settings.mongodb_database]
        
        # New collection references (from Indian API + PDF processing)
        self.financial_statements = self.db.financial_statements
        self.tables = self.db.tables
        self.companies = self.db.companies
        
        # Legacy collection references (backward compatibility)
        self.corporate_actions = self.db.corporate_actions
        self.historic_stats = self.db.historic_stats
        self.stock_details = self.db.stock_details
    
    # ==================== NEW METHODS (Indian API Data) ====================
    
    async def get_quarterly_financials(
        self,
        ticker: str,
        quarters: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Get quarterly financial statements from Indian API data.
        
        Args:
            ticker: Stock ticker (e.g., "TCS", "RELIANCE")
            quarters: Number of quarters to fetch
            
        Returns:
            List of quarterly financial statements, sorted by date (newest first)
        """
        query = {
            "ticker": ticker.upper(),
            "period_type": "quarterly"
        }
        cursor = self.financial_statements.find(query).sort("fiscal_period", -1).limit(quarters)
        return await cursor.to_list(length=quarters)
    
    async def get_latest_quarterly_financials(
        self,
        ticker: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the most recent quarterly financial statement.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Latest quarterly financial data or None
        """
        query = {
            "ticker": ticker.upper(),
            "period_type": "quarterly"
        }
        return await self.financial_statements.find_one(
            query,
            sort=[("fiscal_period", -1)]
        )
    
    async def get_financial_trend(
        self,
        ticker: str,
        metric: str,
        quarters: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Get trend data for a specific financial metric over time.
        
        Args:
            ticker: Stock ticker
            metric: Metric name (e.g., "revenue", "net_profit", "operating_margin_pct", "eps")
            quarters: Number of quarters to analyze
            
        Returns:
            List of dicts with period, value, and YoY growth
        """
        financials = await self.get_quarterly_financials(ticker, quarters)
        
        trend_data = []
        for i, statement in enumerate(financials):
            data = statement.get("data", {})
            value = data.get(metric)
            
            if value is not None:
                # Calculate YoY growth if we have data from a year ago
                yoy_growth = None
                if i + 4 < len(financials):  # 4 quarters = 1 year
                    prev_value = financials[i + 4].get("data", {}).get(metric)
                    if prev_value and prev_value > 0:
                        yoy_growth = ((value - prev_value) / prev_value) * 100
                
                trend_data.append({
                    "period": statement.get("quarter_label"),
                    "fiscal_period": statement.get("fiscal_period"),
                    "value": value,
                    "yoy_growth": yoy_growth
                })
        
        return trend_data
    
    async def get_table_by_name(
        self,
        ticker: str,
        table_name: str,
        fiscal_year: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a specific financial table by name.
        
        Args:
            ticker: Stock ticker
            table_name: Table name (e.g., "Segment", "P&L", "Balance Sheet")
            fiscal_year: Fiscal year (e.g., "FY2024")
            
        Returns:
            Table data with headers and rows
        """
        query = {
            "ticker": ticker.upper(),
            "fiscal_year": fiscal_year,
            "table_info.table_name": {"$regex": table_name, "$options": "i"}
        }
        return await self.tables.find_one(query)
    
    async def get_tables_by_fiscal_year(
        self,
        ticker: str,
        fiscal_year: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get all tables for a specific fiscal year.
        
        Args:
            ticker: Stock ticker
            fiscal_year: Fiscal year
            limit: Maximum number of tables to return
            
        Returns:
            List of tables
        """
        query = {
            "ticker": ticker.upper(),
            "fiscal_year": fiscal_year
        }
        cursor = self.tables.find(query).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_company_info(
        self,
        ticker: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get company master data.
        
        Args:
            ticker: Stock ticker
            
        Returns:
            Company info including name, sector, industry
        """
        return await self.companies.find_one({"ticker": ticker.upper()})
    
    async def get_upcoming_dividends(
        self,
        ticker: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get upcoming dividend announcements.
        
        Args:
            ticker: Stock ticker
            limit: Maximum results
            
        Returns:
            List of upcoming dividends
        """
        query = {
            "ticker": ticker.upper(),
            "action_type": "dividend",
            "ex_date": {"$gte": datetime.now().strftime("%Y-%m-%d")}
        }
        cursor = self.corporate_actions.find(query).sort("ex_date", 1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_dividend_history(
        self,
        ticker: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get historical dividend announcements.
        
        Args:
            ticker: Stock ticker
            limit: Maximum results
            
        Returns:
            List of historical dividends
        """
        query = {
            "ticker": ticker.upper(),
            "action_type": "dividend"
        }
        cursor = self.corporate_actions.find(query).sort("ex_date", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_all_corporate_actions(
        self,
        ticker: str,
        action_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get corporate actions (dividends, splits, bonus, rights).
        
        Args:
            ticker: Stock ticker
            action_type: Filter by type (dividend, split, bonus, rights)
            limit: Maximum results
            
        Returns:
            List of corporate actions
        """
        query = {"ticker": ticker.upper()}
        if action_type:
            query["action_type"] = action_type
        
        cursor = self.corporate_actions.find(query).sort("ex_date", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    # ==================== LEGACY METHODS (Backward Compatibility) ====================
    
    async def get_corporate_actions(
        self,
        symbol: str,
        action_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        LEGACY: Get corporate actions using 'symbol' field.
        Kept for backward compatibility. Use get_all_corporate_actions() instead.
        """
        # Try new schema first (ticker field)
        result = await self.get_all_corporate_actions(symbol, action_type, limit)
        if result:
            return result
        
        # Fallback to old schema (symbol field)
        query = {"symbol": symbol}
        if action_type:
            query["action_type"] = action_type
        
        cursor = self.corporate_actions.find(query).sort("date", -1).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_latest_financials(
        self,
        symbol: str,
        period: str = "quarterly"
    ) -> Optional[Dict[str, Any]]:
        """
        LEGACY: Get latest financial data using old schema.
        Kept for backward compatibility. Use get_latest_quarterly_financials() instead.
        """
        # Try new schema first
        if period == "quarterly":
            result = await self.get_latest_quarterly_financials(symbol)
            if result:
                return result
        
        # Fallback to old schema
        query = {"symbol": symbol, "period": period}
        result = await self.historic_stats.find_one(
            query,
            sort=[("date", -1)]
        )
        return result
    
    async def get_financial_ratios(
        self,
        symbol: str,
        quarters: int = 4
    ) -> List[Dict[str, Any]]:
        """
        LEGACY: Get financial ratios over time using old schema.
        Kept for backward compatibility.
        """
        # Try new schema first
        result = await self.get_quarterly_financials(symbol, quarters)
        if result:
            return result
        
        # Fallback to old schema
        query = {"symbol": symbol, "period": "quarterly"}
        cursor = self.historic_stats.find(query).sort("date", -1).limit(quarters)
        return await cursor.to_list(length=quarters)
    
    async def get_stock_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        LEGACY: Get company metadata using old schema.
        Kept for backward compatibility. Use get_company_info() instead.
        """
        # Try new schema first
        result = await self.get_company_info(symbol)
        if result:
            return result
        
        # Fallback to old schema
        return await self.stock_details.find_one({"symbol": symbol})
    
    async def get_sector_peers(
        self,
        symbol: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get peer companies in the same sector.
        
        Args:
            symbol: Stock symbol/ticker
            limit: Number of peers to return
            
        Returns:
            List of peer companies
        """
        # Get stock's sector (try new schema first)
        stock = await self.get_company_info(symbol)
        if not stock:
            stock = await self.stock_details.find_one({"symbol": symbol})
        
        if not stock or "sector" not in stock:
            return []
        
        sector = stock["sector"]
        ticker_field = "ticker" if "ticker" in stock else "symbol"
        
        # Find peers in same sector
        query = {"sector": sector, ticker_field: {"$ne": symbol.upper()}}
        
        # Try companies collection first
        cursor = self.companies.find(query).limit(limit)
        results = await cursor.to_list(length=limit)
        
        if not results:
            # Fallback to stock_details
            cursor = self.stock_details.find(query).limit(limit)
            results = await cursor.to_list(length=limit)
        
        return results
    
    async def compare_metrics(
        self,
        symbols: List[str],
        metrics: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compare specific metrics across multiple stocks.
        
        Args:
            symbols: List of stock symbols/tickers
            metrics: List of metric names
            
        Returns:
            Dict mapping symbol to metric values
        """
        # Try new schema first
        tickers_upper = [s.upper() for s in symbols]
        query = {"ticker": {"$in": tickers_upper}}
        projection = {"ticker": 1, **{m: 1 for m in metrics}}
        
        cursor = self.companies.find(query, projection)
        results = await cursor.to_list(length=len(symbols))
        
        if results:
            return {r["ticker"]: r for r in results}
        
        # Fallback to old schema
        query = {"symbol": {"$in": symbols}}
        projection = {"symbol": 1, **{m: 1 for m in metrics}}
        
        cursor = self.stock_details.find(query, projection)
        results = await cursor.to_list(length=len(symbols))
        
        return {r["symbol"]: r for r in results}
    
    # ==================== ZERODHA OAUTH METHODS ====================
    
    async def save_zerodha_connection(
        self,
        session_id: str,
        zerodha_user_id: str,
        access_token: str,
        expires_at: datetime,
        user_name: str = "",
        email: str = ""
    ):
        """
        Save or update Zerodha connection for a user.
        
        Args:
            session_id: User's session ID
            zerodha_user_id: Zerodha user ID
            access_token: Encrypted access token
            expires_at: Token expiry datetime
            user_name: Zerodha user name
            email: User email
        """
        # Use a separate database for Zerodha connections
        zerodha_db = self.client.get_database("aarthik_zerodha")
        connections = zerodha_db.zerodha_connections
        
        connection_doc = {
            "session_id": session_id,
            "zerodha_user_id": zerodha_user_id,
            "access_token": access_token,
            "expires_at": expires_at,
            "user_name": user_name,
            "email": email,
            "updated_at": datetime.utcnow()
        }
        
        await connections.update_one(
            {"session_id": session_id},
            {
                "$set": connection_doc,
                "$setOnInsert": {"created_at": datetime.utcnow()}
            },
            upsert=True
        )
    
    async def get_zerodha_connection(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get Zerodha connection for a user.
        
        Args:
            session_id: User's session ID
            
        Returns:
            Connection document or None
        """
        zerodha_db = self.client.get_database("aarthik_zerodha")
        connections = zerodha_db.zerodha_connections
        
        return await connections.find_one({"session_id": session_id})
    
    async def delete_zerodha_connection(self, session_id: str):
        """
        Delete Zerodha connection for a user.
        
        Args:
            session_id: User's session ID
        """
        zerodha_db = self.client.get_database("aarthik_zerodha")
        connections = zerodha_db.zerodha_connections
        
        await connections.delete_one({"session_id": session_id})
    
    async def save_oauth_state(
        self,
        state: str,
        session_id: str,
        expires_at: datetime
    ):
        """
        Save temporary OAuth state for CSRF protection.
        
        Args:
            state: Random state string
            session_id: User's session ID
            expires_at: State expiry datetime
        """
        zerodha_db = self.client.get_database("aarthik_zerodha")
        oauth_states = zerodha_db.oauth_states
        
        await oauth_states.insert_one({
            "state": state,
            "session_id": session_id,
            "expires_at": expires_at,
            "created_at": datetime.utcnow()
        })
    
    async def verify_oauth_state(self, state: str) -> Optional[str]:
        """
        Verify OAuth state and return session_id.
        
        Args:
            state: State parameter from OAuth callback
            
        Returns:
            session_id if valid, None otherwise
        """
        zerodha_db = self.client.get_database("aarthik_zerodha")
        oauth_states = zerodha_db.oauth_states
        
        state_doc = await oauth_states.find_one({
            "state": state,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        
        return state_doc["session_id"] if state_doc else None
    
    async def cleanup_oauth_state(self, state: str):
        """
        Delete OAuth state after use.
        
        Args:
            state: State parameter to delete
        """
        zerodha_db = self.client.get_database("aarthik_zerodha")
        oauth_states = zerodha_db.oauth_states
        
        await oauth_states.delete_one({"state": state})
    
    async def cleanup_expired_oauth_states(self):
        """
        Cleanup expired OAuth states (run periodically).
        """
        zerodha_db = self.client.get_database("aarthik_zerodha")
        oauth_states = zerodha_db.oauth_states
        
        result = await oauth_states.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        
        return result.deleted_count
    
    async def close(self):
        """Close MongoDB connection."""
        self.client.close()


# Singleton instance
_mongo_client_instance: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    """Get singleton MongoDB client instance."""
    global _mongo_client_instance
    if _mongo_client_instance is None:
        _mongo_client_instance = MongoClient()
    return _mongo_client_instance
