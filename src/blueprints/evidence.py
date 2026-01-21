"""
Evidence Object Builder.

Transforms raw data into structured evidence objects that the LLM uses for reasoning.
This ensures traceable, debuggable, and consistent outputs.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class PriceAction(Enum):
    """Price action classification."""
    STRONG_UP = "strong_up"
    MODERATE_UP = "moderate_up"
    NEUTRAL = "neutral"
    MODERATE_DOWN = "moderate_down"
    STRONG_DOWN = "strong_down"


class Breadth(Enum):
    """Market breadth classification."""
    BROAD = "broad"
    MODERATE = "moderate"
    NARROW = "narrow"


class FundamentalTrend(Enum):
    """Fundamental trend classification."""
    CYCLICAL = "cyclical"
    DEFENSIVE = "defensive"
    GROWTH = "growth"
    VALUE = "value"


class DataConfidence(Enum):
    """Data confidence level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class EvidenceObject:
    """
    Structured evidence for LLM reasoning.
    
    The LLM never sees raw data - only this processed evidence.
    """
    # Price & Technical
    price_action: str
    relative_strength: str
    momentum: str
    
    # Market Structure
    breadth: str
    participation: str
    
    # Fundamentals
    fundamental_trend: str
    
    # Optional fields (must come after required fields)
    market_price_data: Optional[Dict[str, Any]] = None  # Actual price data from Zerodha
    
    # NEW: Pre-formatted price data for LLM
    formatted_price: Optional[str] = None  # e.g., "₹4,250.50 (+1.2%, +₹50.35)"
    support_levels: Optional[List[float]] = None  # Calculated from OHLC
    resistance_levels: Optional[List[float]] = None  # Calculated from OHLC
    technical_indicators: Optional[Dict[str, Any]] = None  # RSI, MACD, etc.
    
    earnings_quality: Optional[str] = None
    valuation_level: Optional[str] = None
    
    # Macro & Drivers
    macro_drivers: List[str] = None
    sector_drivers: List[str] = None
    
    # Risk
    risk_flags: List[str] = None
    volatility_regime: Optional[str] = None
    
    # NEW: Document & Corporate Action Data
    recent_announcements: List[str] = None
    corporate_actions_summary: Optional[str] = None
    annual_reports_available: bool = False
    concalls_available: bool = False
    
    # Metadata
    data_confidence: str = "medium"
    data_sources: List[str] = None
    
    def __post_init__(self):
        """Initialize default lists."""
        if self.macro_drivers is None:
            self.macro_drivers = []
        if self.sector_drivers is None:
            self.sector_drivers = []
        if self.risk_flags is None:
            self.risk_flags = []
        if self.data_sources is None:
            self.data_sources = []
        if self.recent_announcements is None:
            self.recent_announcements = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "price_action": self.price_action,
            "market_price_data": self.market_price_data,
            "formatted_price": self.formatted_price,
            "support_levels": self.support_levels,
            "resistance_levels": self.resistance_levels,
            "technical_indicators": self.technical_indicators,
            "relative_strength": self.relative_strength,
            "momentum": self.momentum,
            "breadth": self.breadth,
            "participation": self.participation,
            "fundamental_trend": self.fundamental_trend,
            "earnings_quality": self.earnings_quality,
            "valuation_level": self.valuation_level,
            "macro_drivers": self.macro_drivers,
            "sector_drivers": self.sector_drivers,
            "risk_flags": self.risk_flags,
            "volatility_regime": self.volatility_regime,
            "recent_announcements": self.recent_announcements,
            "corporate_actions_summary": self.corporate_actions_summary,
            "annual_reports_available": self.annual_reports_available,
            "concalls_available": self.concalls_available,
            "data_confidence": self.data_confidence,
            "data_sources": self.data_sources,
        }


def get_impact_statement(contribution: float) -> str:
    """
    Convert contribution decimal to human-readable impact statement.
    
    Args:
        contribution: Stock's contribution to index (e.g., 0.082, -0.154)
        
    Returns:
        Impact statement (e.g., "Major positive contributor")
    """
    abs_contrib = abs(contribution)
    direction = "positive" if contribution > 0 else "negative"
    
    if abs_contrib > 0.10:
        return f"Major {direction} contributor"
    elif abs_contrib > 0.05:
        return f"Moderate {direction} contributor"
    else:
        return f"Minor {direction} contributor"


class EvidenceBuilder:
    """
    Builds evidence objects from raw data.
    
    Transforms market data, fundamentals, and news into
    structured evidence for LLM reasoning.
    """
    
    async def build_stock_evidence(
        self,
        symbol: str,
        market_data: Optional[Dict] = None,
        structured_data: Optional[Dict] = None,
        news_data: Optional[Dict] = None,
        sector_data: Optional[Dict] = None,
    ) -> EvidenceObject:
        """
        Build evidence object for a stock using enhanced MongoDB data.
        
        Args:
            symbol: Stock symbol
            market_data: Live market data from Zerodha
            structured_data: Financial data from MongoDB (legacy)
            news_data: News from Perplexity
            sector_data: Sector performance data
        
        Returns:
            EvidenceObject with comprehensive processed insights
        """
        # NEW: Fetch comprehensive data from enhanced MongoDB client
        from src.data.enhanced_mongo_client import get_enhanced_mongo_client
        
        mongo = get_enhanced_mongo_client()
        
        # Fetch all MongoDB data in parallel
        import asyncio
        company_task = mongo.get_company_info(symbol)
        quarterly_task = mongo.get_quarterly_results(symbol)
        stats_task = mongo.get_profit_loss_stats(symbol)
        ratios_task = mongo.get_ratios(symbol)
        shareholding_task = mongo.get_shareholding_pattern(symbol)
        announcements_task = mongo.get_recent_announcements(symbol, limit=3)
        dividends_task = mongo.get_dividends(symbol)
        reports_task = mongo.get_annual_reports(symbol)
        concalls_task = mongo.get_concalls(symbol)
        
        (company, quarterly, stats, ratios, shareholding, 
         announcements, dividends, reports, concalls) = await asyncio.gather(
            company_task, quarterly_task, stats_task, ratios_task,
            shareholding_task, announcements_task, dividends_task,
            reports_task, concalls_task,
            return_exceptions=True
        )
        
        # Extract price action
        price_action = self._classify_price_action(market_data)
        relative_strength = self._calculate_relative_strength(market_data, sector_data)
        momentum = self._assess_momentum(market_data)
        
        # NEW: Format price data for direct use in prompts
        formatted_price = self._format_price_display(market_data)
        support_levels = self._calculate_support_levels(market_data)
        resistance_levels = self._calculate_resistance_levels(market_data)
        technical_indicators = self._extract_technical_indicators(market_data)
        
        # Extract fundamental trend using actual data
        fundamental_trend = self._classify_fundamental_trend_enhanced(stats, quarterly)
        earnings_quality = self._assess_earnings_quality_enhanced(quarterly, ratios)
        valuation_level = self._assess_valuation_enhanced(company, quarterly)
        
        # Extract drivers
        macro_drivers = self._extract_macro_drivers(news_data)
        sector_drivers = self._extract_sector_drivers(sector_data)
        
        # Extract risks using announcements and shareholding
        risk_flags = self._identify_risk_flags_enhanced(
            shareholding, announcements, ratios
        )
        volatility_regime = self._assess_volatility(market_data)
        
        # NEW: Process announcements
        recent_announcements = []
        if announcements and not isinstance(announcements, Exception):
            for ann in announcements[:3]:
                title = ann.get('title', '')[:80]  # Truncate long titles
                recent_announcements.append(title)
        
        # NEW: Summarize corporate actions
        corporate_actions_summary = None
        if dividends and not isinstance(dividends, Exception):
            div_data = dividends.get('data', [])
            if div_data:
                corporate_actions_summary = f"{len(div_data)} dividend payments on record"
        
        # NEW: Check document availability
        annual_reports_available = bool(reports and not isinstance(reports, Exception) and len(reports) > 0)
        concalls_available = bool(concalls and not isinstance(concalls, Exception) and len(concalls) > 0)
        
        # Assess data confidence
        data_confidence = self._calculate_confidence_enhanced(
            market_data, quarterly, stats, announcements
        )
        
        # Track data sources
        data_sources = []
        if market_data:
            data_sources.append("zerodha")
        if quarterly and not isinstance(quarterly, Exception):
            data_sources.append("mongodb_financials")
        if announcements and not isinstance(announcements, Exception):
            data_sources.append("mongodb_documents")
        if news_data:
            data_sources.append("perplexity")
        
        return EvidenceObject(
            price_action=price_action,
            market_price_data=market_data,  # Pass actual price data
            formatted_price=formatted_price,  # NEW: Pre-formatted price string
            support_levels=support_levels,  # NEW: Support levels
            resistance_levels=resistance_levels,  # NEW: Resistance levels
            technical_indicators=technical_indicators,  # NEW: Technical indicators
            relative_strength=relative_strength,
            momentum=momentum,
            breadth="n/a",  # Stock-level doesn't have breadth
            participation="n/a",
            fundamental_trend=fundamental_trend,
            earnings_quality=earnings_quality,
            valuation_level=valuation_level,
            macro_drivers=macro_drivers,
            sector_drivers=sector_drivers,
            risk_flags=risk_flags,
            volatility_regime=volatility_regime,
            recent_announcements=recent_announcements,
            corporate_actions_summary=corporate_actions_summary,
            annual_reports_available=annual_reports_available,
            concalls_available=concalls_available,
            data_confidence=data_confidence,
            data_sources=data_sources,
        )
    
    def build_sector_evidence(
        self,
        sector: str,
        sector_data: Optional[Dict] = None,
        constituent_data: Optional[List[Dict]] = None,
        news_data: Optional[Dict] = None,
    ) -> EvidenceObject:
        """
        Build evidence object for a sector.
        
        Args:
            sector: Sector name
            sector_data: Sector performance data
            constituent_data: Individual stock data
            news_data: Sector news
        
        Returns:
            EvidenceObject with sector insights
        """
        # Extract sector performance
        price_action = self._classify_sector_performance(sector_data)
        relative_strength = self._calculate_sector_relative_strength(sector_data)
        momentum = self._assess_sector_momentum(sector_data)
        
        # Extract breadth
        breadth = self._calculate_breadth(constituent_data)
        participation = self._assess_participation(constituent_data)
        
        # Extract drivers
        macro_drivers = self._extract_macro_drivers(news_data)
        sector_drivers = self._extract_sector_specific_drivers(sector, news_data)
        
        # Extract risks
        risk_flags = self._identify_sector_risks(sector, news_data)
        
        # Assess confidence
        data_confidence = self._calculate_confidence(
            sector_data, constituent_data, news_data
        )
        
        data_sources = []
        if sector_data:
            data_sources.append("sector_indices")
        if constituent_data:
            data_sources.append("constituents")
        if news_data:
            data_sources.append("perplexity")
        
        return EvidenceObject(
            price_action=price_action,
            relative_strength=relative_strength,
            momentum=momentum,
            breadth=breadth,
            participation=participation,
            fundamental_trend="sector",
            macro_drivers=macro_drivers,
            sector_drivers=sector_drivers,
            risk_flags=risk_flags,
            data_confidence=data_confidence,
            data_sources=data_sources,
        )
    
    # ========================================================================
    # Private Helper Methods
    # ========================================================================
    
    def _classify_price_action(self, market_data: Optional[Dict]) -> str:
        """Classify price action from market data."""
        if not market_data:
            return "unknown"
        
        change_pct = market_data.get("change_percent", 0)
        
        if change_pct > 3:
            return "strong_up"
        elif change_pct > 1:
            return "moderate_up"
        elif change_pct < -3:
            return "strong_down"
        elif change_pct < -1:
            return "moderate_down"
        else:
            return "neutral"
    
    def _calculate_relative_strength(
        self, market_data: Optional[Dict], sector_data: Optional[Dict]
    ) -> str:
        """Calculate relative strength vs benchmark."""
        if not market_data:
            return "unknown"
        
        change_pct = market_data.get("change_percent", 0)
        
        # TODO: Compare vs Nifty/sector benchmark
        # For now, use absolute performance
        if change_pct > 0:
            return f"+{change_pct:.1f}% (outperforming)"
        else:
            return f"{change_pct:.1f}% (underperforming)"
    
    def _assess_momentum(self, market_data: Optional[Dict]) -> str:
        """Assess price momentum."""
        if not market_data:
            return "unknown"
        
        # TODO: Use technical indicators (RSI, MACD)
        # For now, use price change as proxy
        change_pct = abs(market_data.get("change_percent", 0))
        
        if change_pct > 2:
            return "strong"
        elif change_pct > 0.5:
            return "moderate"
        else:
            return "weak"
    
    def _classify_fundamental_trend(self, structured_data: Optional[Dict]) -> str:
        """Classify fundamental trend."""
        if not structured_data:
            return "unknown"
        
        # TODO: Analyze revenue/profit trends
        # For now, return generic
        return "growth"
    
    def _assess_earnings_quality(self, structured_data: Optional[Dict]) -> Optional[str]:
        """Assess earnings quality."""
        if not structured_data:
            return None
        
        # TODO: Analyze cash flow vs profit
        return "high"
    
    def _assess_valuation(self, structured_data: Optional[Dict]) -> Optional[str]:
        """Assess valuation level."""
        if not structured_data:
            return None
        
        # TODO: Compare P/E vs historical/sector
        return "fair"
    
    def _extract_macro_drivers(self, news_data: Optional[Dict]) -> List[str]:
        """Extract macro drivers from news."""
        if not news_data:
            return []
        
        # TODO: Use NLP to extract drivers
        return ["interest rates", "inflation", "global growth"]
    
    def _extract_sector_drivers(self, sector_data: Optional[Dict]) -> List[str]:
        """Extract sector-specific drivers."""
        if not sector_data:
            return []
        
        # TODO: Extract from sector data
        return []
    
    def _identify_risk_flags(
        self, structured_data: Optional[Dict], news_data: Optional[Dict]
    ) -> List[str]:
        """Identify risk flags."""
        risks = []
        
        # TODO: Analyze for risks
        # - High debt
        # - Declining margins
        # - Regulatory issues
        # - Management changes
        
        return risks
    
    def _assess_volatility(self, market_data: Optional[Dict]) -> Optional[str]:
        """Assess volatility regime."""
        if not market_data:
            return None
        
        # TODO: Calculate historical volatility
        return "normal"
    
    def _format_price_display(self, market_data: Optional[Dict]) -> Optional[str]:
        """
        Format price data for display in prompts.
        
        NEW: Handles both Dhan API data and Perplexity fallback data.
        
        Returns formatted string like: "₹4,250.50 (+1.2%, +₹50.35)"
        Or for fallback: "⚠️ Data from web search: [Perplexity summary]"
        """
        if not market_data:
            return None
        
        # NEW: Check if this is Perplexity fallback data
        if market_data.get("source") == "perplexity_fallback":
            perplexity_data = market_data.get("perplexity_data", "")
            fallback_reason = market_data.get("fallback_reason", "Stock not found in Dhan")
            
            # Extract first 200 characters of Perplexity response
            summary = perplexity_data[:200] + "..." if len(perplexity_data) > 200 else perplexity_data
            
            return f"⚠️ {fallback_reason}\n\n{summary}"
        
        # Standard Dhan API data handling
        last_price = market_data.get("last_price")
        change_percent = market_data.get("change_percent")
        close = market_data.get("close")
        
        if last_price is None:
            return None
        
        # Format price with Indian number system (lakhs, crores)
        formatted_price = f"₹{last_price:,.2f}"
        
        # Calculate absolute change
        if close and close > 0:
            absolute_change = last_price - close
            sign = "+" if change_percent >= 0 else ""
            change_str = f"({sign}{change_percent:.2f}%, {sign}₹{absolute_change:.2f})"
        elif change_percent is not None:
            sign = "+" if change_percent >= 0 else ""
            change_str = f"({sign}{change_percent:.2f}%)"
        else:
            change_str = ""
        
        return f"{formatted_price} {change_str}".strip()
    
    def _calculate_support_levels(self, market_data: Optional[Dict]) -> Optional[List[float]]:
        """
        Calculate support levels from OHLC data.
        
        Simple approach: Use low and close as support levels.
        """
        if not market_data:
            return None
        
        low = market_data.get("low")
        close = market_data.get("close")
        
        levels = []
        if low:
            levels.append(round(low, 2))
        if close and close != low:
            # Add a level slightly below close (e.g., 2% below)
            levels.append(round(close * 0.98, 2))
        
        return levels if levels else None
    
    def _calculate_resistance_levels(self, market_data: Optional[Dict]) -> Optional[List[float]]:
        """
        Calculate resistance levels from OHLC data.
        
        Simple approach: Use high and close as resistance levels.
        """
        if not market_data:
            return None
        
        high = market_data.get("high")
        close = market_data.get("close")
        
        levels = []
        if high:
            levels.append(round(high, 2))
        if close and close != high:
            # Add a level slightly above close (e.g., 2% above)
            levels.append(round(close * 1.02, 2))
        
        return levels if levels else None
    
    def _extract_technical_indicators(self, market_data: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """
        Extract technical indicators from market data.
        
        Note: Current Dhan API doesn't provide RSI/MACD directly.
        This is a placeholder for future enhancement.
        """
        if not market_data:
            return None
        
        indicators = {}
        
        # TODO: Calculate RSI, MACD from historical data
        # For now, return None to indicate unavailable
        # indicators["rsi"] = None
        # indicators["macd"] = None
        
        # We can calculate simple momentum from price change
        change_percent = market_data.get("change_percent")
        if change_percent is not None:
            if abs(change_percent) > 2:
                indicators["momentum"] = "strong"
            elif abs(change_percent) > 0.5:
                indicators["momentum"] = "moderate"
            else:
                indicators["momentum"] = "weak"
        
        return indicators if indicators else None
    
    def _calculate_confidence(self, *data_sources) -> str:
        """Calculate data confidence level."""
        available_sources = sum(1 for d in data_sources if d)
        
        if available_sources >= 3:
            return "high"
        elif available_sources >= 2:
            return "medium"
        else:
            return "low"
    
    def _classify_sector_performance(self, sector_data: Optional[Dict]) -> str:
        """Classify sector performance."""
        if not sector_data:
            return "unknown"
        
        # Get Nifty change from sector_data
        nifty_change = sector_data.get("nifty_change", 0)
        
        # Classify based on Nifty performance
        if nifty_change > 2:
            return "strong_up"
        elif nifty_change > 0.5:
            return "moderate_up"
        elif nifty_change < -2:
            return "strong_down"
        elif nifty_change < -0.5:
            return "moderate_down"
        else:
            return "neutral"
    
    def _calculate_sector_relative_strength(self, sector_data: Optional[Dict]) -> str:
        """Calculate sector relative strength."""
        if not sector_data:
            return "unknown"
        
        # Get sectors list and find top performers
        sectors = sector_data.get("sectors", [])
        if not sectors:
            return "unknown"
        
        # Find top 3 and bottom 3 sectors by performance
        sorted_sectors = sorted(sectors, key=lambda x: x.get("change_percent", 0), reverse=True)
        
        top_3 = sorted_sectors[:3]
        bottom_3 = sorted_sectors[-3:]
        
        top_str = ", ".join([f"{s.get('name', 'N/A')}: {s.get('change_percent', 0):+.2f}%" for s in top_3])
        bottom_str = ", ".join([f"{s.get('name', 'N/A')}: {s.get('change_percent', 0):+.2f}%" for s in bottom_3])
        
        return f"Top: {top_str} | Bottom: {bottom_str}"
    
    def _assess_sector_momentum(self, sector_data: Optional[Dict]) -> str:
        """Assess sector momentum."""
        if not sector_data:
            return "unknown"
        
        # Calculate average sector performance
        sectors = sector_data.get("sectors", [])
        if not sectors:
            return "unknown"
        
        avg_change = sum(s.get("change_percent", 0) for s in sectors) / len(sectors)
        
        # Count positive vs negative sectors
        positive_count = sum(1 for s in sectors if s.get("change_percent", 0) > 0)
        total_count = len(sectors)
        positive_ratio = positive_count / total_count if total_count > 0 else 0
        
        # Assess momentum based on breadth and average change
        if positive_ratio > 0.7 and avg_change > 1:
            return "strong_positive"
        elif positive_ratio > 0.5 and avg_change > 0:
            return "moderate_positive"
        elif positive_ratio < 0.3 and avg_change < -1:
            return "strong_negative"
        elif positive_ratio < 0.5 and avg_change < 0:
            return "moderate_negative"
        else:
            return "mixed"
    
    def _calculate_breadth(self, constituent_data: Optional[List[Dict]]) -> str:
        """Calculate market breadth."""
        if not constituent_data:
            return "unknown"
        
        # Calculate advance/decline ratio from constituent sectors
        advancing = sum(1 for s in constituent_data if s.get("change_percent", 0) > 0)
        declining = sum(1 for s in constituent_data if s.get("change_percent", 0) < 0)
        total = len(constituent_data)
        
        if total == 0:
            return "unknown"
        
        advance_ratio = advancing / total
        
        # Classify breadth
        if advance_ratio > 0.7:
            return f"broad ({advancing}/{total} sectors advancing)"
        elif advance_ratio > 0.4:
            return f"moderate ({advancing}/{total} sectors advancing)"
        else:
            return f"narrow ({advancing}/{total} sectors advancing)"
    
    def _assess_participation(self, constituent_data: Optional[List[Dict]]) -> str:
        """Assess market participation."""
        if not constituent_data:
            return "unknown"
        
        # Analyze participation based on sector distribution
        total = len(constituent_data)
        if total == 0:
            return "unknown"
        
        # Count sectors with significant moves (>1% or <-1%)
        significant_moves = sum(1 for s in constituent_data if abs(s.get("change_percent", 0)) > 1)
        participation_ratio = significant_moves / total
        
        if participation_ratio > 0.6:
            return "healthy (broad participation)"
        elif participation_ratio > 0.3:
            return "moderate (selective participation)"
        else:
            return "weak (narrow participation)"
    
    def _extract_sector_specific_drivers(
        self, sector: str, news_data: Optional[Dict]
    ) -> List[str]:
        """Extract sector-specific drivers."""
        drivers = []
        
        # Extract from Indian API news if available
        if news_data and "indian_api_news" in news_data:
            indian_news = news_data["indian_api_news"]
            if isinstance(indian_news, list):
                # Extract headlines related to the sector
                sector_keywords = {
                    "IT": ["tech", "software", "it", "digital"],
                    "Banking": ["bank", "credit", "lending", "npa"],
                    "Pharma": ["pharma", "drug", "healthcare", "medicine"],
                    "Auto": ["auto", "vehicle", "car", "ev"],
                    "Energy": ["oil", "energy", "power", "renewable"],
                    "FMCG": ["consumer", "fmcg", "retail"],
                }
                
                keywords = sector_keywords.get(sector, [])
                for item in indian_news[:5]:  # Top 5 news items
                    title = item.get("title", "").lower()
                    if any(kw in title for kw in keywords):
                        drivers.append(item.get("title", "")[:100])  # Truncate long titles
        
        # Extract from Perplexity answer if available
        if news_data and "answer" in news_data:
            answer = news_data["answer"]
            if isinstance(answer, str) and sector.lower() in answer.lower():
                # Extract first sentence mentioning the sector
                sentences = answer.split(".")
                for sent in sentences[:3]:
                    if sector.lower() in sent.lower():
                        drivers.append(sent.strip()[:150])
                        break
        
        return drivers[:3]  # Return top 3 drivers
    
    def _identify_sector_risks(
        self, sector: str, news_data: Optional[Dict]
    ) -> List[str]:
        """Identify sector-specific risks."""
        risks = []
        
        # Risk keywords to look for in news
        risk_keywords = [
            "concern", "risk", "challenge", "pressure", "decline", "fall",
            "regulatory", "investigation", "penalty", "slowdown", "weakness"
        ]
        
        # Extract from Indian API news
        if news_data and "indian_api_news" in news_data:
            indian_news = news_data["indian_api_news"]
            if isinstance(indian_news, list):
                for item in indian_news[:10]:  # Check top 10 news
                    title = item.get("title", "").lower()
                    if any(kw in title for kw in risk_keywords):
                        risks.append(item.get("title", "")[:100])
        
        # Extract from Perplexity answer
        if news_data and "answer" in news_data:
            answer = news_data["answer"].lower()
            for keyword in risk_keywords:
                if keyword in answer:
                    # Find sentence containing the risk keyword
                    sentences = news_data["answer"].split(".")
                    for sent in sentences:
                        if keyword in sent.lower():
                            risks.append(sent.strip()[:150])
                            break
        
        return risks[:3]  # Return top 3 risks
    
    # ========================================================================
    # Enhanced Analysis Methods (using MongoDB data)
    # ========================================================================
    
    def _classify_fundamental_trend_enhanced(
        self, stats: Optional[Dict], quarterly: Optional[Dict]
    ) -> str:
        """Classify fundamental trend using actual growth stats."""
        if not stats or isinstance(stats, Exception):
            return "unknown"
        
        # Get 3-year sales and profit CAGR
        sales_growth = stats.get('compounded sales growth', {})
        profit_growth = stats.get('compounded profit growth', {})
        
        sales_3yr = sales_growth.get('3 Years', 0) if isinstance(sales_growth, dict) else 0
        profit_3yr = profit_growth.get('3 Years', 0) if isinstance(profit_growth, dict) else 0
        
        # Classify based on growth rates
        if sales_3yr > 15 and profit_3yr > 15:
            return "growth"
        elif sales_3yr < 5 and profit_3yr < 5:
            return "value"
        elif sales_3yr > 10:
            return "cyclical"
        else:
            return "defensive"
    
    def _assess_earnings_quality_enhanced(
        self, quarterly: Optional[Dict], ratios: Optional[Dict]
    ) -> Optional[str]:
        """Assess earnings quality using ratios."""
        if not ratios or isinstance(ratios, Exception):
            return None
        
        # Check ROCE (Return on Capital Employed)
        roce = ratios.get('roce %', {})
        if isinstance(roce, dict):
            # Get latest ROCE value
            latest_roce = None
            for key in sorted(roce.keys(), reverse=True):
                if roce[key] and roce[key] != 'N/A':
                    try:
                        latest_roce = float(roce[key])
                        break
                    except:
                        pass
            
            if latest_roce:
                if latest_roce > 20:
                    return "high"
                elif latest_roce > 10:
                    return "medium"
                else:
                    return "low"
        
        return "medium"
    
    def _assess_valuation_enhanced(
        self, company: Optional[Dict], quarterly: Optional[Dict]
    ) -> Optional[str]:
        """Assess valuation level."""
        # TODO: Calculate P/E from market cap and earnings
        # For now, return generic
        return "fair"
    
    def _identify_risk_flags_enhanced(
        self,
        shareholding: Optional[Dict],
        announcements: Optional[List[Dict]],
        ratios: Optional[Dict]
    ) -> List[str]:
        """Identify risk flags from shareholding and announcements."""
        risks = []
        
        # Check promoter holding changes
        if shareholding and not isinstance(shareholding, Exception):
            promoters = shareholding.get('promoters', {})
            if isinstance(promoters, dict):
                # Get latest and previous promoter holding
                holdings = []
                for key in sorted(promoters.keys(), reverse=True)[:2]:
                    val = promoters[key]
                    if val and val != 'N/A':
                        try:
                            holdings.append(float(val))
                        except:
                            pass
                
                if len(holdings) >= 2:
                    change = holdings[0] - holdings[1]
                    if change < -2:  # Promoter holding decreased by >2%
                        risks.append("promoter_holding_decline")
        
        # Check announcements for regulatory issues
        if announcements and not isinstance(announcements, Exception):
            for ann in announcements:
                title = ann.get('title', '').lower()
                if any(word in title for word in ['penalty', 'sebi', 'regulatory', 'investigation']):
                    risks.append("regulatory_concerns")
                    break
        
        # Check working capital efficiency
        if ratios and not isinstance(ratios, Exception):
            cash_cycle = ratios.get('cash conversion cycle', {})
            if isinstance(cash_cycle, dict):
                # Get latest value
                for key in sorted(cash_cycle.keys(), reverse=True):
                    val = cash_cycle[key]
                    if val and val != 'N/A':
                        try:
                            cycle_days = float(val)
                            if cycle_days > 100:  # High working capital requirement
                                risks.append("high_working_capital")
                            break
                        except:
                            pass
        
        return risks
    
    def _calculate_confidence_enhanced(self, *data_sources) -> str:
        """Calculate data confidence level with enhanced logic."""
        available_sources = sum(1 for d in data_sources if d and not isinstance(d, Exception))
        
        if available_sources >= 4:
            return "high"
        elif available_sources >= 2:
            return "medium"
        else:
            return "low"


# Singleton instance
_evidence_builder: Optional[EvidenceBuilder] = None


def get_evidence_builder() -> EvidenceBuilder:
    """Get singleton evidence builder instance."""
    global _evidence_builder
    if _evidence_builder is None:
        _evidence_builder = EvidenceBuilder()
    return _evidence_builder
