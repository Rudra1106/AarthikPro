"""
Zerodha Portfolio Data Service.

Fetches and formats user portfolio data (holdings, positions, margins) for AI consumption.
"""

import logging
from typing import Dict, Any, Optional, List
from kiteconnect import KiteConnect

from src.config import settings
from src.auth.zerodha_oauth import get_user_zerodha_connection

logger = logging.getLogger(__name__)


async def get_user_holdings(session_id: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch user's long-term equity holdings from Zerodha.
    
    Args:
        session_id: User's session ID
        
    Returns:
        List of holdings or None if not connected/error
        
    Example:
        >>> holdings = await get_user_holdings("session-123")
        >>> print(holdings[0])
        {
            'tradingsymbol': 'INFY',
            'quantity': 100,
            'average_price': 1450.50,
            'last_price': 1520.00,
            'pnl': 6950.00,
            'day_change': 15.50,
            'day_change_percentage': 1.03
        }
    """
    try:
        # Get user's Zerodha connection
        connection = await get_user_zerodha_connection(session_id)
        
        if not connection:
            logger.warning(f"No Zerodha connection for session {session_id[:8]}...")
            return None
        
        # Initialize Kite with user's access token
        kite = KiteConnect(api_key=settings.zerodha_api_key)
        kite.set_access_token(connection["access_token"])
        
        # Fetch holdings
        holdings = kite.holdings()
        
        logger.info(f"Fetched {len(holdings)} holdings for session {session_id[:8]}...")
        
        return holdings
        
    except Exception as e:
        logger.error(f"Error fetching holdings: {e}")
        return None


async def get_user_positions(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user's positions (F&O and intraday).
    
    Args:
        session_id: User's session ID
        
    Returns:
        Dict with 'net' and 'day' positions, or None
    """
    try:
        connection = await get_user_zerodha_connection(session_id)
        
        if not connection:
            return None
        
        kite = KiteConnect(api_key=settings.zerodha_api_key)
        kite.set_access_token(connection["access_token"])
        
        # Fetch positions
        positions = kite.positions()
        
        logger.info(f"Fetched positions for session {session_id[:8]}...")
        
        return positions
        
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        return None


async def get_user_margins(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch user's available funds and margins.
    
    Args:
        session_id: User's session ID
        
    Returns:
        Margins data or None
    """
    try:
        connection = await get_user_zerodha_connection(session_id)
        
        if not connection:
            return None
        
        kite = KiteConnect(api_key=settings.zerodha_api_key)
        kite.set_access_token(connection["access_token"])
        
        # Fetch margins for equity segment
        margins = kite.margins("equity")
        
        logger.info(f"Fetched margins for session {session_id[:8]}...")
        
        return margins
        
    except Exception as e:
        logger.error(f"Error fetching margins: {e}")
        return None


async def get_complete_portfolio(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch complete portfolio data (holdings + positions + margins).
    
    Args:
        session_id: User's session ID
        
    Returns:
        Complete portfolio data or None
    """
    try:
        holdings = await get_user_holdings(session_id)
        positions = await get_user_positions(session_id)
        margins = await get_user_margins(session_id)
        
        if holdings is None:
            return None
        
        return {
            "holdings": holdings or [],
            "positions": positions or {"net": [], "day": []},
            "margins": margins or {}
        }
        
    except Exception as e:
        logger.error(f"Error fetching complete portfolio: {e}")
        return None


def format_portfolio_for_ai(portfolio: Dict[str, Any]) -> str:
    """
    Format portfolio data for AI consumption.
    
    Args:
        portfolio: Portfolio data from get_complete_portfolio()
        
    Returns:
        Formatted string for LLM context
    """
    lines = ["USER'S PORTFOLIO:\n"]
    
    # Format holdings
    holdings = portfolio.get("holdings", [])
    if holdings:
        lines.append("HOLDINGS (Long-term equity):")
        total_investment = 0
        total_current = 0
        
        for h in holdings:
            symbol = h.get("tradingsymbol", "")
            qty = h.get("quantity", 0)
            avg_price = h.get("average_price", 0)
            ltp = h.get("last_price", 0)
            pnl = h.get("pnl", 0)
            
            investment = qty * avg_price
            current_value = qty * ltp
            total_investment += investment
            total_current += current_value
            
            pnl_pct = (pnl / investment * 100) if investment > 0 else 0
            
            lines.append(
                f"  - {symbol}: {qty} shares @ ₹{avg_price:.2f} "
                f"(Current: ₹{ltp:.2f}, P&L: ₹{pnl:.2f} / {pnl_pct:+.2f}%)"
            )
        
        total_pnl = total_current - total_investment
        total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0
        
        lines.append(f"\n  Total Investment: ₹{total_investment:,.2f}")
        lines.append(f"  Current Value: ₹{total_current:,.2f}")
        lines.append(f"  Total P&L: ₹{total_pnl:,.2f} ({total_pnl_pct:+.2f}%)\n")
    else:
        lines.append("HOLDINGS: None\n")
    
    # Format positions
    positions = portfolio.get("positions", {})
    net_positions = positions.get("net", [])
    
    if net_positions:
        lines.append("POSITIONS (F&O / Intraday):")
        for p in net_positions:
            symbol = p.get("tradingsymbol", "")
            qty = p.get("quantity", 0)
            avg_price = p.get("average_price", 0)
            ltp = p.get("last_price", 0)
            pnl = p.get("pnl", 0)
            
            lines.append(
                f"  - {symbol}: {qty} qty @ ₹{avg_price:.2f} "
                f"(Current: ₹{ltp:.2f}, P&L: ₹{pnl:.2f})"
            )
        lines.append("")
    
    # Format margins
    margins = portfolio.get("margins", {})
    if margins:
        available = margins.get("available", {}).get("live_balance", 0)
        used = margins.get("utilised", {}).get("debits", 0)
        
        lines.append(f"AVAILABLE FUNDS: ₹{available:,.2f}")
        lines.append(f"MARGIN USED: ₹{used:,.2f}\n")
    
    return "\n".join(lines)


def calculate_portfolio_metrics(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate portfolio metrics for analysis.
    
    Args:
        portfolio: Portfolio data
        
    Returns:
        Dict with calculated metrics
    """
    holdings = portfolio.get("holdings", [])
    
    if not holdings:
        return {
            "total_stocks": 0,
            "total_investment": 0,
            "current_value": 0,
            "total_pnl": 0,
            "total_pnl_pct": 0,
            "top_gainer": None,
            "top_loser": None
        }
    
    total_investment = sum(h.get("quantity", 0) * h.get("average_price", 0) for h in holdings)
    total_current = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in holdings)
    total_pnl = total_current - total_investment
    total_pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0
    
    # Find top gainer and loser
    holdings_with_pnl_pct = []
    for h in holdings:
        investment = h.get("quantity", 0) * h.get("average_price", 0)
        pnl = h.get("pnl", 0)
        pnl_pct = (pnl / investment * 100) if investment > 0 else 0
        holdings_with_pnl_pct.append({
            "symbol": h.get("tradingsymbol"),
            "pnl": pnl,
            "pnl_pct": pnl_pct
        })
    
    holdings_with_pnl_pct.sort(key=lambda x: x["pnl_pct"], reverse=True)
    
    return {
        "total_stocks": len(holdings),
        "total_investment": total_investment,
        "current_value": total_current,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "top_gainer": holdings_with_pnl_pct[0] if holdings_with_pnl_pct else None,
        "top_loser": holdings_with_pnl_pct[-1] if holdings_with_pnl_pct else None
    }
