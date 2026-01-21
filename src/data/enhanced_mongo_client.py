"""
Enhanced MongoDB Client for Indian API Data.

Uses the actual collection names from the production database:
- stock_generals: Company info, prices, peers
- stock_financials: Financial statements, ratios, shareholding
- stock_documents: Annual reports, concalls, announcements
- stock_corporate_actions: Dividends, splits, bonus, rights
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from src.config import settings


class EnhancedMongoClient:
    """
    Enhanced MongoDB client using actual Indian API collection names.
    
    Collections (5,665 stocks each):
    - stock_generals: Company info, current prices, peers
    - stock_financials: Quarterly/yearly results, ratios, shareholding
    - stock_documents: Annual reports (67%), concalls (36%), announcements (70%)
    - stock_corporate_actions: Dividends, splits, bonus, rights
    """
    
    def __init__(self):
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)
        self.db: AsyncIOMotorDatabase = self.client[settings.mongodb_database]
        
        # Actual collection references (from Indian API)
        self.stock_generals = self.db.stock_generals
        self.stock_financials = self.db.stock_financials
        self.stock_documents = self.db.stock_documents
        self.stock_corporate_actions = self.db.stock_corporate_actions
    
    # ==================== SYMBOL RESOLUTION ====================
    
    async def _resolve_isin(self, symbol: str) -> Optional[str]:
        """
        Resolve stock symbol to ISIN.
        
        Args:
            symbol: Stock symbol (e.g., "TCS", "RELIANCE")
        
        Returns:
            ISIN code or None
        """
        # Try exact match on underlying_symbol
        doc = await self.stock_generals.find_one(
            {"underlying_symbol": symbol.upper()},
            {"isin": 1}
        )
        
        if doc:
            return doc.get("isin")
        
        # Try fuzzy match on display_name
        doc = await self.stock_generals.find_one(
            {"display_name": {"$regex": symbol, "$options": "i"}},
            {"isin": 1}
        )
        
        return doc.get("isin") if doc else None
    
    # ==================== COMPANY INFO (stock_generals) ====================
    
    async def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive company information.
        
        Returns:
            Company info including:
            - Basic: display_name, description, industry, sector
            - Prices: current_price, year_high, year_low, market_cap
            - Peers: List of peer companies
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        return await self.stock_generals.find_one({"isin": isin})
    
    async def get_peers(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get peer companies.
        
        Returns:
            List of peers with ticker_id, display_name, image_url
        """
        company = await self.get_company_info(symbol)
        if not company:
            return []
        
        return company.get("peers", [])
    
    async def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current market data.
        
        Returns:
            Dict with current_price, today_high, today_low, year_high, year_low, market_cap
        """
        company = await self.get_company_info(symbol)
        if not company:
            return None
        
        return {
            "current_price": company.get("current_price"),
            "today_high": company.get("today_high"),
            "today_low": company.get("today_low"),
            "today_net_change": company.get("today_net_change"),
            "today_percent_change": company.get("today_percent_change"),
            "year_high": company.get("year_high"),
            "year_low": company.get("year_low"),
            "market_cap": company.get("market_cap"),
            "capped_type": company.get("capped_type"),
        }
    
    # ==================== FINANCIALS (stock_financials) ====================
    
    async def get_quarterly_results(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get quarterly financial results.
        
        Returns:
            Dict with sales, expenses, operating_profit, opm %, net_profit, eps
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_financials.find_one(
            {"isin": isin},
            {"quarter_results": 1}
        )
        
        return doc.get("quarter_results") if doc else None
    
    async def get_yearly_results(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get year-over-year financial results.
        
        Returns:
            Dict with sales, expenses, operating_profit, net_profit, eps
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_financials.find_one(
            {"isin": isin},
            {"yoy_results": 1}
        )
        
        return doc.get("yoy_results") if doc else None
    
    async def get_profit_loss_stats(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get long-term profit/loss statistics.
        
        Returns:
            Dict with compounded_sales_growth, compounded_profit_growth, stock_price_cagr, return_on_equity
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_financials.find_one(
            {"isin": isin},
            {"profit_loss_stats": 1}
        )
        
        return doc.get("profit_loss_stats") if doc else None
    
    async def get_balance_sheet(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get balance sheet data.
        
        Returns:
            Dict with equity_capital, reserves, borrowings, total_assets, etc.
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_financials.find_one(
            {"isin": isin},
            {"balancesheet": 1}
        )
        
        return doc.get("balancesheet") if doc else None
    
    async def get_cashflow(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cashflow statement.
        
        Returns:
            Dict with cash_from_operating_activity, cash_from_investing_activity, etc.
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_financials.find_one(
            {"isin": isin},
            {"cashflow": 1}
        )
        
        return doc.get("cashflow") if doc else None
    
    async def get_ratios(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get financial ratios.
        
        Returns:
            Dict with debtor_days, inventory_days, cash_conversion_cycle, roce %
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_financials.find_one(
            {"isin": isin},
            {"ratios": 1}
        )
        
        return doc.get("ratios") if doc else None
    
    async def get_shareholding_pattern(self, symbol: str, period: str = "quarterly") -> Optional[Dict[str, Any]]:
        """
        Get shareholding pattern.
        
        Args:
            symbol: Stock symbol
            period: "quarterly" or "yearly"
        
        Returns:
            Dict with promoters, fiis, diis, government, public
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        field = "shareholding_pattern_quarterly" if period == "quarterly" else "shareholding_pattern_yearly"
        
        doc = await self.stock_financials.find_one(
            {"isin": isin},
            {field: 1}
        )
        
        return doc.get(field) if doc else None
    
    # ==================== DOCUMENTS (stock_documents) ====================
    
    async def get_annual_reports(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get annual report URLs.
        
        Returns:
            List of dicts with year, url, source
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return []
        
        doc = await self.stock_documents.find_one(
            {"isin": isin},
            {"annual_reports": 1}
        )
        
        return doc.get("annual_reports", []) if doc else []
    
    async def get_concalls(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get concall transcripts and recordings.
        
        Returns:
            List of dicts with date, transcript, ppt, rec (recording URL)
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return []
        
        doc = await self.stock_documents.find_one(
            {"isin": isin},
            {"concalls": 1}
        )
        
        return doc.get("concalls", []) if doc else []
    
    async def get_recent_announcements(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent corporate announcements.
        
        Returns:
            List of dicts with title, date, url
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return []
        
        doc = await self.stock_documents.find_one(
            {"isin": isin},
            {"recent_announcements": 1}
        )
        
        announcements = doc.get("recent_announcements", []) if doc else []
        return announcements[:limit]
    
    async def get_credit_ratings(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Get credit rating history.
        
        Returns:
            List of dicts with title, date, url
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return []
        
        doc = await self.stock_documents.find_one(
            {"isin": isin},
            {"credit_ratings": 1}
        )
        
        return doc.get("credit_ratings", []) if doc else []
    
    # ==================== CORPORATE ACTIONS (stock_corporate_actions) ====================
    
    async def get_dividends(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get dividend history.
        
        Returns:
            Dict with title and data array
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_corporate_actions.find_one(
            {"isin": isin},
            {"dividends": 1}
        )
        
        return doc.get("dividends") if doc else None
    
    async def get_splits(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock split history.
        
        Returns:
            Dict with title and data array
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_corporate_actions.find_one(
            {"isin": isin},
            {"splits": 1}
        )
        
        return doc.get("splits") if doc else None
    
    async def get_bonus(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get bonus issue history.
        
        Returns:
            Dict with title and msg/data
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_corporate_actions.find_one(
            {"isin": isin},
            {"bonus": 1}
        )
        
        return doc.get("bonus") if doc else None
    
    async def get_rights(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get rights issue history.
        
        Returns:
            Dict with title and data array
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_corporate_actions.find_one(
            {"isin": isin},
            {"rights": 1}
        )
        
        return doc.get("rights") if doc else None
    
    async def get_board_meetings(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get board meeting schedule.
        
        Returns:
            Dict with title and data array
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return None
        
        doc = await self.stock_corporate_actions.find_one(
            {"isin": isin},
            {"board_meetings": 1}
        )
        
        return doc.get("board_meetings") if doc else None
    
    # ==================== COMPREHENSIVE DATA FETCH ====================
    
    async def get_complete_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get ALL available data for a stock in one call.
        
        Returns:
            Dict with all data from all 4 collections
        """
        isin = await self._resolve_isin(symbol)
        if not isin:
            return {}
        
        # Fetch from all collections in parallel
        general_task = self.stock_generals.find_one({"isin": isin})
        financial_task = self.stock_financials.find_one({"isin": isin})
        document_task = self.stock_documents.find_one({"isin": isin})
        action_task = self.stock_corporate_actions.find_one({"isin": isin})
        
        general, financial, document, action = await asyncio.gather(
            general_task, financial_task, document_task, action_task,
            return_exceptions=True
        )
        
        return {
            "general": general if not isinstance(general, Exception) else {},
            "financial": financial if not isinstance(financial, Exception) else {},
            "documents": document if not isinstance(document, Exception) else {},
            "corporate_actions": action if not isinstance(action, Exception) else {},
        }
    
    async def close(self):
        """Close MongoDB connection."""
        self.client.close()


# Singleton instance
_enhanced_mongo_client: Optional[EnhancedMongoClient] = None


def get_enhanced_mongo_client() -> EnhancedMongoClient:
    """Get singleton enhanced MongoDB client instance."""
    global _enhanced_mongo_client
    if _enhanced_mongo_client is None:
        _enhanced_mongo_client = EnhancedMongoClient()
    return _enhanced_mongo_client
