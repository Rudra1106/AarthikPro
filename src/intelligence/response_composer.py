"""
Response Composer Layer - Transforms sector data into stock-level insights.

This module adapts sector performance analysis to stock comparison format,
addressing the intent mismatch where users ask for "best stocks in sector"
but receive sector-level breadth analysis instead.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def extract_sector_from_query(query: str) -> Optional[str]:
    """
    Extract sector name from user query.
    
    Args:
        query: User's query string
        
    Returns:
        Normalized sector name (e.g., "Energy", "IT", "Banking") or None
        
    Examples:
        "compare best stocks in energy sector" -> "Energy"
        "top IT stocks" -> "IT"
        "which pharma companies are good" -> "Pharma"
    """
    query_lower = query.lower()
    
    # Sector mapping (query keywords -> normalized sector name)
    sector_map = {
        "energy": "Energy",
        "oil": "Energy",
        "gas": "Energy",
        "petroleum": "Energy",
        "it": "IT",
        "tech": "IT",
        "technology": "IT",
        "software": "IT",
        "pharma": "Pharma",
        "pharmaceutical": "Pharma",
        "healthcare": "Pharma",
        "auto": "Auto",
        "automobile": "Auto",
        "automotive": "Auto",
        "bank": "Banking",
        "banking": "Banking",
        "financial": "Financial Services",
        "finance": "Financial Services",
        "fmcg": "FMCG",
        "consumer": "FMCG",
        "metal": "Metals",
        "metals": "Metals",
        "steel": "Metals",
        "realty": "Realty",
        "real estate": "Realty",
        "infrastructure": "Infrastructure",
        "infra": "Infrastructure",
    }
    
    # Search for sector keywords
    for keyword, sector_name in sector_map.items():
        if keyword in query_lower:
            logger.info(f"Extracted sector '{sector_name}' from query")
            return sector_name
    
    logger.warning(f"Could not extract sector from query: {query}")
    return None


def extract_stock_rankings(
    sector_data: Dict[str, Any],
    sector_name: str
) -> List[Dict[str, Any]]:
    """
    Extract and rank individual stocks from sector performance data.
    
    Args:
        sector_data: Sector performance data with stock-level details
        sector_name: Name of the sector
        
    Returns:
        List of stocks sorted by performance, with metadata
        
    Example output:
        [
            {
                "rank": 1,
                "symbol": "ONGC",
                "name": "Oil & Natural Gas Corp",
                "change_percent": 2.1,
                "last_price": 245.50,
                "trend": "📈",
                "reason": "Crude price tailwinds + upstream leverage"
            },
            ...
        ]
    """
    stocks = []
    
    # Extract stocks from sector data
    # Sector data structure varies, handle multiple formats
    if "sectors" in sector_data:
        # Format from get_sector_performance()
        for sector in sector_data.get("sectors", []):
            if sector.get("name", "").lower() == sector_name.lower():
                top_movers = sector.get("top_movers", [])
                for i, stock in enumerate(top_movers, 1):
                    stocks.append({
                        "rank": i,
                        "symbol": stock.get("symbol", ""),
                        "name": stock.get("name", stock.get("symbol", "")),
                        "change_percent": stock.get("change_percent", 0),
                        "last_price": stock.get("last_price", 0),
                        "trend": "📈" if stock.get("change_percent", 0) > 0 else "📉",
                        "reason": _infer_stock_reason(stock, sector)
                    })
                break
    
    elif "stocks" in sector_data:
        # Direct stock list format
        for i, stock in enumerate(sector_data.get("stocks", []), 1):
            stocks.append({
                "rank": i,
                "symbol": stock.get("symbol", ""),
                "name": stock.get("name", stock.get("symbol", "")),
                "change_percent": stock.get("change_percent", 0),
                "last_price": stock.get("last_price", 0),
                "trend": "📈" if stock.get("change_percent", 0) > 0 else "📉",
                "reason": stock.get("reason", _infer_stock_reason(stock, sector_data))
            })
    
    # Sort by performance (descending)
    stocks.sort(key=lambda x: x["change_percent"], reverse=True)
    
    # Re-rank after sorting
    for i, stock in enumerate(stocks, 1):
        stock["rank"] = i
    
    logger.info(f"Extracted {len(stocks)} stocks from {sector_name} sector")
    return stocks


def _infer_stock_reason(stock: Dict[str, Any], sector_context: Dict[str, Any]) -> str:
    """
    Infer reason for stock performance based on context.
    
    This is a heuristic-based approach. In production, this could be enhanced
    with LLM-based reasoning or news sentiment analysis.
    """
    change_pct = stock.get("change_percent", 0)
    symbol = stock.get("symbol", "")
    
    # Sector-specific reasons (simplified heuristics)
    if change_pct > 1.5:
        return "Strong momentum + sector tailwinds"
    elif change_pct > 0.5:
        return "Positive sector sentiment"
    elif change_pct > -0.5:
        return "Stable performance"
    elif change_pct > -1.5:
        return "Sector headwinds"
    else:
        return "Weak fundamentals or profit booking"


def identify_leaders_laggards(
    stocks: List[Dict[str, Any]],
    top_n: int = 3,
    bottom_n: int = 3
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Separate top performers from laggards.
    
    Args:
        stocks: List of ranked stocks
        top_n: Number of top performers to return
        bottom_n: Number of laggards to return
        
    Returns:
        Tuple of (leaders, laggards)
    """
    leaders = stocks[:top_n] if len(stocks) >= top_n else stocks
    laggards = stocks[-bottom_n:] if len(stocks) >= bottom_n else []
    
    return leaders, laggards


def generate_stock_comparison_table(
    stocks: List[Dict[str, Any]],
    include_price: bool = True
) -> str:
    """
    Generate markdown table for stock comparison.
    
    Args:
        stocks: List of stocks with ranking data
        include_price: Whether to include price column
        
    Returns:
        Markdown-formatted table string
        
    Example output:
        | Rank | Stock | WTD % | Trend | Reason |
        |------|-------|-------|-------|--------|
        | 1️⃣ | ONGC | +2.1% | 📈 | Crude up + upstream leverage |
    """
    if not stocks:
        return "_No stock data available_"
    
    # Table header
    if include_price:
        table = "| Rank | Stock | Price | WTD % | Trend | Reason |\n"
        table += "|------|-------|-------|-------|-------|--------|\n"
    else:
        table = "| Rank | Stock | WTD % | Trend | Reason |\n"
        table += "|------|-------|-------|-------|--------|\n"
    
    # Rank emojis
    rank_emojis = {1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣"}
    
    # Table rows
    for stock in stocks:
        rank = stock.get("rank", 0)
        rank_display = rank_emojis.get(rank, str(rank))
        symbol = stock.get("symbol", "N/A")
        change_pct = stock.get("change_percent", 0)
        trend = stock.get("trend", "⚖️")
        reason = stock.get("reason", "N/A")
        
        # Truncate reason if too long
        if len(reason) > 50:
            reason = reason[:47] + "..."
        
        if include_price:
            price = stock.get("last_price", 0)
            table += f"| {rank_display} | {symbol} | ₹{price:,.2f} | {change_pct:+.1f}% | {trend} | {reason} |\n"
        else:
            table += f"| {rank_display} | {symbol} | {change_pct:+.1f}% | {trend} | {reason} |\n"
    
    return table


def generate_actionable_takeaway(
    sector_name: str,
    leaders: List[Dict[str, Any]],
    laggards: List[Dict[str, Any]],
    breadth: float,
    nifty_change: float = 0
) -> str:
    """
    Generate actionable investment takeaway.
    
    Args:
        sector_name: Name of the sector
        leaders: Top performing stocks
        laggards: Underperforming stocks
        breadth: Sector breadth (0-1, fraction of stocks advancing)
        nifty_change: Nifty 50 change % for comparison
        
    Returns:
        Actionable recommendation string
        
    Example:
        "Energy is suitable for stock-specific trades, not sector-wide allocation.
         Prefer upstream & refiners (ONGC, BPCL); avoid utilities for now."
    """
    # Determine sector strength
    sector_outperforming = len(leaders) > 0 and leaders[0].get("change_percent", 0) > nifty_change
    narrow_breadth = breadth < 0.4  # Less than 40% stocks advancing
    
    # Build recommendation
    if sector_outperforming and narrow_breadth:
        # Selective opportunities
        leader_symbols = ", ".join([s.get("symbol", "") for s in leaders[:3]])
        laggard_symbols = ", ".join([s.get("symbol", "") for s in laggards[:2]]) if laggards else "utilities"
        
        takeaway = f"{sector_name} is suitable for **stock-specific trades**, not sector-wide allocation. "
        takeaway += f"Prefer {leader_symbols}; avoid {laggard_symbols} for now."
    
    elif sector_outperforming and not narrow_breadth:
        # Broad sector rally
        takeaway = f"{sector_name} shows **broad-based strength** with {breadth*100:.0f}% stocks advancing. "
        takeaway += f"Sector-wide allocation recommended. Top picks: {', '.join([s.get('symbol', '') for s in leaders[:3]])}."
    
    elif not sector_outperforming and narrow_breadth:
        # Sector weakness
        takeaway = f"{sector_name} is underperforming with limited participation. "
        takeaway += f"**Avoid sector allocation** for now. Only consider {leaders[0].get('symbol', '')} if momentum continues."
    
    else:
        # Mixed signals
        takeaway = f"{sector_name} shows mixed signals. "
        takeaway += f"Wait for clearer trend or focus on stock-specific opportunities in {', '.join([s.get('symbol', '') for s in leaders[:2]])}."
    
    return takeaway


def generate_breadth_insight(
    stocks: List[Dict[str, Any]],
    breadth: float,
    sector_name: str
) -> str:
    """
    Generate breadth interpretation with stock names.
    
    Args:
        stocks: List of all stocks in sector
        breadth: Sector breadth (0-1)
        sector_name: Name of the sector
        
    Returns:
        Breadth insight string with specific stock names
        
    Example:
        "Only 3 of 10 energy stocks are advancing.
         This confirms leadership is concentrated in upstream & refining stocks (ONGC, BPCL, RELIANCE),
         while gas utilities and power names are lagging."
    """
    total_stocks = len(stocks)
    advancing_stocks = [s for s in stocks if s.get("change_percent", 0) > 0]
    declining_stocks = [s for s in stocks if s.get("change_percent", 0) < 0]
    
    num_advancing = len(advancing_stocks)
    num_declining = len(declining_stocks)
    
    # Build insight
    insight = f"Only {num_advancing} of {total_stocks} {sector_name} stocks are advancing. "
    
    # Add stock names for context
    if num_advancing > 0 and num_advancing <= 5:
        advancing_names = ", ".join([s.get("symbol", "") for s in advancing_stocks[:5]])
        insight += f"This confirms leadership is concentrated in {advancing_names}, "
    elif num_advancing > 5:
        advancing_names = ", ".join([s.get("symbol", "") for s in advancing_stocks[:3]])
        insight += f"Leadership is spread across {advancing_names} and others, "
    
    # Mention laggards
    if num_declining > 0 and num_declining <= 3:
        declining_names = ", ".join([s.get("symbol", "") for s in declining_stocks[:3]])
        insight += f"while {declining_names} are lagging."
    elif num_declining > 3:
        insight += f"while {num_declining} stocks are underperforming."
    
    return insight


def compose_stock_comparison_response(
    query: str,
    sector_data: Dict[str, Any],
    sector_name: str
) -> Dict[str, Any]:
    """
    Main composer function - transforms sector data into stock comparison format.
    
    Args:
        query: User's original query
        sector_data: Raw sector performance data
        sector_name: Extracted sector name
        
    Returns:
        Dict with composed response components:
        {
            "tldr": "Decision-oriented summary",
            "stock_table": "Markdown table",
            "leaders": [...],
            "laggards": [...],
            "breadth_insight": "...",
            "actionable_takeaway": "..."
        }
    """
    # Extract stock rankings
    stocks = extract_stock_rankings(sector_data, sector_name)
    
    if not stocks:
        return {
            "error": f"No stock data available for {sector_name} sector",
            "tldr": f"Unable to fetch stock rankings for {sector_name}.",
            "stock_table": "_No data available_",
            "leaders": [],
            "laggards": [],
            "breadth_insight": "",
            "actionable_takeaway": ""
        }
    
    # Identify leaders and laggards
    leaders, laggards = identify_leaders_laggards(stocks, top_n=3, bottom_n=3)
    
    # Get breadth and Nifty change
    breadth = sector_data.get("breadth", 0.5)
    nifty_change = sector_data.get("nifty_change", 0)
    
    # Generate components
    stock_table = generate_stock_comparison_table(stocks[:10], include_price=True)
    breadth_insight = generate_breadth_insight(stocks, breadth, sector_name)
    actionable_takeaway = generate_actionable_takeaway(
        sector_name, leaders, laggards, breadth, nifty_change
    )
    
    # Generate decision-oriented TL;DR
    if leaders:
        leader_names = ", ".join([s.get("symbol", "") for s in leaders[:3]])
        tldr = f"{sector_name} is "
        
        if leaders[0].get("change_percent", 0) > nifty_change:
            tldr += f"outperforming Nifty, but leadership is narrow. "
        else:
            tldr += f"underperforming Nifty with mixed signals. "
        
        tldr += f"Gains are driven mainly by {leader_names}."
    else:
        tldr = f"{sector_name} sector shows weak performance with no clear leaders."
    
    return {
        "tldr": tldr,
        "stock_table": stock_table,
        "leaders": leaders,
        "laggards": laggards,
        "breadth_insight": breadth_insight,
        "actionable_takeaway": actionable_takeaway,
        "stocks": stocks
    }
