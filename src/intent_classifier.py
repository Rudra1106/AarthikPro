"""
Fast intent classification system for routing queries.
Uses rule-based patterns for MVP, can be upgraded to ML-based later.
"""
import re
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class QueryIntent(str, Enum):
    """Query intent categories for routing."""
    FUNDAMENTAL = "fundamental"  # Annual reports, financials, ratios
    TECHNICAL = "technical"  # Charts, indicators, price action
    NEWS = "news"  # Recent events, breaking news
    MARKET_DATA = "market_data"  # Live prices, volume, order book
    PORTFOLIO = "portfolio"  # User's holdings, P&L
    GENERAL = "general"  # General questions, greetings
    MULTI = "multi"  # Requires multiple data sources
    # NEW: MongoDB-specific intents for structured data
    FINANCIAL_METRICS = "financial_metrics"  # Revenue, profit, margins, EPS from financial_statements
    CORPORATE_ACTIONS = "corporate_actions"  # Dividends, splits, bonus, rights
    TREND_ANALYSIS = "trend_analysis"  # Multi-quarter trends, YoY growth
    # NEW: Sector performance analysis
    SECTOR_PERFORMANCE = "sector_performance"  # Sector rotation, leaders/laggards
    # NEW: Vertical/segment analysis
    VERTICAL_ANALYSIS = "vertical_analysis"  # Business vertical/segment performance
    # NEW: Mutual fund queries
    MUTUAL_FUND = "mutual_fund"  # SIP, fund recommendations, MF performance
    # NEW: Geopolitics queries
    GEO_NEWS = "geo_news"  # Geopolitical news and events
    SANCTIONS_STATUS = "sanctions_status"  # Sanctions information
    MARKET_IMPACT = "market_impact"  # Market reaction to geopolitics
    INDIA_IMPACT = "india_impact"  # India-specific geopolitical impact


@dataclass
class IntentClassification:
    """Result of intent classification."""
    primary_intent: QueryIntent
    confidence: float
    secondary_intents: List[QueryIntent]
    matched_patterns: List[str]


class IntentClassifier:
    """
    Fast, rule-based intent classifier using keyword patterns.
    
    Optimizations:
    - Compiled regex patterns for speed
    - Early exit on high-confidence matches
    - <10ms latency target
    """
    
    # Indian stock aliases - map common names to NSE symbols
    # Expanded to include top 100 stocks for better recognition
    INDIAN_STOCK_ALIASES = {
        # Large caps (Nifty 50)
        "TCS": ["TATA CONSULTANCY", "TATA CONSULTANCY SERVICES"],
        "INFY": ["INFOSYS"],
        "RELIANCE": ["RIL"],
        "HDFCBANK": ["HDFC BANK"],
        "ICICIBANK": ["ICICI BANK"],
        "SBIN": ["SBI", "STATE BANK"],
        "BHARTIARTL": ["AIRTEL", "BHARTI AIRTEL"],
        "ITC": ["ITC LIMITED"],
        "KOTAKBANK": ["KOTAK", "KOTAK MAHINDRA"],
        "LT": ["L&T", "LARSEN AND TOUBRO", "LARSEN"],
        "TATAMOTORS": ["TATA MOTORS"],
        "TMPV": ["TATA MOTORS PASSENGER", "TATA PASSENGER VEHICLES"],
        "WIPRO": ["WIPRO LIMITED"],
        "AXISBANK": ["AXIS BANK"],
        "MARUTI": ["MARUTI SUZUKI"],
        "HCLTECH": ["HCL TECH", "HCL TECHNOLOGIES"],
        "TITAN": ["TITAN COMPANY"],
        "NESTLEIND": ["NESTLE", "NESTLE INDIA"],
        "ULTRACEMCO": ["ULTRATECH", "ULTRATECH CEMENT"],
        "ADANIENT": ["ADANI ENTERPRISES"],
        "ONGC": ["OIL AND NATURAL GAS"],
        "NTPC": ["NTPC LIMITED"],
        "POWERGRID": ["POWER GRID"],
        "BSE": ["BSE LTD", "BSE LIMITED", "BOMBAY STOCK EXCHANGE"],
        "ASIANPAINT": ["ASIAN PAINTS"],
        "BAJFINANCE": ["BAJAJ FINANCE"],
        "BAJAJFINSV": ["BAJAJ FINSERV"],
        "SUNPHARMA": ["SUN PHARMA", "SUN PHARMACEUTICAL"],
        "DRREDDY": ["DR REDDY", "DR REDDYS"],
        "HINDALCO": ["HINDALCO INDUSTRIES"],
        "JSWSTEEL": ["JSW STEEL"],
        "TATASTEEL": ["TATA STEEL"],
        "COALINDIA": ["COAL INDIA"],
        "GRASIM": ["GRASIM INDUSTRIES"],
        "TECHM": ["TECH MAHINDRA"],
        "DIVISLAB": ["DIVIS LAB", "DIVIS LABORATORIES"],
        "CIPLA": ["CIPLA LIMITED"],
        "EICHERMOT": ["EICHER MOTORS"],
        "HEROMOTOCO": ["HERO MOTOCORP"],
        "BRITANNIA": ["BRITANNIA INDUSTRIES"],
        "HINDUNILVR": ["HUL", "HINDUSTAN UNILEVER"],
        "M&M": ["MAHINDRA", "MAHINDRA AND MAHINDRA"],
        "APOLLOHOSP": ["APOLLO HOSPITALS"],
        "INDUSINDBK": ["INDUSIND BANK"],
        "ADANIPORTS": ["ADANI PORTS"],
        "TATACONSUM": ["TATA CONSUMER"],
        "BPCL": ["BHARAT PETROLEUM"],
        "HDFCLIFE": ["HDFC LIFE"],
        "SBILIFE": ["SBI LIFE"],
        
        # Mid caps & Popular stocks
        "NATIONALUM": ["NALCO", "NATIONAL ALUMINIUM", "NATIONAL ALUMINIUM COMPANY"],
        "ZOMATO": ["ZOMATO LIMITED"],
        "PAYTM": ["ONE97", "ONE97 COMMUNICATIONS"],
        "NYKAA": ["FSN", "FSN ECOMMERCE"],
        "POLICYBAZAAR": ["PB FINTECH", "PBFINTECH"],
        "DMART": ["AVENUE SUPERMARTS"],
        "VEDL": ["VEDANTA", "VEDANTA LIMITED"],
        "ADANIGREEN": ["ADANI GREEN", "ADANI GREEN ENERGY"],
        "ADANIPOWER": ["ADANI POWER"],
        "ADANITRANS": ["ADANI TRANSMISSION"],
        "ADANIWILMAR": ["ADANI WILMAR"],
        "GODREJCP": ["GODREJ CONSUMER"],
        "GODREJPROP": ["GODREJ PROPERTIES"],
        "PIDILITIND": ["PIDILITE", "PIDILITE INDUSTRIES"],
        "BERGEPAINT": ["BERGER PAINTS"],
        "DABUR": ["DABUR INDIA"],
        "MARICO": ["MARICO LIMITED"],
        "COLPAL": ["COLGATE", "COLGATE PALMOLIVE"],
        "HAVELLS": ["HAVELLS INDIA"],
        "VOLTAS": ["VOLTAS LIMITED"],
        "SIEMENS": ["SIEMENS LIMITED"],
        "ABB": ["ABB INDIA"],
        "BOSCHLTD": ["BOSCH", "BOSCH LIMITED"],
        "MOTHERSON": ["MOTHERSON SUMI", "SAMVARDHANA MOTHERSON"],
        "BAJAJ-AUTO": ["BAJAJ AUTO"],
        "TVSMOTOR": ["TVS MOTOR"],
        "ESCORTS": ["ESCORTS KUBOTA"],
        "ASHOKLEY": ["ASHOK LEYLAND"],
        "TATACHEM": ["TATA CHEMICALS"],
        "TATAPOWER": ["TATA POWER"],
        "TATACOMM": ["TATA COMMUNICATIONS"],
        "TATAELXSI": ["TATA ELXSI"],
        "MPHASIS": ["MPHASIS LIMITED"],
        "LTTS": ["L&T TECHNOLOGY", "LT TECHNOLOGY SERVICES"],
        "LTIM": ["LTI MINDTREE", "LTIMINDTREE"],
        "COFORGE": ["COFORGE LIMITED"],
        "PERSISTENT": ["PERSISTENT SYSTEMS"],
        "BANKBARODA": ["BANK OF BARODA", "BOB"],
        "PNB": ["PUNJAB NATIONAL BANK"],
        "CANBK": ["CANARA BANK"],
        "UNIONBANK": ["UNION BANK"],
        "IDFCFIRSTB": ["IDFC FIRST BANK"],
        "BANDHANBNK": ["BANDHAN BANK"],
        "FEDERALBNK": ["FEDERAL BANK"],
        "AUBANK": ["AU SMALL FINANCE", "AU BANK"],
        "CHOLAFIN": ["CHOLAMANDALAM"],
        "SHRIRAMFIN": ["SHRIRAM FINANCE"],
        "MUTHOOTFIN": ["MUTHOOT FINANCE"],
        "BAJAJHLDNG": ["BAJAJ HOLDINGS"],
        "LICHSGFIN": ["LIC HOUSING FINANCE"],
        "PFC": ["POWER FINANCE CORPORATION"],
        "RECLTD": ["REC LIMITED", "RURAL ELECTRIFICATION"],
        "IRCTC": ["INDIAN RAILWAY CATERING"],
        "IRFC": ["INDIAN RAILWAY FINANCE"],
    }
    
    def __init__(self):
        # Fundamental analysis patterns
        self.fundamental_patterns = [
            r'\b(revenue|profit|earnings|ebitda|margin|debt|equity)\b',
            r'\b(balance sheet|cash flow|income statement|financials?)\b',
            r'\b(pe ratio|pb ratio|roe|roce|dividend|eps)\b',
            r'\b(annual report|quarterly result|concall|earnings call)\b',
            r'\b(valuation|fundamental|intrinsic value)\b',
            r'\b(sector comparison|peer analysis|industry)\b',
        ]
        
        # Technical analysis patterns
        self.technical_patterns = [
            r'\b(rsi|macd|bollinger|moving average|sma|ema)\b',
            r'\b(support|resistance|breakout|trend|chart)\b',
            r'\b(technical analysis|price action|volume)\b',
            r'\b(candlestick|pattern|fibonacci)\b',
            r'\b(overbought|oversold|momentum)\b',
        ]
        
        # News and events patterns
        self.news_patterns = [
            r'\b(news|latest|recent|today|yesterday)\b',
            r'\b(announcement|event|breaking|update)\b',
            r'\b(merger|acquisition|policy|regulation)\b',
            r'\b(what happened|why (is|did)|reason for)\b',
            r'\b(performance|how is|how\'s|doing)\b',
            r'\b(up or down|gain|loss|change)\b.*\b(today|this week|this month)\b',
        ]
        
        # Market data patterns (includes OHLC)
        self.market_data_patterns = [
            r'\b(current price|live price|stock price|market price)\b',
            r'\b(price of|price for|what.*price)\b',  # NEW: Simple price queries
            r'\b([A-Z]{2,10})\s+(price|quote|ltp)\b',  # NEW: "TCS price", "INFY quote"
            r'\b(volume|order book|bid|ask|spread)\b',
            r'\b(high|low|open|close)\b.*\b(today|intraday)\b',
            r'\btoday\'s (high|low|range|open|close)\b',
            r'\b(day\'s|daily) (high|low|range)\b',
            r'\b(market cap|52 week (high|low))\b',
        ]
        
        # Portfolio patterns - USER'S PERSONAL PORTFOLIO
        self.portfolio_patterns = [
            r'\b(my portfolio|my holdings|my stocks|my investments|my shares)\b',
            r'\b(what (do i|stocks do i|shares do i)|which stocks do i) (own|have|hold)\b',
            r'\b(show me|list|display|view) (my|all my)? (portfolio|holdings|stocks|investments)\b',
            r'\b(how (is|are)) my (portfolio|holdings|investments|stocks) (doing|performing)\b',
            r'\b(my|portfolio) (profit|loss|p&l|returns?|performance|gains?)\b',
            r'\b(top|best|worst) (gainer|loser|performer)s? in my portfolio\b',
            r'\b(should i (buy|sell|hold))\b.*\b(my portfolio|my holdings)\b',
            r'\b(portfolio|holdings) (analysis|review|summary|breakdown)\b',
            r'\b(total|overall) (investment|portfolio value|returns?)\b',
            r'\b(buying power|available funds|margin|cash)\b',
            r'\b(positions|trades|orders)\b.*\b(my|current|open)\b',
        ]
        
        # General patterns
        self.general_patterns = [
            r'\b(hello|hi|hey|thanks|thank you)\b',
            r'\b(what (is|are)|who (is|are)|how (does|do))\b',
            r'\b(explain|tell me about|help)\b',
        ]
        
        # NEW: Financial metrics patterns (specific quarterly/annual metrics)
        self.financial_metrics_patterns = [
            r'\b(what (was|is)|show me|get)\b.*\b(revenue|profit|earnings|margin|eps)\b',
            r'\b(q[1-4]|quarter|quarterly|annual)\b.*\b(revenue|profit|earnings|result)\b',
            r'\b(revenue|profit|earnings|margin|eps)\b.*\b(in|for|of)\b.*\b(q[1-4]|quarter|fy\d{4}|sep|jun|mar|dec)\b',
            r'\b(latest|recent|last)\b.*\b(quarter|quarterly|result|earnings)\b',
            r'\b(operating margin|net margin|profit margin)\b',
            r'\b(total (revenue|income|expenses))\b',
        ]
        
        # NEW: Corporate actions patterns (dividends, splits, bonus, rights)
        self.corporate_actions_patterns = [
            r'\b(dividend|dividends)\b',
            r'\b(when (is|was)|next|upcoming|recent)\b.*\b(dividend|payout)\b',
            r'\b(dividend (history|yield|payout|announcement))\b',
            r'\b(stock split|bonus (share|issue)|rights issue)\b',
            r'\b(ex-date|record date|payment date)\b',
            r'\b(declared|announced)\b.*\b(dividend|bonus|split)\b',
        ]
        
        # NEW: Trend analysis patterns (multi-quarter comparisons, growth)
        self.trend_analysis_patterns = [
            r'\b(trend|growth|trajectory)\b',
            r'\b(over (time|quarters|years)|last \d+ (quarters|years))\b',
            r'\b(yoy|year over year|qoq|quarter over quarter)\b.*\b(growth|change)\b',
            r'\b(compare|comparison)\b.*\b(quarters|years|periods)\b',
            r'\b(show me|display)\b.*\b(trend|growth|history)\b',
            r'\b(revenue|profit|margin)\b.*\b(trend|over time|growth rate)\b',
            r'\b(increasing|decreasing|improving|declining)\b.*\b(over|across)\b',
        ]
        
        # NEW: Sector performance patterns (sector rotation, leaders/laggards)
        self.sector_performance_patterns = [
            r'\b(which|what) sectors? (are|is) (performing|doing|growing) (well|good|bad|poorly)?\b',
            r'\bsector (performance|rotation|leaders?|laggards?)\b',
            r'\b(top|best|worst|leading|lagging) (performing )?sectors?\b',
            r'\b(outperforming|underperforming) sectors?\b',
            r'\bsectors? (to|you should) (buy|watch|avoid)\b',
            r'\b(sectoral|sector) (breakdown|analysis|trends?)\b',
            # NEW: Time-sensitive sector patterns
            r'\b(which|what) sector.*(growing|growth|this year|in 2025|currently|now)\b',
            r'\bsector.*(this year|this quarter|this month|best|top|growing)\b',
            r'\b(growing|best|top|leading) sectors?\b',
            r'\b(performing|growing) sectors? (currently|now|this)\b',
        ]
        
        # NEW: Vertical/segment analysis patterns
        self.vertical_analysis_patterns = [
            r'\b(which|what) (vertical|segment|business) (is|are) (driving|contributing)',
            r'\b(vertical|segment)-wise (performance|revenue|growth|margin)',
            r'\b(bfsi|retail|manufacturing|ev|telecom|passenger|commercial) (vertical|segment|demand)',
            r'\b(vertical|segment|business) (breakdown|analysis|performance)',
            r'\b(strongest|weakest) (vertical|segment|business)',
            r'\b(margin pressure|demand slowdown) in (vertical|segment)',
            r'\bshow me (vertical|segment) (performance|breakdown)',
        ]
        
        # NEW: Mutual fund patterns
        self.mutual_fund_patterns = [
            r'\b(mutual fund|mf|sip|elss|nfo)\b',
            r'\b(best|top|good|recommend)\b.*\b(mutual )?funds?\b',
            r'\bfund (recommendations?|suggestions?|options?)\b',
            r'\b(debt|equity|hybrid|index|liquid|flexicap|largecap|midcap|smallcap) funds?\b',
            r'\bmonthly (sip|investment|investing)\b',
            r'\bfund (performance|returns?|cagr|nav)\b',
            r'\b(which|what) funds? (should|can|to) (buy|invest|start)\b',
            r'\b(sbi|hdfc|icici|axis|nippon|kotak|mirae|dsp)\b.*\bfund\b',
            r'\bmutual fund (portfolio|allocation)\b',
            r'\b(tax saving|elss) funds?\b',
        ]
        
        # NEW: Geopolitics patterns
        self.geo_news_patterns = [
            r'\b(geopolitic|geopolitical)\b',
            r'\b(sanctions?|sanctioned)\b',
            r'\b(trade war|tariff|embargo)\b',
            r'\b(international (relations|conflict|tension))\b',
            r'\b(us (policy|policies)|foreign policy)\b',
            r'\b(global (conflict|tension|crisis))\b',
        ]
        
        self.sanctions_status_patterns = [
            r'\b(which|what) (countries?|nations?) (are|is) (under|facing) sanctions?\b',
            r'\b(active|current|latest) sanctions?\b',
            r'\b(sanctions? (on|against|imposed))\b',
            r'\b(trump(-era)?) sanctions?\b',
            r'\b(us sanctions?|american sanctions?)\b',
            r'\b(sanctions? (status|package|regime))\b',
            r'\b(sanctions? (lifted|eased|rolled back|removed))\b',
        ]
        
        self.market_impact_patterns = [
            r'\b(market (reaction|response|impact))\b.*\b(geopolitic|sanctions?|tension)\b',
            r'\b(how (do|did|have)) (markets?|stocks?) (react|respond)\b.*\b(geopolitic|sanctions?|tension)\b',
            r'\b(geopolitic|sanctions?|tension)\b.*\b(affect|impact|influence) (markets?|stocks?|prices?)\b',
            r'\b(volatility|uncertainty)\b.*\b(geopolitic|sanctions?|conflict)\b',
            r'\b(oil price|commodity price|currency)\b.*\b(sanctions?|geopolitic|conflict)\b',
        ]
        
        self.india_impact_patterns = [
            r'\b(india|indian)\b.*\b(sanctions?|geopolitic|trade war)\b',
            r'\b(sanctions?|geopolitic|trade war)\b.*\b(india|indian)\b',
            r'\b(how (do|does|did)) sanctions?\b.*\b(affect|impact) india\b',
            r'\b(india|indian) (exports?|imports?|trade)\b.*\b(sanctions?|geopolitic)\b',
            r'\b(fii|foreign (investment|flows))\b.*\b(geopolitic|sanctions?|uncertainty)\b',
            r'\b(indian (markets?|economy|sectors?))\b.*\b(geopolitic|sanctions?|tension)\b',
        ]
        
        # Compile patterns for performance
        self.compiled_patterns = {
            QueryIntent.FUNDAMENTAL: [re.compile(p, re.IGNORECASE) for p in self.fundamental_patterns],
            QueryIntent.TECHNICAL: [re.compile(p, re.IGNORECASE) for p in self.technical_patterns],
            QueryIntent.NEWS: [re.compile(p, re.IGNORECASE) for p in self.news_patterns],
            QueryIntent.MARKET_DATA: [re.compile(p, re.IGNORECASE) for p in self.market_data_patterns],
            QueryIntent.PORTFOLIO: [re.compile(p, re.IGNORECASE) for p in self.portfolio_patterns],
            QueryIntent.GENERAL: [re.compile(p, re.IGNORECASE) for p in self.general_patterns],
            # NEW: MongoDB-specific intents
            QueryIntent.FINANCIAL_METRICS: [re.compile(p, re.IGNORECASE) for p in self.financial_metrics_patterns],
            QueryIntent.CORPORATE_ACTIONS: [re.compile(p, re.IGNORECASE) for p in self.corporate_actions_patterns],
            QueryIntent.TREND_ANALYSIS: [re.compile(p, re.IGNORECASE) for p in self.trend_analysis_patterns],
            # NEW: Sector performance
            QueryIntent.SECTOR_PERFORMANCE: [re.compile(p, re.IGNORECASE) for p in self.sector_performance_patterns],
            QueryIntent.MUTUAL_FUND: [re.compile(p, re.IGNORECASE) for p in self.mutual_fund_patterns],
            # NEW: Vertical analysis
            QueryIntent.VERTICAL_ANALYSIS: [re.compile(p, re.IGNORECASE) for p in self.vertical_analysis_patterns],
            # NEW: Geopolitics intents
            QueryIntent.GEO_NEWS: [re.compile(p, re.IGNORECASE) for p in self.geo_news_patterns],
            QueryIntent.SANCTIONS_STATUS: [re.compile(p, re.IGNORECASE) for p in self.sanctions_status_patterns],
            QueryIntent.MARKET_IMPACT: [re.compile(p, re.IGNORECASE) for p in self.market_impact_patterns],
            QueryIntent.INDIA_IMPACT: [re.compile(p, re.IGNORECASE) for p in self.india_impact_patterns],
        }
    
    def normalize_stock_symbol(self, symbol: str) -> str:
        """Normalize stock symbol to NSE format."""
        symbol_upper = symbol.upper().strip()
        
        # Check if it's already a known symbol
        if symbol_upper in self.INDIAN_STOCK_ALIASES:
            return symbol_upper
        
        # Check aliases
        for nse_symbol, aliases in self.INDIAN_STOCK_ALIASES.items():
            if symbol_upper in [a.upper() for a in aliases]:
                return nse_symbol
        
        return symbol_upper
    
    def classify(self, query: str) -> IntentClassification:
        """
        Classify query intent using pattern matching.
        
        Args:
            query: User's query string
            
        Returns:
            IntentClassification with primary intent and confidence
        """
        query_lower = query.lower()
        
        # Score each intent
        intent_scores: Dict[QueryIntent, float] = {}
        matched_patterns: Dict[QueryIntent, List[str]] = {}
        
        for intent, patterns in self.compiled_patterns.items():
            matches = []
            for pattern in patterns:
                if pattern.search(query_lower):
                    matches.append(pattern.pattern)
            
            if matches:
                matched_patterns[intent] = matches
                # Score based on number of matches and pattern specificity
                intent_scores[intent] = len(matches) / len(patterns)
        
        # No matches - check if stock symbols detected
        if not intent_scores:
            symbols = self.extract_stock_symbols(query)
            if symbols:
                # Stock query without specific intent -> use MARKET_DATA for price queries
                # This ensures simple queries like "TCS price" work correctly
                return IntentClassification(
                    primary_intent=QueryIntent.MARKET_DATA,
                    confidence=0.7,
                    secondary_intents=[],
                    matched_patterns=["stock_symbol_detected"]
                )
            return IntentClassification(
                primary_intent=QueryIntent.GENERAL,
                confidence=0.5,
                secondary_intents=[],
                matched_patterns=[]
            )
        
        # Sort by score
        sorted_intents = sorted(intent_scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent, primary_score = sorted_intents[0]
        
        # Extract stock symbols for additional logic
        symbols = self.extract_stock_symbols(query)
        
        # Override GENERAL intent if stock symbols detected
        # This ensures stock queries get routed to Perplexity for real-time info
        if primary_intent == QueryIntent.GENERAL and symbols:
            return IntentClassification(
                primary_intent=QueryIntent.NEWS,
                confidence=0.7,
                secondary_intents=[QueryIntent.GENERAL],
                matched_patterns=["stock_symbol_detected"]
            )
        
        # NEW: Boost MongoDB-specific intents when matched
        # These intents should take priority over generic NEWS/MULTI
        mongodb_intents = [QueryIntent.FINANCIAL_METRICS, QueryIntent.CORPORATE_ACTIONS, QueryIntent.TREND_ANALYSIS, QueryIntent.SECTOR_PERFORMANCE, QueryIntent.VERTICAL_ANALYSIS]
        
        # If any MongoDB intent matched, boost it
        for mongodb_intent in mongodb_intents:
            if mongodb_intent in intent_scores and intent_scores[mongodb_intent] > 0:
                # Check if it's the top scorer or close to it
                if mongodb_intent == primary_intent or intent_scores[mongodb_intent] >= primary_score * 0.7:
                    return IntentClassification(
                        primary_intent=mongodb_intent,
                        confidence=min(intent_scores[mongodb_intent] * 2.0, 0.95),  # Boost confidence
                        secondary_intents=[primary_intent] if mongodb_intent != primary_intent else [],
                        matched_patterns=matched_patterns.get(mongodb_intent, [])
                    )
        
        # Boost MARKET_DATA intent for price-related queries with symbols
        # This ensures Zerodha is used for live prices
        if symbols and primary_intent == QueryIntent.MARKET_DATA:
            # Check if query has price-related keywords
            price_keywords = ['price', 'current', 'trading at', 'worth', 'value', 'quote']
            has_price_keyword = any(kw in query.lower() for kw in price_keywords)
            
            if has_price_keyword:
                return IntentClassification(
                    primary_intent=QueryIntent.MARKET_DATA,
                    confidence=0.85,  # High confidence for price queries
                    secondary_intents=[],
                    matched_patterns=matched_patterns.get(QueryIntent.MARKET_DATA, [])
                )
        
        # NEW: Boost MARKET_DATA over NEWS for price queries
        # Handles cases like "HDFC Bank latest price" where "latest" triggers NEWS
        if symbols and QueryIntent.MARKET_DATA in intent_scores:
            price_keywords = ['price', 'quote', 'ltp', 'current', 'latest', 'trading at', 'worth', 'value']
            has_price_keyword = any(kw in query.lower() for kw in price_keywords)
            
            if has_price_keyword and primary_intent == QueryIntent.NEWS:
                # Override NEWS with MARKET_DATA for price queries
                return IntentClassification(
                    primary_intent=QueryIntent.MARKET_DATA,
                    confidence=0.85,
                    secondary_intents=[QueryIntent.NEWS],
                    matched_patterns=matched_patterns.get(QueryIntent.MARKET_DATA, [])
                )
        
        # Boost MARKET_DATA for OHLC queries (high/low/open/close) with symbols
        if symbols:
            ohlc_keywords = ['high', 'low', 'open', 'close', 'range']
            has_ohlc = any(kw in query.lower() for kw in ohlc_keywords)
            
            if has_ohlc and 'today' in query.lower():
                return IntentClassification(
                    primary_intent=QueryIntent.MARKET_DATA,
                    confidence=0.85,
                    secondary_intents=[],
                    matched_patterns=["ohlc_query_detected"]
                )
        
        # Check if multi-intent query (multiple high scores)
        high_scoring_intents = [intent for intent, score in sorted_intents if score > 0.3]
        if len(high_scoring_intents) > 1:
            return IntentClassification(
                primary_intent=QueryIntent.MULTI,
                confidence=0.8,
                secondary_intents=high_scoring_intents,
                matched_patterns=sum(matched_patterns.values(), [])
            )
        
        # Single intent
        secondary_intents = [intent for intent, _ in sorted_intents[1:] if intent_scores.get(intent, 0) > 0.2]
        
        return IntentClassification(
            primary_intent=primary_intent,
            confidence=min(primary_score * 1.5, 1.0),  # Boost confidence
            secondary_intents=secondary_intents,
            matched_patterns=matched_patterns.get(primary_intent, [])
        )
    
    def extract_stock_symbols(self, query: str) -> List[str]:
        """
        Extract and normalize stock symbols from query.
        
        Hybrid approach for optimal latency:
        1. Symbol mapper (fast, free) - indices and common aliases
        2. Hardcoded aliases (fast, free) - top 100 stocks
        3. Regex pattern (fast, free) - uppercase symbols
        4. LLM fallback (slower, cheap) - comprehensive coverage
        
        Now supports:
        - Index names: "nifty 50", "sensex", "bank nifty"
        - Company names: "Zomato Limited", "TCS", "NALCO"
        - Stock aliases: "reliance", "hdfc bank", "sbi"
        """
        symbols = []
        
        # PRIORITY 1: Check symbol mapper for indices and aliases (FAST)
        try:
            from src.intelligence.symbol_mapper import get_symbol_mapper
            mapper = get_symbol_mapper()
            mapped_symbols = mapper.extract_from_query(query)  # Now returns List[str]
            if mapped_symbols:
                symbols.extend(mapped_symbols)  # Add all mapped symbols
                return symbols  # Return immediately if mapped
        except ImportError:
            pass
        
        # PRIORITY 2: Check hardcoded aliases (FAST)
        query_upper = query.upper()
        for nse_symbol, aliases in self.INDIAN_STOCK_ALIASES.items():
            # Check if symbol itself is in query
            if nse_symbol in query_upper:
                if nse_symbol not in symbols:
                    symbols.append(nse_symbol)
            # Check aliases
            for alias in aliases:
                if alias.upper() in query_upper:
                    if nse_symbol not in symbols:
                        symbols.append(nse_symbol)
        
        if symbols:
            return symbols  # Found via aliases, return immediately
        
        # PRIORITY 3: Pattern for Indian stock symbols (FAST)
        pattern = r'\b([A-Z]{2,10})\b'
        matches = re.findall(pattern, query)
        
        # Filter out common words AND mutual fund terms
        common_words = {
            'PE', 'PB', 'ROE', 'ROCE', 'EPS', 'RSI', 'MACD', 'SMA', 'EMA', 'YOY', 'QOQ', 'NSE', 'BSE',
            'SIP', 'MF', 'ETF', 'NFO', 'ELSS', 'NAV', 'AUM', 'CAGR', 'SWP', 'STP',
            'IPO', 'FII', 'DII', 'GDP', 'CPI', 'WPI', 'RBI', 'SEBI'
        }
        raw_symbols = [m for m in matches if m not in common_words]
        
        if raw_symbols:
            # Normalize symbols using aliases
            normalized_symbols = [self.normalize_stock_symbol(s) for s in raw_symbols]
            
            # Remove duplicates
            seen = set()
            for symbol in normalized_symbols:
                if symbol not in seen:
                    seen.add(symbol)
                    symbols.append(symbol)
            
            if symbols:
                return symbols  # Found via regex, return immediately
        
        # PRIORITY 4: LLM fallback for unknown stocks (SLOWER but comprehensive)
        # Only use if query seems to be about stocks but no symbols found yet
        stock_keywords = ['price', 'stock', 'share', 'company', 'buy', 'sell', 'invest', 'trading']
        has_stock_context = any(kw in query.lower() for kw in stock_keywords)
        
        if has_stock_context:
            try:
                from src.intelligence.llm_symbol_extractor import get_llm_symbol_extractor
                import asyncio
                
                extractor = get_llm_symbol_extractor()
                
                # Run async extraction
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If already in async context, create task
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, extractor.extract_symbols(query))
                        llm_symbols = future.result(timeout=3)  # 3s timeout
                else:
                    llm_symbols = asyncio.run(extractor.extract_symbols(query))
                
                if llm_symbols:
                    logger.info(f"✅ LLM fallback found symbols: {llm_symbols}")
                    return llm_symbols
            except Exception as e:
                logger.warning(f"LLM symbol extraction failed: {e}")
        
        return symbols  # Return empty if nothing found


# Singleton instance
_classifier_instance: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    """Get singleton intent classifier instance."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier()
    return _classifier_instance
