"""
LangGraph node functions for the state machine.
"""
import time
import asyncio
from datetime import datetime
from typing import Dict, Any
import logging
import pytz

from src.graph.state import ChatState
from src.intent_classifier import get_intent_classifier, QueryIntent
from src.data.vector_store import get_vector_store
from src.data.mongo_client import get_mongo_client
from src.data.enhanced_mongo_client import get_enhanced_mongo_client  # NEW: Enhanced MongoDB client
from src.data.perplexity_client import get_perplexity_client
from src.data.zerodha_client import get_zerodha_client  # For portfolio only
from src.data.dhan_client import get_dhan_client  # For market data
from src.data.market_snapshot import get_market_snapshot_client
from src.models.model_router import get_model_router
from src.models.prompt_templates import get_prompt_templates, PromptTemplates
from src.models.data_confidence import get_data_confidence
from src.blueprints.canonical_intents import CanonicalIntent
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from src.config import settings

logger = logging.getLogger(__name__) # Added
templates = PromptTemplates() # Added


# PHASE 5: Helper function for shareholding pattern trend analysis
def calculate_shareholding_trends(shareholding_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate trends in shareholding pattern from quarterly data.
    
    Args:
        shareholding_data: Shareholding pattern data with quarterly/yearly data
        
    Returns:
        Dict with FII, DII, and promoter trends (change amounts and directions)
    """
    if not shareholding_data or "data" not in shareholding_data:
        return {}
    
    data_list = shareholding_data.get("data", [])
    if not data_list or len(data_list) < 2:
        return {}
    
    # Get latest and previous period data
    latest = data_list[0] if isinstance(data_list[0], dict) else {}
    previous = data_list[1] if len(data_list) > 1 and isinstance(data_list[1], dict) else {}
    
    trends = {}
    
    # Calculate FII trend
    fii_latest = latest.get("fiis", 0) or latest.get("fii", 0)
    fii_prev = previous.get("fiis", 0) or previous.get("fii", 0)
    if fii_prev and fii_latest:
        trends["fii_change"] = round(fii_latest - fii_prev, 2)
        trends["fii_direction"] = "increasing" if trends["fii_change"] > 0 else "decreasing"
        trends["fii_latest"] = fii_latest
    
    # Calculate DII trend
    dii_latest = latest.get("diis", 0) or latest.get("dii", 0)
    dii_prev = previous.get("diis", 0) or previous.get("dii", 0)
    if dii_prev and dii_latest:
        trends["dii_change"] = round(dii_latest - dii_prev, 2)
        trends["dii_direction"] = "increasing" if trends["dii_change"] > 0 else "decreasing"
        trends["dii_latest"] = dii_latest
    
    # Calculate promoter trend
    promoter_latest = latest.get("promoters", 0) or latest.get("promoter", 0)
    promoter_prev = previous.get("promoters", 0) or previous.get("promoter", 0)
    if promoter_prev and promoter_latest:
        trends["promoter_change"] = round(promoter_latest - promoter_prev, 2)
        trends["promoter_direction"] = "increasing" if trends["promoter_change"] > 0 else "decreasing"
        trends["promoter_latest"] = promoter_latest
    
    return trends


def get_market_status() -> Dict[str, Any]:
    """
    Get current market status and timestamp for India (IST).
    
    Returns:
        Dict with timestamp, market status, and data type
    """
    from datetime import datetime
    import pytz
    
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Market hours: 9:15 AM - 3:30 PM IST, Monday-Friday
    is_weekday = now.weekday() < 5  # 0=Monday, 4=Friday
    market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_market_hours = market_open_time <= now <= market_close_time
    is_open = is_weekday and is_market_hours
    
    return {
        "timestamp": now.strftime("%d %b %Y, %I:%M %p IST"),
        "date_only": now.strftime("%d %b %Y"),
        "is_open": is_open,
        "status": "Market Open" if is_open else "Market Closed",
        "data_type": "Live from Zerodha Kite" if is_open else "Previous close"
    }


async def classify_intent_node(state: ChatState) -> Dict[str, Any]:
    """
    Classify user query intent using canonical intent system.
    
    NEW: Uses pattern-based canonical intent mapper for fast, deterministic classification.
    Falls back to legacy intent classifier for backward compatibility.
    
    Returns updated state with canonical intent and stock symbols.
    """
    query = state["query"]
    classifier = get_intent_classifier()
    
    # Check for greetings first (hardcoded responses - no LLM needed)
    greeting_patterns = [
        r'^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\s*[!.?]*\s*$',
        r'^\s*(what\'s up|whats up|sup|yo)\s*[!.?]*\s*$',
        r'^\s*(how are you|how\'s it going)\s*[!.?]*\s*$',
    ]
    
    import re
    query_lower = query.lower().strip()
    for pattern in greeting_patterns:
        if re.match(pattern, query_lower, re.IGNORECASE):
            return {
                "intent": QueryIntent.GENERAL,
                "stock_symbols": [],
                "reasoning_steps": ["Detected greeting - using hardcoded response"],
                "is_greeting": True,
                "canonical_intent": "stock_overview",  # Default
                "canonical_confidence": 1.0
            }
    
    # NEW (Phase 1): Get conversation context and resolve ambiguous queries
    from src.memory import get_conversation_memory
    memory = get_conversation_memory()
    
    session_id = state.get("session_id", "default")
    context = await memory.get_context(session_id)
    
    # NEW: Query Normalization - Convert casual queries to structured queries
    from src.intelligence.query_normalizer import get_query_normalizer
    
    normalizer = get_query_normalizer()
    original_query = query
    
    # Normalize if query is ambiguous or casual
    if normalizer.is_ambiguous_or_casual(query):
        logger.info(f"Query is ambiguous, normalizing: '{query}'")
        query = await normalizer.normalize(query, {
            "last_stocks": context.get("last_stocks", []),
            "last_intent": context.get("last_intent")
        })
        logger.info(f"Normalized query: '{query}'")
    
    # Resolve ambiguous queries using conversation context (legacy)
    if context.get("has_context") and query == original_query:
        resolved_query = await memory.resolve_ambiguity(query, context)
        if resolved_query != query:
            logger.info(f"Resolved ambiguous query: '{query}' → '{resolved_query}'")
            query = resolved_query
    
    # Extract stock symbols (may find more after normalization)
    symbols = classifier.extract_stock_symbols(query)
    
    # If no symbols found but context has stocks, use them
    if not symbols and context.get("last_stocks"):
        symbols = context.get("last_stocks", [])[:1]  # Use most recent
        logger.info(f"Using stock from context: {symbols}")
    
    # NEW: Use canonical intent mapper (pattern-based, fast)
    from src.blueprints.intent_mapper import get_intent_mapper
    from src.blueprints.legacy_mapper import map_legacy_intent
    
    intent_mapper = get_intent_mapper()
    canonical_classification = intent_mapper.classify(query, symbols)
    
    # Also get legacy intent for backward compatibility
    legacy_classification = classifier.classify(query)
    
    # Build reasoning
    reasoning = f"Canonical: {canonical_classification.intent.value} ({canonical_classification.confidence:.2f})"
    reasoning += f" | Legacy: {legacy_classification.primary_intent.value}"
    if symbols:
        reasoning += f" | Symbols: {', '.join(symbols)}"
    if query != original_query:
        reasoning += f" | Resolved from: '{original_query}'"
    
    logger.info(f"Intent classification: {reasoning}")
    
    return {
        # Legacy fields (for backward compatibility)
        "intent": legacy_classification.primary_intent,
        "stock_symbols": symbols,
        "reasoning_steps": [reasoning],
        "is_greeting": False,
        
        # NEW: Canonical intent fields
        "canonical_intent": canonical_classification.intent.value,
        "canonical_confidence": canonical_classification.confidence,
        "canonical_reasoning": canonical_classification.reasoning,
        
        # NEW (Phase 1): Conversation context
        "last_mentioned_stocks": context.get("last_stocks", []),
        "conversation_history": context.get("conversation_history", []),
    }


async def fetch_vector_context_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch relevant context from Pinecone vector store.
    
    Used for fundamental analysis queries.
    """
    query = state["query"]
    symbols = state.get("stock_symbols", [])
    
    vector_store = get_vector_store()
    
    # Fetch context
    if symbols:
        # Search for specific companies
        all_docs = []
        for symbol in symbols[:3]:  # Limit to 3 companies
            docs = await vector_store.search_by_company(query, symbol, top_k=3)
            all_docs.extend(docs)
    else:
        # General search
        all_docs = await vector_store.search(query, top_k=5)
    
    reasoning = f"Retrieved {len(all_docs)} documents from vector store"
    
    return {
        "vector_context": all_docs,
        "reasoning_steps": [reasoning]
    }


async def fetch_structured_data_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch structured data from MongoDB.
    
    Enhanced to use new schema with:
    - Quarterly financials from financial_statements collection
    - Trend analysis (8 quarters)
    - Corporate actions (dividends, splits, bonus, rights)
    - Company information
    """
    symbols = state.get("stock_symbols", [])
    intent = state.get("intent", "")
    
    if not symbols:
        return {
            "structured_data": {},
            "reasoning_steps": ["No symbols to fetch data for"]
        }
    
    mongo = get_mongo_client()
    structured_data = {}
    
    for symbol in symbols[:3]:  # Limit to 3 companies
        # PHASE 3: Fetch all data in parallel for optimal performance
        # This reduces latency from ~300ms to ~100ms per stock (3x improvement)
        tasks = [
            mongo.get_latest_quarterly_financials(symbol),
            mongo.get_quarterly_financials(symbol, quarters=8),
            mongo.get_financial_trend(symbol, "revenue", quarters=8),
            mongo.get_financial_trend(symbol, "net_profit", quarters=8),
            mongo.get_dividend_history(symbol, limit=5),
            mongo.get_all_corporate_actions(symbol, limit=10),
            mongo.get_company_info(symbol),
            mongo.get_stock_details(symbol),  # Legacy fallback
            mongo.get_table_by_name(symbol, "Segment", "FY2024"),  # PHASE 1
            mongo.get_table_by_name(symbol, "Geographic", "FY2024"),  # PHASE 1
            mongo.get_sector_peers(symbol, limit=5),  # PHASE 2
        ]
        
        # PHASE 5: Add shareholding pattern for institutional activity tracking
        enhanced_mongo = get_enhanced_mongo_client()
        tasks.append(enhanced_mongo.get_shareholding_pattern(symbol, period="quarterly"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Unpack results
        (latest_quarterly, quarterly_trend, revenue_trend, profit_trend,
         dividend_history, all_actions, company_info, details,
         segment_table, geo_table, peers, shareholding) = results
        
        # Build symbol_data from results
        symbol_data = {}
        
        # 1. Latest quarterly financials
        if not isinstance(latest_quarterly, Exception) and latest_quarterly:
            symbol_data["latest_quarterly"] = latest_quarterly
            symbol_data["latest_period"] = latest_quarterly.get("quarter_label")
            symbol_data["latest_data"] = latest_quarterly.get("data", {})
        
        # 2. Quarterly trend
        if not isinstance(quarterly_trend, Exception) and quarterly_trend:
            symbol_data["quarterly_trend"] = quarterly_trend
        
        # 3. Revenue trend
        if not isinstance(revenue_trend, Exception) and revenue_trend:
            symbol_data["revenue_trend"] = revenue_trend
        
        # 4. Profit trend
        if not isinstance(profit_trend, Exception) and profit_trend:
            symbol_data["profit_trend"] = profit_trend
        
        # 5. Dividend history
        if not isinstance(dividend_history, Exception) and dividend_history:
            symbol_data["dividend_history"] = dividend_history
        
        # 6. Corporate actions
        if not isinstance(all_actions, Exception) and all_actions:
            symbol_data["corporate_actions"] = all_actions
        
        # 7. Company info
        if not isinstance(company_info, Exception) and company_info:
            symbol_data["company_info"] = company_info
        
        # 8. Segment breakdown (PHASE 1)
        if not isinstance(segment_table, Exception) and segment_table:
            symbol_data["segment_breakdown"] = segment_table
        
        # 9. Geographic revenue (PHASE 1)
        if not isinstance(geo_table, Exception) and geo_table:
            symbol_data["geographic_revenue"] = geo_table
        
        # 10. Peer companies (PHASE 2)
        if not isinstance(peers, Exception) and peers:
            symbol_data["peers"] = peers
            
            # Fetch peer metrics for top 3 peers for comparison
            peer_metrics = []
            for peer in peers[:3]:
                peer_ticker = peer.get("ticker") or peer.get("symbol")
                if peer_ticker:
                    peer_info = await mongo.get_company_info(peer_ticker)
                    if peer_info:
                        peer_metrics.append({
                            "symbol": peer_ticker,
                            "name": peer.get("name") or peer.get("display_name"),
                            "sector": peer.get("sector"),
                            "market_cap": peer_info.get("market_cap")
                        })
            
            if peer_metrics:
                symbol_data["peer_comparison"] = peer_metrics
        
        # 11. Shareholding pattern with trends (PHASE 5)
        if not isinstance(shareholding, Exception) and shareholding:
            symbol_data["shareholding"] = shareholding
            # Calculate institutional activity trends
            trends = calculate_shareholding_trends(shareholding)
            if trends:
                symbol_data["shareholding_trends"] = trends
        
        # LEGACY: Stock details (backward compatibility)
        if not isinstance(details, Exception) and details:
            symbol_data["details"] = details
        
        # LEGACY: Get latest financials (old schema - fallback)
        if not latest_quarterly or isinstance(latest_quarterly, Exception):
            financials = await mongo.get_latest_financials(symbol)
            if financials:
                symbol_data["financials"] = financials
        
        structured_data[symbol] = symbol_data

    
    # PHASE 4: Add balance sheet & cashflow for fundamental analysis queries
    # Only fetch for FUNDAMENTAL intent or deep dive/risk analysis canonical intents
    canonical_intent = state.get("canonical_intent", "")
    if intent == QueryIntent.FUNDAMENTAL or canonical_intent in ["stock_deep_dive", "risk_analysis"]:
        # Use EnhancedMongoClient for balance sheet and cashflow
        enhanced_mongo = get_enhanced_mongo_client()
        
        for symbol in structured_data.keys():
            # Fetch balance sheet and cashflow in parallel
            balance_sheet_task = enhanced_mongo.get_balance_sheet(symbol)
            cashflow_task = enhanced_mongo.get_cashflow(symbol)
            
            balance_sheet, cashflow = await asyncio.gather(
                balance_sheet_task, cashflow_task, return_exceptions=True
            )
            
            if not isinstance(balance_sheet, Exception) and balance_sheet:
                structured_data[symbol]["balance_sheet"] = balance_sheet
            
            if not isinstance(cashflow, Exception) and cashflow:
                structured_data[symbol]["cashflow"] = cashflow
    
    # Build detailed reasoning
    data_sources = []
    if any("latest_quarterly" in data for data in structured_data.values()):
        data_sources.append("quarterly financials")
    if any("revenue_trend" in data for data in structured_data.values()):
        data_sources.append("trend analysis")
    if any("dividend_history" in data for data in structured_data.values()):
        data_sources.append("dividend history")
    if any("corporate_actions" in data for data in structured_data.values()):
        data_sources.append("corporate actions")
    
    reasoning = f"Fetched {', '.join(data_sources)} for {len(structured_data)} companies from MongoDB"
    
    return {
        "structured_data": structured_data,
        "reasoning_steps": [reasoning]
    }


async def fetch_news_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch recent news with latency optimization.
    
    Strategy for low latency:
    1. Try Indian API first (faster, Indian-focused, 6-hour cache)
    2. Fallback to Perplexity if needed (5-second timeout)
    3. Parallel execution with other graph nodes
    4. Return immediately if cached
    
    Used for news, fundamental analysis, and comprehensive stock queries.
    """
    import asyncio
    import time
    
    start_time = time.time()
    query = state["query"]
    symbols = state.get("stock_symbols", [])
    
    news_data = {}
    sources_used = []
    
    # OPTIMIZATION 1: Try Indian API first (faster, cached)
    if symbols:
        try:
            from src.services.indian_api_service import get_indian_api_service
            indian_api = get_indian_api_service()
            
            # Fetch company news (6-hour cache, <50ms if cached)
            indian_news = await asyncio.wait_for(
                indian_api.get_company_news(symbols[0], limit=5),
                timeout=2.0  # 2-second timeout
            )
            
            if indian_news:
                news_data["indian_api"] = indian_news
                sources_used.append("Indian API")
                logger.info(f"✅ Indian API news: {len(indian_news)} items")
        except asyncio.TimeoutError:
            logger.warning("Indian API timeout (>2s), skipping")
        except Exception as e:
            logger.warning(f"Indian API error: {e}")
    
    # OPTIMIZATION 2: Perplexity for comprehensive search (5-second timeout)
    # Only if we need more context or Indian API failed
    should_use_perplexity = (
        not news_data or  # No Indian API data
        state.get("intent") == QueryIntent.NEWS or  # Explicit news query
        state.get("canonical_intent") in ["news_analysis", "stock_deep_dive"]  # Deep analysis
    )
    
    if should_use_perplexity:
        try:
            perplexity = get_perplexity_client()
            
            # Fetch with timeout
            if symbols:
                # Company-specific news
                # NOTE: search_domain_filter not supported by Perplexity client
                perplexity_task = perplexity.get_company_news(
                    symbols[0],
                    days=7
                )
            else:
                # General news search
                perplexity_task = perplexity.search_news(
                    query,
                    recency_filter="week"
                )
            
            perplexity_data = await asyncio.wait_for(
                perplexity_task,
                timeout=5.0  # 5-second timeout
            )
            
            if perplexity_data and "error" not in perplexity_data:
                news_data["perplexity"] = perplexity_data
                sources_used.append("Perplexity")
                logger.info(f"✅ Perplexity news fetched")
            
        except asyncio.TimeoutError:
            logger.warning("Perplexity timeout (>5s), skipping")
        except Exception as e:
            logger.warning(f"Perplexity error: {e}")
    
    elapsed = time.time() - start_time
    
    # Build reasoning
    if sources_used:
        reasoning = f"Fetched news from {', '.join(sources_used)} in {elapsed:.2f}s"
    else:
        reasoning = f"No news data available (attempted in {elapsed:.2f}s)"
    
    logger.info(reasoning)
    
    return {
        "news_data": news_data,
        "reasoning_steps": [reasoning]
    }


async def fetch_market_data_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch live market data (OHLC, LTP) from Dhan API.
    
    NEW: Falls back to Perplexity Sonar web search for stocks not found in Dhan.
    This handles foreign stocks, delisted stocks, new IPOs, and missing symbols.
    
    NOTE: Uses Dhan for market data (faster, simpler auth).
    Zerodha is only used for portfolio queries.
    
    Returns OHLC data (Open, High, Low, Close, Last Price, Change %)
    for detected stock symbols.
    """
    import time
    start_time = time.time()
    
    symbols = state.get("stock_symbols", [])
    
    if not symbols:
        return {"market_data": {}, "reasoning_steps": []}
    
    # Use Dhan for market data
    dhan = get_dhan_client()
    
    if not dhan.dhan:
        logger.warning("Dhan client not initialized - skipping market data fetch")
        return {"market_data": {}, "reasoning_steps": []}
    
    market_data = {}
    
    # Fetch OHLC for up to 3 stocks (to keep latency low)
    # Dhan supports batch fetching (up to 1000 instruments)
    try:
        symbols_batch = symbols[:3]
        logger.info(f"Fetching OHLC from Dhan for: {symbols_batch}")
        
        # Batch fetch OHLC data
        ohlc_data = await dhan.get_ohlc(symbols_batch, exchange="NSE_EQ")
        
        for symbol, data in ohlc_data.items():
            market_data[symbol] = {
                **data,
                "source": "dhan_api"
            }
            
    except Exception as e:
        logger.error(f"Error fetching OHLC from Dhan: {e}")
    
    # NEW: Identify symbols with no data from Dhan
    missing_symbols = [s for s in symbols_batch if s not in market_data]
    
    # NEW: Fallback to Perplexity for missing symbols
    if missing_symbols:
        logger.info(f"⚠️ Dhan data missing for {missing_symbols}, falling back to Perplexity web search")
        
        try:
            perplexity = get_perplexity_client()
            
            # Fetch data for each missing symbol
            for symbol in missing_symbols:
                logger.info(f"Searching Perplexity for: {symbol}")
                
                # Use search_indian_stock with price query type
                perplexity_result = await perplexity.search_indian_stock(
                    symbol=symbol,
                    query_type="price"
                )
                
                if perplexity_result and "answer" in perplexity_result:
                    # Mark as fallback source
                    market_data[symbol] = {
                        "perplexity_data": perplexity_result.get("answer", ""),
                        "citations": perplexity_result.get("citations", []),
                        "source": "perplexity_fallback",
                        "fallback_reason": "Stock not found in Dhan (may be foreign stock, delisted, or new IPO)"
                    }
                    logger.info(f"✅ Perplexity fallback successful for {symbol}")
                else:
                    logger.warning(f"❌ Perplexity fallback failed for {symbol}")
                    
        except Exception as e:
            logger.error(f"Error in Perplexity fallback: {e}")
    
    elapsed = time.time() - start_time
    
    # Build reasoning message
    dhan_count = len([v for v in market_data.values() if v.get("source") == "dhan_api"])
    fallback_count = len([v for v in market_data.values() if v.get("source") == "perplexity_fallback"])
    
    reasoning_parts = []
    if dhan_count > 0:
        reasoning_parts.append(f"Dhan API: {dhan_count} stocks")
    if fallback_count > 0:
        reasoning_parts.append(f"Perplexity fallback: {fallback_count} stocks")
    
    reasoning = f"Fetched market data ({', '.join(reasoning_parts)}) in {elapsed:.2f}s"
    logger.info(reasoning)
    
    return {
        "market_data": market_data,
        "reasoning_steps": [reasoning]
    }



async def fetch_portfolio_data_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch user's Zerodha portfolio data if connected.
    
    This node checks if the user has a connected Zerodha account and fetches
    their portfolio (holdings, positions, margins) to provide personalized responses.
    
    Returns:
        portfolio_data: User's complete portfolio or None
        portfolio_context: Formatted portfolio string for LLM
    """
    import time
    start_time = time.time()
    
    # Get session_id from state
    session_id = state.get("session_id")
    
    if not session_id:
        logger.warning("No session_id in state - skipping portfolio fetch")
        return {
            "portfolio_data": None,
            "portfolio_context": None,
            "reasoning_steps": ["No session_id available"]
        }
    
    # Import portfolio service
    from src.data.zerodha_portfolio import get_complete_portfolio, format_portfolio_for_ai
    from src.auth.zerodha_oauth import is_zerodha_connected
    
    # Check if user is connected
    is_connected = await is_zerodha_connected(session_id)
    
    if not is_connected:
        logger.info(f"User {session_id[:8]}... not connected to Zerodha")
        return {
            "portfolio_data": None,
            "portfolio_context": None,
            "reasoning_steps": ["User not connected to Zerodha"]
        }
    
    # Fetch portfolio data
    try:
        portfolio = await get_complete_portfolio(session_id)
        
        if not portfolio:
            logger.warning(f"Failed to fetch portfolio for {session_id[:8]}...")
            return {
                "portfolio_data": None,
                "portfolio_context": None,
                "reasoning_steps": ["Portfolio fetch failed (token may be expired)"]
            }
        
        # Format for AI
        portfolio_context = format_portfolio_for_ai(portfolio)
        
        elapsed = time.time() - start_time
        logger.info(f"Portfolio fetch completed in {elapsed:.2f}s for {session_id[:8]}...")
        
        # Count holdings
        num_holdings = len(portfolio.get("holdings", []))
        num_positions = len(portfolio.get("positions", {}).get("net", []))
        
        reasoning = f"Fetched user portfolio: {num_holdings} holdings, {num_positions} positions"
        
        return {
            "portfolio_data": portfolio,
            "portfolio_context": portfolio_context,
            "reasoning_steps": [reasoning]
        }
        
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return {
            "portfolio_data": None,
            "portfolio_context": None,
            "reasoning_steps": [f"Portfolio fetch error: {str(e)}"]
        }


async def fetch_market_overview_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch comprehensive market overview with institutional-grade analytics.
    
    Enhanced with:
    - Nifty 50 constituent analysis (top contributors by weight)
    - Sectoral performance breakdown
    - Technical indicators (DMAs, RSI)
    - India VIX for volatility context
    - Optimized web searches (reduced from 4 to 2)
    """
    import time
    start_time = time.time()
    
    from src.data.nifty_analytics import (
        fetch_constituent_performance,
        calculate_top_contributors,
        get_sectoral_breakdown,
        get_technical_indicators,
        get_india_vix
    )
    from src.data.nse_client import get_nse_client
    
    perplexity = get_perplexity_client()
    zerodha = get_zerodha_client()
    nse = get_nse_client()
    
    # Fetch all data in parallel for optimal latency
    tasks = []
    
    # 1. Fetch live index data from Zerodha
    index_task = asyncio.gather(*[
        zerodha.get_ohlc("NIFTY 50"),
        zerodha.get_ohlc("NIFTY BANK"),
        zerodha.get_ohlc("SENSEX")
    ])
    tasks.append(index_task)
    
    # 2. Fetch Nifty 50 constituent performance (top 10 stocks)
    tasks.append(fetch_constituent_performance(top_n=10))
    
    # 3. Fetch technical indicators (DMAs, RSI, MACD)
    tasks.append(get_technical_indicators("NIFTY 50"))
    
    # 4. Fetch India VIX
    tasks.append(get_india_vix())
    
    # 5. Fetch P/E and P/B from NSE
    tasks.append(nse.get_index_pe_pb("NIFTY 50"))
    
    # 6. Fetch FII/DII flows from NSE
    tasks.append(nse.get_fii_dii_data())
    
    # 7. Optimized web searches (reduced from 4 to 2)
    # Only sector performance and FII/DII activity get from Zerodha
    tasks.append(perplexity.web_search(
        query="Indian stock market sector performance today NSE",
        country="IN",
        max_results=3  # Reduced from 5
    ))
    tasks.append(perplexity.web_search(
        query="FII DII activity India stock market today",
        country="IN",
        max_results=3
    ))
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Unpack results
    indices_data = results[0]
    constituent_data = results[1]
    technical_indicators = results[2]
    volatility = results[3]
    nse_valuation = results[4]  # P/E, P/B from NSE
    nse_fii_dii = results[5]  # FII/DII from NSE
    sector_search = results[6]
    fii_dii_search = results[7]
    
    # Process index data
    index_dict = {}
    if not isinstance(indices_data, Exception) and indices_data:
        nifty_data, bank_nifty_data, sensex_data = indices_data
        if nifty_data:
            index_dict["NIFTY 50"] = nifty_data
        if bank_nifty_data:
            index_dict["NIFTY BANK"] = bank_nifty_data
        if sensex_data:
            index_dict["SENSEX"] = sensex_data
    
    # Process constituent data
    top_contributors = {}
    sectoral_performance = {}
    
    if not isinstance(constituent_data, Exception) and constituent_data:
        top_contributors = await calculate_top_contributors(constituent_data, top_n=3)
        sectoral_performance = await get_sectoral_breakdown(constituent_data)
    
    # Prepare response data
    market_overview_data = {
        "_index_data": index_dict,
        "_top_contributors": top_contributors,
        "_sectoral_performance": sectoral_performance,
        "_technical_indicators": technical_indicators if not isinstance(technical_indicators, Exception) else {},
        "_volatility": volatility if not isinstance(volatility, Exception) else {},
        "_nse_valuation": nse_valuation if not isinstance(nse_valuation, Exception) else {},  # P/E, P/B
        "_nse_fii_dii": nse_fii_dii if not isinstance(nse_fii_dii, Exception) else {},  # FII/DII flows
        "sector_performance_search": sector_search if not isinstance(sector_search, Exception) else {"results": []},
        "fii_dii_search": fii_dii_search if not isinstance(fii_dii_search, Exception) else {"results": []}
    }
    
    elapsed = time.time() - start_time
    logger.info(f"Enhanced market overview completed in {elapsed:.2f}s")
    
    reasoning = f"Fetched indices + {len(constituent_data)} constituents + technical indicators + 2 web searches"
    
    return {
        "market_overview_data": market_overview_data,
        "reasoning_steps": [reasoning]
    }


async def fetch_sector_data_node(state: ChatState) -> Dict[str, Any]:
    """
    Fetch comprehensive sector performance data for time-sensitive queries.
    
    This is the KEY FIX for "which sector is growing this year?" type queries.
    
    Sources:
    1. Zerodha - Live sectoral indices (NIFTY IT, NIFTY BANK, etc.)
    2. Perplexity - Current 2025 market context and sector trends
    
    Returns:
        sector_data: Dict with all sector performance metrics
        sector_news: Dict with Perplexity search results
    """
    import pytz
    from datetime import datetime
    
    start_time = time.time()
    
    # Get current time for context injection
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_year = now.year  # 2025
    current_date = now.strftime("%d %b %Y")
    
    logger.info(f"Fetching sector data for {current_date} (year: {current_year})")
    
    # Import sector performance function
    from src.data.sectoral_indices import get_sector_performance
    
    # Fetch in parallel: Zerodha sector data + Perplexity context
    perplexity = get_perplexity_client()
    
    # Optimize Perplexity query for better results
    from src.intelligence.perplexity_optimizer import get_perplexity_optimizer
    optimizer = get_perplexity_optimizer()
    optimized_query = optimizer.optimize_query(
        user_query=f"India stock market sector performance {current_year}",
        query_type="sector_analysis",
        urgency="high"
    )
    
    sector_task = get_sector_performance(timeframe="5D")
    perplexity_task = perplexity.search_news(
        query=optimized_query,
        recency_filter="week",
        max_results=5
    )
    
    sector_data, perplexity_context = await asyncio.gather(
        sector_task, perplexity_task, return_exceptions=True
    )
    
    # Handle exceptions
    if isinstance(sector_data, Exception):
        logger.error(f"Sector data fetch failed: {sector_data}")
        sector_data = {"error": str(sector_data), "sectors": []}
    
    if isinstance(perplexity_context, Exception):
        logger.error(f"Perplexity sector search failed: {perplexity_context}")
        perplexity_context = {"error": str(perplexity_context), "answer": ""}
    
    # Add current year context to help the LLM
    sector_data["current_year"] = current_year
    sector_data["current_date"] = current_date
    sector_data["data_freshness"] = f"Live data as of {current_date}"
    
    elapsed = time.time() - start_time
    logger.info(f"Sector data fetch completed in {elapsed:.2f}s")
    
    reasoning = f"Fetched {len(sector_data.get('sectors', []))} sector indices from Zerodha + Perplexity {current_year} context"
    
    return {
        "sector_data": sector_data,
        "sector_news": perplexity_context,
        "reasoning_steps": [reasoning]
    }


async def synthesize_response_node(state: ChatState) -> Dict[str, Any]:
    """
    Synthesize final response using LLM.
    
    Selects appropriate model and generates response.
    """
    start_time = time.time()
    
    # Handle greetings with hardcoded response (no LLM call needed)
    if state.get("is_greeting", False):
        greeting_response = """👋 **Hello! I'm AarthikAI, your India-focused financial intelligence assistant.**

I can help you with:
- 📊 **Live Stock Prices** - Real-time data from NSE/BSE via Zerodha
- 📰 **Latest News** - Market updates and company developments
- 📈 **Financial Analysis** - Fundamentals, technicals, and insights
- 💹 **Market Trends** - Sector performance and market sentiment

**Try asking:**
- "What's the current price of INFY?"
- "Tell me about Reliance Industries"
- "Show me TCS latest news"
- "What are the top performing stocks today?"

How can I assist you today?"""
        
        return {
            "response": greeting_response,
            "reasoning_steps": ["Returned hardcoded greeting (no LLM call)"],
            "latency_ms": (time.time() - start_time) * 1000,
            "cost_estimate": 0.0  # No cost for hardcoded response
        }
    
    
    query = state["query"]
    intent = state["intent"]
    vector_context = state.get("vector_context", [])
    structured_data = state.get("structured_data", {})
    news_data = state.get("news_data", {})
    symbols = state.get("stock_symbols", [])
    
    # Initialize variables that may be used in both blueprint and legacy paths
    templates = get_prompt_templates()  # Initialize early to avoid UnboundLocalError
    model_config = {"tier": "default", "name": "gpt-4o-mini"}  # Default config
    model_name = "openai/gpt-4o-mini"  # Default model
    
    # NEW: Check if we should use blueprint-based synthesis
    canonical_intent = state.get("canonical_intent")
    use_blueprints = canonical_intent is not None
    user_prompt = None  # Initialize to avoid UnboundLocalError
    
    if use_blueprints:
        logger.info(f"Using blueprint-based synthesis for intent: {canonical_intent}")
        
        # Build evidence object from fetched data
        from src.blueprints.evidence import get_evidence_builder
        from src.blueprints.prompts import get_blueprint_prompts
        
        evidence_builder = get_evidence_builder()
        blueprint_prompts = get_blueprint_prompts()
        
        # Build evidence for stock queries
        if symbols and canonical_intent in ["stock_overview", "stock_deep_dive", "price_action", "risk_analysis", "trade_idea"]:
            symbol = symbols[0]
            market_data = state.get("market_data", {}).get(symbol)
            symbol_structured_data = structured_data.get(symbol)
            
            evidence = await evidence_builder.build_stock_evidence(
                symbol=symbol,
                market_data=market_data,
                structured_data=symbol_structured_data,
                news_data=news_data,
            )
            
            # Select appropriate blueprint prompt
            if canonical_intent == "stock_overview":
                user_prompt = blueprint_prompts.stock_overview_prompt(evidence.to_dict(), symbol, query)
            elif canonical_intent == "stock_deep_dive":
                user_prompt = blueprint_prompts.stock_deep_dive_prompt(evidence.to_dict(), symbol, query)
            elif canonical_intent == "price_action":
                user_prompt = blueprint_prompts.price_action_prompt(evidence.to_dict(), symbol, query)
            elif canonical_intent == "risk_analysis":
                user_prompt = blueprint_prompts.risk_analysis_prompt(evidence.to_dict(), symbol, query)
            elif canonical_intent == "trade_idea":
                user_prompt = blueprint_prompts.trade_idea_prompt(evidence.to_dict(), symbol, query)
            else:
                # Fallback to legacy
                use_blueprints = False
        
        # Build evidence for comparison
        elif canonical_intent == "stock_comparison" and len(symbols) >= 2:
            symbol_a, symbol_b = symbols[0], symbols[1]
            
            market_data_a = state.get("market_data", {}).get(symbol_a)
            market_data_b = state.get("market_data", {}).get(symbol_b)
            
            evidence_a = await evidence_builder.build_stock_evidence(
                symbol=symbol_a,
                market_data=market_data_a,
                structured_data=structured_data.get(symbol_a),
                news_data=news_data,
            )
            
            evidence_b = await evidence_builder.build_stock_evidence(
                symbol=symbol_b,
                market_data=market_data_b,
                structured_data=structured_data.get(symbol_b),
                news_data=news_data,
            )
            
            user_prompt = blueprint_prompts.stock_comparison_prompt(
                evidence_a.to_dict(),
                evidence_b.to_dict(),
                symbol_a,
                symbol_b,
                query
            )
        
        # Build evidence for sector queries
        elif canonical_intent in ["sector_overview", "sector_rotation", "sector_comparison"]:
            # Extract sector from query
            sector_keywords = {
                'it': 'IT',
                'software': 'IT',
                'tech': 'IT',
                'technology': 'IT',
                'banking': 'Banking',
                'bank': 'Banking',
                'pharma': 'Pharma',
                'pharmaceutical': 'Pharma',
                'auto': 'Auto',
                'automobile': 'Auto',
                'fmcg': 'FMCG',
                'consumer': 'FMCG',
                'energy': 'Energy',
                'oil': 'Energy',
                'power': 'Energy',
                'metals': 'Metals',
                'metal': 'Metals',
                'mining': 'Metals',
                'steel': 'Metals',
                'telecom': 'Telecom',
                'telecommunication': 'Telecom',
                'media': 'Telecom',
                'realty': 'Realty',
                'real estate': 'Realty',
                'infrastructure': 'Realty',
                'capital goods': 'Capital Goods',
                'engineering': 'Capital Goods',
                'cement': 'Cement',
                'construction': 'Cement',
                'consumer durables': 'Consumer Durables',
                'durables': 'Consumer Durables',
                'appliances': 'Consumer Durables',
            }
            
            # For sector comparison, extract TWO sectors
            if canonical_intent == "sector_comparison":
                from src.intelligence import get_sector_intelligence
                
                query_lower = query.lower()
                sectors_found = []
                
                # Extract all mentioned sectors
                for keyword, sector_name in sector_keywords.items():
                    if keyword in query_lower and sector_name not in sectors_found:
                        sectors_found.append(sector_name)
                
                if len(sectors_found) >= 2:
                    sector_a = sectors_found[0]
                    sector_b = sectors_found[1]
                    
                    logger.info(f"Sector comparison: {sector_a} vs {sector_b}")
                    
                    # Get sector intelligence
                    sector_intel = get_sector_intelligence()
                    comparison_data = sector_intel.compare_sectors(sector_a, sector_b)
                    
                    if "error" not in comparison_data:
                        # Use sector comparison prompt
                        user_prompt = blueprint_prompts.sector_comparison_prompt(
                            sector_a=sector_a,
                            sector_b=sector_b,
                            comparison_data=comparison_data,
                            query=query
                        )
                    else:
                        # Fallback if sectors not found
                        logger.warning(f"Sector comparison failed: {comparison_data['error']}")
                        user_prompt = f"I don't have detailed profiles for {sector_a} and {sector_b} comparison yet. Please try IT, Energy, Banking, Auto, Pharma, or FMCG sectors."
                else:
                    logger.warning(f"Could not extract two sectors from query: {query}")
                    user_prompt = "Please specify two sectors to compare (e.g., 'compare IT and Energy sector')"
            
            # STOCK_DEEP_DIVE - Investment verdict with bull/bear analysis
            elif canonical_intent == "stock_deep_dive":
                from src.intelligence import get_reasoning_engine, get_sector_intelligence
                
                # Get symbol from state
                symbols = state.get("symbols", [])
                if symbols:
                    symbol = symbols[0]
                    company_name = state.get("company_names", {}).get(symbol, symbol)
                    
                    # Get fundamentals
                    fundamentals = state.get("fundamentals", {}).get(symbol, {})
                    
                    # Get price data from Redis cache
                    price_data = {}
                    try:
                        from src.data.redis_client import get_redis_cache
                        redis = get_redis_cache()
                        cached_ohlc = await redis.get(f"ohlc:NSE:{symbol}")
                        if cached_ohlc:
                            price_data = {
                                "current_price": cached_ohlc.get("close"),
                                "change_percent": cached_ohlc.get("change_percent"),
                                "high_52w": cached_ohlc.get("high_52w"),
                                "low_52w": cached_ohlc.get("low_52w"),
                                "volume": cached_ohlc.get("volume"),
                            }
                    except Exception as e:
                        logger.warning(f"Could not fetch price data: {e}")
                    
                    # Get reasoning insights
                    reasoning_engine = get_reasoning_engine()
                    reasoning = {}
                    if fundamentals:
                        try:
                            reasoning = {
                                "valuation": reasoning_engine.interpret_valuation(
                                    fundamentals.get("pe_ratio"),
                                    fundamentals.get("pb_ratio"),
                                    fundamentals.get("roe")
                                ),
                                "trends": reasoning_engine.interpret_trends(
                                    fundamentals.get("revenue_growth_qoq"),
                                    fundamentals.get("profit_growth_qoq"),
                                    fundamentals.get("margin_trend")
                                ),
                                "risk": reasoning_engine.interpret_risk(
                                    fundamentals.get("debt_to_equity"),
                                    fundamentals.get("current_ratio"),
                                    fundamentals.get("volatility")
                                ),
                            }
                        except Exception as e:
                            logger.warning(f"Reasoning engine error: {e}")
                    
                    # Get sector context
                    sector = fundamentals.get("sector", "Unknown")
                    
                    # Get news summary
                    news_summary = "Recent news not available"
                    news_data = state.get("news", [])
                    if news_data:
                        news_items = news_data[:3]  # Top 3 news
                        news_summary = "\n".join([f"- {item.get('title', 'N/A')}" for item in news_items])
                    
                    # Use stock deep dive prompt
                    user_prompt = blueprint_prompts.stock_deep_dive_prompt(
                        symbol=symbol,
                        company_name=company_name,
                        fundamentals=fundamentals,
                        price_data=price_data,
                        reasoning=reasoning,
                        sector=sector,
                        news_summary=news_summary,
                        query=query
                    )
                else:
                    logger.warning("No symbol found for stock_deep_dive intent")
                    user_prompt = "Please specify a company for investment analysis (e.g., 'Should I buy TCS?')"
            
            else:
                # Single sector queries (overview/rotation)
                sector = None
                query_lower = query.lower()
                for keyword, sector_name in sector_keywords.items():
                    if keyword in query_lower:
                        sector = sector_name
                        break
                
                if not sector:
                    sector = "General Market"
                
                logger.info(f"Extracted sector: {sector} from query: {query}")
                
                # Get Indian API news from Redis cache (populated by market_data_worker)
                indian_market_news = []
                try:
                    from src.data.redis_client import get_redis_cache
                    redis = get_redis_cache()
                    cached_news = await redis.get("market_news")
                    if cached_news:
                        indian_market_news = cached_news
                        logger.info(f"✅ Using cached market news ({len(indian_market_news)} items)")
                    else:
                        logger.warning("No cached market news found in Redis")
                except Exception as e:
                    logger.error(f"Error reading cached news from Redis: {e}")
                
                # Get sector data from state (contains Zerodha data)
                sector_data = state.get("sector_data", {})
                sector_news = state.get("sector_news", {})
                
                logger.info(f"Sector data keys: {list(sector_data.keys())}")
                logger.info(f"Number of sectors in data: {len(sector_data.get('sectors', []))}")
                
                # Merge Indian API news with existing news
                combined_news = news_data.copy() if news_data else {}
                if indian_market_news:
                    combined_news["indian_api_news"] = indian_market_news
                    combined_news["news_source"] = "Indian API (cached) + Perplexity"
                else:
                    combined_news["news_source"] = "Perplexity"
                
                # Build evidence with ACTUAL data + Indian API news
                evidence = evidence_builder.build_sector_evidence(
                    sector=sector,
                    sector_data=sector_data,
                    constituent_data=sector_data.get("sectors", []),
                    news_data=sector_news if sector_news else combined_news,
                )
                
                if canonical_intent == "sector_overview":
                    user_prompt = blueprint_prompts.sector_overview_prompt(evidence.to_dict(), sector, query)
                else:
                    user_prompt = blueprint_prompts.sector_rotation_prompt(evidence.to_dict(), query)
        
        else:
            # Fallback to legacy for unsupported intents
            use_blueprints = False
            logger.info(f"Blueprint not yet implemented for {canonical_intent}, falling back to legacy")
    
    # LEGACY: Use old prompt formatting if blueprints not used
    if not use_blueprints:
        # Select model
        router = get_model_router()
        # context_length = sum(len(str(doc)) for doc in vector_context) # Original line, replaced below
        
        # Convert intent enum to string for model router
        intent_str = intent.value.lower() if hasattr(intent, 'value') else str(intent).split('.')[-1].lower()
        has_market_data = bool(state.get("market_data"))
        
        model_config = router.select_model(
            intent=intent_str,
            query_length=len(query),
            context_length=len(str(vector_context)) + len(str(news_data)),
            requires_reasoning=(intent == QueryIntent.MULTI),
            has_market_data=has_market_data
        )
        
        # Build prompt
        templates = get_prompt_templates()
        system_prompt = templates.system_prompt()
        
        # Check if we have any context
        has_vector_context = bool(vector_context)
        has_structured_data = bool(structured_data)
        has_news = bool(news_data and news_data.get("answer"))
        has_market_data = bool(state.get("market_data"))
        
        # Fallback to Perplexity ONLY if no data found for stock queries
        # AND we don't have market data from Zerodha
        if not (has_vector_context or has_structured_data or has_news or has_market_data) and symbols:
            perplexity = get_perplexity_client()
            # Use India-specific search for stocks
            news_data = await perplexity.search_indian_stock(symbols[0], "comprehensive")
            has_news = bool(news_data.get("answer"))
        
        # Format context based on intent
        # Check for market overview first (takes precedence)
        market_overview_data = state.get("market_overview_data", {})
        if market_overview_data:
            # Use market overview prompt with web search results
            user_prompt = templates.market_overview_prompt(market_overview_data, query)
        
        # FIXED: Sector performance analysis - now properly inside if not use_blueprints block
        elif intent == QueryIntent.SECTOR_PERFORMANCE:
            # Use pre-fetched sector data from fetch_sector_data_node
            sector_data = state.get("sector_data", {})
            sector_news = state.get("sector_news", {})
            
            if not sector_data or "error" in sector_data:
                # Fallback to Perplexity if sector data unavailable
                sector_news_text = sector_news.get("answer", "") if sector_news else ""
                user_prompt = f"I apologize, but I'm unable to fetch live sector performance data at the moment. Here's what I found:\n\n{sector_news_text}\n\nQuestion: {query}"
            else:
                # Use sector performance prompt with real data
                user_prompt = templates.sector_performance_prompt(sector_data, query)
        
        # MUTUAL FUND queries - use Perplexity + structured prompt
        elif intent == QueryIntent.MUTUAL_FUND:
            perplexity = get_perplexity_client()
            
            # Search for mutual fund data using search_news method
            mf_query = f"Best performing mutual funds India {query}"
            mf_data = await perplexity.search_news(mf_query, recency_filter="month")
            mf_context = mf_data.get("answer", "") if mf_data else ""
            
            # Use mutual fund prompt template
            user_prompt = templates.mutual_fund_prompt(mf_context, query)
            logger.info(f"Using mutual_fund_prompt for query: {query[:50]}...")
        
        # GEOPOLITICS queries - use Perplexity + India impact mapper
        elif intent in [QueryIntent.GEO_NEWS, QueryIntent.SANCTIONS_STATUS, QueryIntent.MARKET_IMPACT, QueryIntent.INDIA_IMPACT]:
            from src.intelligence.geopolitics_query_builder import get_geopolitics_query_builder
            from src.intelligence.india_impact_mapper import get_india_impact_mapper
            from src.blueprints.geopolitics_prompts import GeopoliticsPrompts
            
            perplexity = get_perplexity_client()
            query_builder = get_geopolitics_query_builder()
            impact_mapper = get_india_impact_mapper()
            geo_prompts = GeopoliticsPrompts()
            
            # Build optimized query
            intent_str = intent.value if hasattr(intent, 'value') else str(intent)
            optimized_query, metadata = query_builder.build_query(query, intent_str)
            
            logger.info(f"Geopolitics query: {optimized_query}")
            logger.info(f"Entities: {metadata['entities']}")
            
            # Fetch Perplexity data
            recency_filter = "week" if metadata["recency_days"] <= 7 else "month"
            perplexity_data = await perplexity.search_news(optimized_query, recency_filter=recency_filter, max_results=5)
            
            # Fetch Indian API news if India-related
            indian_news = None
            if intent == QueryIntent.INDIA_IMPACT or "India" in metadata["entities"].get("countries", []):
                from src.data.indian_api_client import get_indian_api_client
                indian_api = get_indian_api_client()
                indian_news = await indian_api.get_market_news(limit=10)
            
            # Calculate India impact
            india_impact = None
            if intent in [QueryIntent.INDIA_IMPACT, QueryIntent.MARKET_IMPACT, QueryIntent.SANCTIONS_STATUS]:
                india_impact = impact_mapper.get_impact(query, metadata["entities"])
            
            # Generate prompt based on intent
            if intent == QueryIntent.SANCTIONS_STATUS:
                user_prompt = geo_prompts.sanctions_status_prompt(perplexity_data, india_impact, query)
            elif intent == QueryIntent.MARKET_IMPACT:
                market_data = state.get("market_data", {})
                user_prompt = geo_prompts.market_impact_prompt(perplexity_data, market_data, query)
            elif intent == QueryIntent.INDIA_IMPACT:
                user_prompt = geo_prompts.india_impact_prompt(perplexity_data, india_impact, query)
            else:  # GEO_NEWS
                user_prompt = geo_prompts.geo_news_prompt(perplexity_data, indian_news, query)
            
            logger.info(f"Using geopolitics prompt for intent: {intent}")
        
        
        # Vertical/segment analysis
        elif intent == QueryIntent.VERTICAL_ANALYSIS:
            from src.data.vertical_intelligence import get_vertical_performance
            from src.models.vertical_prompt import vertical_analysis_prompt
            
            company = symbols[0] if symbols else None
            if not company:
                user_prompt = f"Please specify a company for vertical analysis.\n\nQuestion: {query}"
            else:
                vertical_data = await get_vertical_performance(company, fiscal_year="FY2024")
                if "error" in vertical_data:
                    user_prompt = f"Unable to fetch vertical data for {company}. {vertical_data.get('error', '')}\n\nQuestion: {query}"
                else:
                    user_prompt = vertical_analysis_prompt(vertical_data, query)
        
        elif intent == QueryIntent.FUNDAMENTAL:
            context_text = "\n\n".join([doc["text"] for doc in vector_context[:5]])
            company = symbols[0] if symbols else "the company"
            user_prompt = templates.fundamental_analysis_prompt(company, context_text, query)
        
        elif intent == QueryIntent.NEWS:
            news_text = news_data.get("answer", "")
            company = symbols[0] if symbols else "the market"
            
            # Include market data if available (enriches news with current price)
            market_data = state.get("market_data", {})
            market_context = ""
            if market_data and symbols:
                symbol = symbols[0]
                if symbol in market_data:
                    data = market_data[symbol]
                    ltp = data.get("last_price", 0)
                    change = data.get("change", 0)
                    change_pct = data.get("change_percent", 0)
                    market_context = f"\n\nCurrent Price: ₹{ltp:,.2f} ({change_pct:+.2f}%)"
            
            # Use India-specific prompt for stock queries
            if symbols:
                user_prompt = templates.indian_stock_prompt(company, news_text + market_context, query)
            else:
                # GENERAL MARKET NEWS - Fetch comprehensive market snapshot
                snapshot_client = get_market_snapshot_client()
                
                try:
                    # Fetch market snapshot data
                    market_snapshot = await snapshot_client.get_full_snapshot()
                    
                    # Format FII/DII data
                    fii_dii = market_snapshot.get("fii_dii", {})
                    fii_dii_text = "Data pending (published after market close)"
                    if fii_dii and "error" not in fii_dii:
                        fii_net = fii_dii.get("fii_net", 0)
                        dii_net = fii_dii.get("dii_net", 0)
                        fii_dii_text = f"""FII: ₹{fii_net:,.0f} Cr ({"net buyers" if fii_net > 0 else "net sellers"})
DII: ₹{dii_net:,.0f} Cr ({"net buyers" if dii_net > 0 else "net sellers"})"""
                    
                    # Format Global Cues
                    global_cues = market_snapshot.get("global_cues", {})
                    global_text = "Data not available"
                    if global_cues and "indices" in global_cues:
                        indices = global_cues["indices"]
                        lines = []
                        for name, data in indices.items():
                            if "error" not in data:
                                change = data.get("change_pct", 0)
                                lines.append(f"{name.upper()}: {change:+.2f}%")
                        global_text = " | ".join(lines) if lines else "Data not available"
                    
                    # Format Forex
                    forex = market_snapshot.get("forex_commodities", {})
                    forex_text = "Data not available"
                    if forex and "error" not in forex:
                        usdinr = forex.get("usdinr", {})
                        brent = forex.get("brent_crude", {})
                        forex_text = f"""USD/INR: ₹{usdinr.get('price', 0):.2f} ({usdinr.get('change_pct', 0):+.2f}%)
Brent Crude: ${brent.get('price', 0):.2f}/bbl"""
                    
                    # Fetch headlines from Perplexity with improved query
                    perplexity = get_perplexity_client()
                    
                    # Use improved query builder for better news quality
                    news_query = perplexity.build_market_news_query(date_str="today", focus="general")
                    
                    headlines = await perplexity.search_news(
                        news_query,
                        recency_filter="day"
                    )
                    headlines_text = headlines.get("answer", "No headlines available") if headlines else "No headlines available"
                    
                except Exception as e:
                    logger.error(f"Error fetching market snapshot: {e}")
                    fii_dii_text = "Data temporarily unavailable"
                    global_text = "Data temporarily unavailable"
                    forex_text = "Data temporarily unavailable"
                    headlines_text = news_text if news_text else "No headlines available"
                
                # Build comprehensive market news prompt with STRICT NO-HALLUCINATION rules
                current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
                
                user_prompt = f"""You are a financial markets analyst. Your job is to FORMAT the data provided - NOT to create new data.

🚨 CRITICAL RULES - VIOLATION = SYSTEM FAILURE:
1. ONLY use numbers that appear in the DATA CONTEXT below
2. NEVER invent index levels, stock prices, or percentage changes
3. If data says "Data not available" or "Data pending", say EXACTLY that
4. DO NOT make up headlines, RBI decisions, or company news
5. If uncertain about any fact, say "Data pending verification"

DATA AS OF: {current_time.strftime('%d %b %Y, %I:%M %p IST')}

=== VERIFIED DATA CONTEXT ===

📊 INDICES:
Source: Zerodha (sector cache)
Nifty 50 change: {state.get('sector_data', {}).get('nifty_change', 'Data pending')}%
(Note: Exact index level not available in current snapshot)

💰 FII/DII ACTIVITY:
Source: NSE/NSDL (nselib)
{fii_dii_text}

🌍 GLOBAL CUES:
Source: Yahoo Finance
{global_text}

💱 FOREX & COMMODITIES:
Source: Yahoo Finance
{forex_text}

📰 HEADLINES (from Perplexity search - may need verification):
{headlines_text[:800]}

=== END DATA CONTEXT ===

USER QUERY: {query}

=== OUTPUT FORMAT ===

📊 **Market Summary – {current_time.strftime('%d %b %Y')}**
_Data as of {current_time.strftime('%I:%M %p IST')} | Sources: NSE, Yahoo Finance_

📈 **Indices**
• [ONLY report Nifty change % if available, NOT invented index levels]
• If no data: "Index levels pending - check NSE website for live data"

💰 **FII/DII Activity**
• [Use EXACT numbers from data above]
• If pending: "FII/DII data published after market close by NSDL"

🌍 **Global Cues**
• [Summarize the global data above - DO NOT add new indices]

💱 **Currency & Commodities**
• [Use EXACT USD/INR and Brent values from data]

📰 **Key Developments**
• [Summarize headlines - mark uncertain items with ⚠️]

_Disclaimer: Data sourced from NSE, Yahoo Finance, Perplexity. Verify critical numbers before trading decisions._
"""
        
        elif intent == QueryIntent.MARKET_DATA:
            market_data = state.get("market_data", {})
            company = symbols[0] if symbols else "the market"
            
            # Get market status for timestamp header
            market_status = get_market_status()
            
            # Format market data for prompt
            market_text = ""
            for symbol, data in market_data.items():
                ltp = data.get("last_price", 0)
                open_price = data.get("open", 0)
                high = data.get("high", 0)
                low = data.get("low", 0)
                prev_close = data.get("close", 0)
                change = data.get("change", 0)
                change_pct = data.get("change_percent", 0)
                
                market_text += f"""
{symbol}:
- Current Price: ₹{ltp:,.2f}
- Change: {'+' if change >= 0 else ''}{change:,.2f} ({change_pct:+.2f}%)
- Open: ₹{open_price:,.2f}
- High: ₹{high:,.2f}
- Low: ₹{low:,.2f}
- Previous Close: ₹{prev_close:,.2f}
"""
            
            user_prompt = templates.market_data_prompt(company, market_text, query, market_status)
        
        elif intent == QueryIntent.MULTI:
            context_text = "\n\n".join([doc["text"] for doc in vector_context[:3]])
            news_text = news_data.get("answer", "")
            company = symbols[0] if symbols else "the company"
            user_prompt = templates.multi_source_prompt(company, context_text, news_text, query)
        
        else:
            # General query
            context_text = "\n\n".join([doc["text"] for doc in vector_context[:5]])
            user_prompt = f"Context:\n{context_text}\n\n Question: {query}"
    
    # Initialize LLM based on model (works for both blueprint and legacy)
    # For blueprints, use a good model (GPT-4 or Claude)
    if use_blueprints:
        model_name = "openai/gpt-4o-mini"  # Fast and good for structured output
        system_prompt = "You are a Bloomberg-style financial analyst. Follow the output structure exactly as specified."
    else:
        model_name = model_config["name"]
        system_prompt = templates.system_prompt()
    
    if "anthropic" in model_name:
        llm = ChatAnthropic(
            model=model_name.split("/")[-1],
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.3,
            max_tokens=1500 if use_blueprints else 1000  # More tokens for structured output
        )
    else:
        llm = ChatOpenAI(
            model=model_name,
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.3,
            max_tokens=1500 if use_blueprints else 1000
        )
    
    # Safety check: Ensure user_prompt is defined
    if user_prompt is None:
        # Fallback to simple query if prompt wasn't set
        user_prompt = f"Question: {query}"
        logger.warning(f"user_prompt was None, using fallback for query: {query}")
    
    # INJECT PORTFOLIO CONTEXT only for portfolio-specific queries
    portfolio_context = state.get("portfolio_context")
    if portfolio_context:
        logger.info(f"Portfolio context available. Intent: {intent}, QueryIntent.PORTFOLIO: {QueryIntent.PORTFOLIO}")
        
        # Check if query mentions portfolio even if intent is different
        query_lower = query.lower()
        portfolio_keywords = ["my portfolio", "my holdings", "my stocks", "my positions", 
                            "portfolio price", "portfolio value", "current price of my"]
        is_portfolio_query = any(keyword in query_lower for keyword in portfolio_keywords)
        
        if intent == QueryIntent.PORTFOLIO or is_portfolio_query:
            user_prompt = f"""=== USER'S ZERODHA PORTFOLIO ===
{portfolio_context}

===================================

{user_prompt}"""
            logger.info(f"✅ Injected portfolio context (intent: {intent}, has keywords: {is_portfolio_query})")
        else:
            logger.info(f"❌ NOT injecting portfolio context - intent mismatch: {intent} != {QueryIntent.PORTFOLIO}")
    
    # Generate response
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = await llm.ainvoke(messages)
        response_text = response.content
    except Exception as e:
        response_text = f"Error generating response: {str(e)}"
    
    # NEW: Add MongoDB document citations (annual reports, concalls, announcements)
    if use_blueprints and symbols:
        from src.blueprints.citations import get_citation_formatter
        
        mongo = get_enhanced_mongo_client()
        citation_formatter = get_citation_formatter()
        
        # Fetch documents for citation
        try:
            reports = await mongo.get_annual_reports(symbols[0])
            concalls = await mongo.get_concalls(symbols[0])
            announcements = await mongo.get_recent_announcements(symbols[0])
            
            # Format and add document citations
            doc_citations = citation_formatter.format_all_citations(
                reports=reports if reports and not isinstance(reports, Exception) else None,
                concalls=concalls if concalls and not isinstance(concalls, Exception) else None,
                announcements=announcements if announcements and not isinstance(announcements, Exception) else None
            )
            
            if doc_citations:
                response_text += doc_citations
                logger.info(f"Added document citations for {symbols[0]}")
        except Exception as e:
            logger.warning(f"Failed to add document citations: {str(e)}")
    
    # Collect citations
    citations = []
    for doc in vector_context[:5]:
        if doc.get("source"):
            citations.append(doc["source"])
    if news_data.get("citations"):
        citations.extend(news_data["citations"][:3])
    
    # P1: Add data completeness banner at the top of response
    dc = get_data_confidence()
    data_banner = dc.get_completeness_banner(state)
    
    # Prepend banner to response (only for non-greeting queries)
    if not state.get("is_greeting", False):
        response_text = data_banner + "\n\n" + response_text
    
    # Add citations to response
    if citations:
        response_text += templates.format_citations(citations)
    
    # Extract related questions as list for clickable buttons (no longer appending text to response)
    intent_str = intent.value.lower() if hasattr(intent, 'value') else str(intent).split('.')[-1].lower()
    related_questions_list = _get_related_questions_list(intent_str, symbols)
    
    # Calculate metrics
    latency_ms = (time.time() - start_time) * 1000
    cost_estimate = 0.001  # Default estimate (can be improved with actual cost tracking)
    
    reasoning = f"Generated response using {model_config['tier']} model ({model_name})"


    
    return {
        "response": response_text,
        "citations": citations,
        "related_questions": related_questions_list,
        "model_used": model_name,
        "latency_ms": latency_ms,
        "cost_estimate": cost_estimate,
        "reasoning_steps": [reasoning]
    }


def _get_related_questions_list(intent: str, symbols: list) -> list:
    """Get related questions as a list for clickable buttons."""
    if not symbols:
        symbols = []
    
    company = symbols[0] if symbols else "the company"
    
    if intent == "news" and symbols:
        return [
            f"What are {company}'s latest quarterly financial results?",
            f"How has {company} stock performed over the last year?",
            f"What recent acquisitions or partnerships has {company} made?",
            f"Compare {company} with its competitors",
            f"What's the current P/E ratio for {company}?"
        ]
    elif intent == "market_data" and symbols:
        return [
            f"What's the technical analysis for {company}?",
            f"Show me {company}'s historical price chart",
            f"What are analysts saying about {company}?",
            f"Compare {company} with its competitors",
            f"What's the latest news about {company}?"
        ]
    elif intent == "fundamental" and symbols:
        return [
            f"What is {company}'s P/E ratio compared to industry average?",
            f"Show me {company}'s revenue growth trend",
            f"What are {company}'s key financial ratios?",
            f"How does {company} compare to its peers?",
            f"What's {company}'s dividend history?"
        ]
    elif intent == "mutual_fund":
        return [
            "What are the best SIP funds for beginners?",
            "Compare index funds vs actively managed funds",
            "What's the difference between direct and regular mutual funds?",
            "Best ELSS funds for tax saving",
            "How to build a diversified mutual fund portfolio?"
        ]
    elif intent == "sector_performance":
        return [
            "Which sectors are outperforming Nifty 50?",
            "What's driving the metal sector's performance?",
            "Top performing stocks in IT sector today",
            "Should I invest in banking sector now?",
            "Compare auto vs pharma sector performance"
        ]
    else:
        return [
            "What are the top performing stocks in Nifty 50 today?",
            "Show me the latest market news",
            "What's the current market sentiment?",
            "Which sectors are performing well?",
            "What are the upcoming IPOs in India?"
        ]
