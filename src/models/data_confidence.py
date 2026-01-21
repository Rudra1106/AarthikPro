"""
Data Confidence & Source Attribution System.

Provides metadata about data quality, sources, and freshness
to prevent hallucination and build user trust.
"""

from typing import Dict, Any, List
from datetime import datetime
import pytz


class DataConfidence:
    """Data confidence levels and source attribution."""
    
    # Confidence levels
    HIGH = "high"           # Real-time verified data
    MEDIUM = "medium"       # Cached/delayed data
    LOW = "low"            # Derived/calculated data
    PROVISIONAL = "provisional"  # Pending official confirmation
    
    @staticmethod
    def get_completeness_banner(state: Dict[str, Any]) -> str:
        """
        Generate data completeness banner for response.
        
        Shows what data is available vs pending to set user expectations.
        
        Args:
            state: Graph state with data availability flags
            
        Returns:
            Formatted banner string
        """
        available = []
        pending = []
        
        # Check what's available
        if state.get("sector_data"):
            available.append("Sector performance")
        else:
            pending.append("Sector data")
            
        if state.get("market_data"):
            available.append("Index levels")
        else:
            pending.append("Index levels")
            
        # FII/DII - check if actually available
        fii_dii_data = state.get("fii_dii_data", {})
        if fii_dii_data and fii_dii_data.get("fii_net") is not None and fii_dii_data.get("fii_net") != 0:
            available.append("FII/DII flows")
        else:
            pending.append("FII/DII (published after market close by NSDL)")
        
        # Global cues
        if state.get("global_cues"):
            available.append("Global markets")
        else:
            pending.append("Global markets")
        
        # Build banner
        banner = "📊 **Data Coverage**\n"
        
        if available:
            banner += f"✅ Available: {', '.join(available)}\n"
        
        if pending:
            banner += f"⚠️ Pending: {', '.join(pending)}\n"
        
        return banner
    
    @staticmethod
    def tag_data_source(
        data: Any,
        source: str,
        confidence: str,
        timestamp: datetime = None
    ) -> Dict[str, Any]:
        """
        Tag data with source and confidence metadata.
        
        Args:
            data: The actual data value
            source: Data source (e.g., "NSE", "Yahoo Finance")
            confidence: Confidence level (HIGH/MEDIUM/LOW/PROVISIONAL)
            timestamp: When data was fetched
            
        Returns:
            Dict with data + metadata
        """
        ist = pytz.timezone('Asia/Kolkata')
        if timestamp is None:
            timestamp = datetime.now(ist)
        
        return {
            "value": data,
            "source": source,
            "confidence": confidence,
            "timestamp": timestamp.strftime("%I:%M %p IST"),
            "date": timestamp.strftime("%d %b %Y")
        }
    
    @staticmethod
    def format_with_source(
        label: str,
        value: Any,
        source: str,
        confidence: str = None
    ) -> str:
        """
        Format data point with source attribution.
        
        Example:
            "FII Net: ₹-3,597 Cr (Provisional - NSE)"
        
        Args:
            label: Data label
            value: Data value
            source: Data source
            confidence: Optional confidence level
            
        Returns:
            Formatted string with source
        """
        result = f"{label}: {value}"
        
        if confidence and confidence == DataConfidence.PROVISIONAL:
            result += f" ({confidence.title()} - {source})"
        else:
            result += f" (Source: {source})"
        
        return result


class ComplianceFilter:
    """Filter advisory language to maintain compliance."""
    
    # Prohibited phrases (stock recommendations)
    PROHIBITED = [
        "consider positions in",
        "buy",
        "sell",
        "accumulate",
        "book profits",
        "exit",
        "add to portfolio",
        "recommended stocks",
        "stock picks"
    ]
    
    # Prediction language to replace
    PREDICTION_REPLACEMENTS = {
        "will": "may",
        "targets": "may see upside toward",
        "expect": "technical levels suggest",
        "should": "could",
        "going to": "likely to"
    }
    
    @staticmethod
    def remove_stock_recommendations(text: str) -> str:
        """
        Remove stock-level recommendations from text.
        
        Replaces:
            "Consider positions in WIPRO and TECHM"
        With:
            "Sector showing momentum led by large-cap names"
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # This is a placeholder - actual implementation would use
        # more sophisticated NLP to detect and replace stock calls
        for phrase in ComplianceFilter.PROHIBITED:
            if phrase.lower() in text.lower():
                # Log warning
                print(f"⚠️ WARNING: Prohibited phrase detected: {phrase}")
        
        return text
    
    @staticmethod
    def soften_predictions(text: str) -> str:
        """
        Replace prediction language with observation language.
        
        Args:
            text: Input text
            
        Returns:
            Text with softened predictions
        """
        result = text
        for old, new in ComplianceFilter.PREDICTION_REPLACEMENTS.items():
            result = result.replace(old, new)
        
        return result
    
    @staticmethod
    def add_disclaimer(section_type: str) -> str:
        """
        Get appropriate disclaimer for section type.
        
        Args:
            section_type: Type of section (technical/scenario/fii_dii/etc)
            
        Returns:
            Disclaimer text
        """
        disclaimers = {
            "technical": "⚠️ Note: Technical levels are observations, not predictions",
            "scenario": "⚠️ Note: Scenarios are for educational purposes, not trading advice",
            "fii_dii": "⚠️ Note: Institutional flow data is provisional and subject to revision",
            "sector": "⚠️ Note: Sector-level observation, not stock-specific advice",
            "investment": "⚠️ Disclaimer: This is educational content. Consult a SEBI-registered advisor for personalized advice"
        }
        
        return disclaimers.get(section_type, "")


def get_data_confidence() -> DataConfidence:
    """Get DataConfidence singleton."""
    return DataConfidence()


def get_compliance_filter() -> ComplianceFilter:
    """Get ComplianceFilter singleton."""
    return ComplianceFilter()
