"""
India Impact Mapper - Geopolitical event impact on Indian economy.

Maps global geopolitical events to Indian economic channels:
- Oil sanctions → Crude imports → Inflation
- Tech sanctions → IT exports
- Banking sanctions → FX flows → INR
- Defense sanctions → PSU defense stocks
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum


class ImpactStrength(str, Enum):
    """Impact strength levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    NEGLIGIBLE = "Negligible"


class IndiaImpactMapper:
    """
    Map geopolitical events to Indian economic impact.
    
    Uses hardcoded rules (not LLM inference) to ensure accuracy.
    """
    
    # Impact rules: event_type → (channels, strength, downstream_effects)
    IMPACT_RULES = {
        "oil_sanctions": {
            "channels": ["Crude Imports", "Energy Costs"],
            "strength": ImpactStrength.HIGH,
            "downstream_effects": [
                "Fuel prices",
                "Inflation (CPI)",
                "Fiscal deficit",
                "INR pressure"
            ],
            "affected_sectors": ["Oil \u0026 Gas", "Transportation", "FMCG"],
            "market_sensitivity": "High"
        },
        
        "tech_sanctions": {
            "channels": ["IT Exports", "Technology Access"],
            "strength": ImpactStrength.MEDIUM,
            "downstream_effects": [
                "IT sector revenue",
                "Tech imports",
                "Digital infrastructure"
            ],
            "affected_sectors": ["IT Services", "Electronics"],
            "market_sensitivity": "Medium"
        },
        
        "banking_sanctions": {
            "channels": ["FX Flows", "Trade Finance"],
            "strength": ImpactStrength.MEDIUM,
            "downstream_effects": [
                "INR volatility",
                "FII flows",
                "Trade settlement"
            ],
            "affected_sectors": ["Banking", "NBFC"],
            "market_sensitivity": "High"
        },
        
        "defense_sanctions": {
            "channels": ["Defense Imports", "Military Equipment"],
            "strength": ImpactStrength.LOW,
            "downstream_effects": [
                "Defense procurement",
                "PSU defense stocks",
                "Strategic partnerships"
            ],
            "affected_sectors": ["Defense", "Aerospace"],
            "market_sensitivity": "Low"
        },
        
        "shipping_sanctions": {
            "channels": ["Trade Costs", "Logistics"],
            "strength": ImpactStrength.MEDIUM,
            "downstream_effects": [
                "Import costs",
                "Export competitiveness",
                "Supply chain delays"
            ],
            "affected_sectors": ["Shipping", "Logistics", "Trade"],
            "market_sensitivity": "Medium"
        },
        
        "commodity_sanctions": {
            "channels": ["Commodity Prices", "Supply Chains"],
            "strength": ImpactStrength.HIGH,
            "downstream_effects": [
                "Input costs",
                "Manufacturing",
                "Consumer prices"
            ],
            "affected_sectors": ["Metals", "Chemicals", "Manufacturing"],
            "market_sensitivity": "High"
        },
    }
    
    # Country-specific impact mappings
    COUNTRY_IMPACT = {
        "Russia": {
            "primary_channel": "oil_sanctions",
            "trade_relationship": "Energy imports, defense equipment",
            "impact_note": "India sources ~2-3% crude from Russia; sanctions may affect pricing and payment mechanisms"
        },
        
        "Iran": {
            "primary_channel": "oil_sanctions",
            "trade_relationship": "Crude oil imports (historically ~10%)",
            "impact_note": "Sanctions significantly reduced Indian crude imports from Iran; alternative sourcing required"
        },
        
        "China": {
            "primary_channel": "tech_sanctions",
            "trade_relationship": "Electronics, machinery, pharma APIs",
            "impact_note": "Trade tensions may affect Indian imports and regional supply chains"
        },
        
        "US": {
            "primary_channel": "tech_sanctions",
            "trade_relationship": "IT exports, trade partnership",
            "impact_note": "US is India's largest export destination; policy changes affect IT sector"
        },
    }
    
    def __init__(self):
        pass
    
    def identify_event_type(self, event_description: str, entities: Dict[str, List[str]]) -> Optional[str]:
        """
        Identify event type from description and entities.
        
        Args:
            event_description: Description of geopolitical event
            entities: Extracted entities (countries, sectors)
        
        Returns:
            Event type key or None
        """
        event_lower = event_description.lower()
        
        # Check for oil/energy sanctions
        if any(word in event_lower for word in ["oil", "crude", "energy", "petroleum"]):
            return "oil_sanctions"
        
        # Check for tech sanctions
        if any(word in event_lower for word in ["tech", "technology", "software", "semiconductor"]):
            return "tech_sanctions"
        
        # Check for banking/financial sanctions
        if any(word in event_lower for word in ["bank", "financial", "swift", "payment"]):
            return "banking_sanctions"
        
        # Check for defense sanctions
        if any(word in event_lower for word in ["defense", "military", "weapons", "arms"]):
            return "defense_sanctions"
        
        # Check for shipping sanctions
        if any(word in event_lower for word in ["shipping", "maritime", "vessel", "port"]):
            return "shipping_sanctions"
        
        # Check for commodity sanctions
        if any(word in event_lower for word in ["commodity", "metal", "mineral", "grain"]):
            return "commodity_sanctions"
        
        # Default to oil if country is major oil exporter
        if entities.get("countries"):
            country = entities["countries"][0]
            if country in ["Russia", "Iran", "Saudi Arabia", "Iraq"]:
                return "oil_sanctions"
        
        return None
    
    def get_impact(
        self,
        event_description: str,
        entities: Dict[str, List[str]]
    ) -> Dict[str, any]:
        """
        Get India-specific impact for a geopolitical event.
        
        Args:
            event_description: Description of event
            entities: Extracted entities
        
        Returns:
            Impact analysis dict
        """
        # Identify event type
        event_type = self.identify_event_type(event_description, entities)
        
        if not event_type:
            return {
                "impact_available": False,
                "reason": "Event type not recognized"
            }
        
        # Get impact rules
        impact_rules = self.IMPACT_RULES.get(event_type, {})
        
        # Get country-specific context
        country_context = None
        if entities.get("countries"):
            country = entities["countries"][0]
            country_context = self.COUNTRY_IMPACT.get(country)
        
        # Build impact analysis
        impact = {
            "impact_available": True,
            "event_type": event_type,
            "channels": impact_rules.get("channels", []),
            "strength": impact_rules.get("strength", ImpactStrength.MEDIUM).value,
            "downstream_effects": impact_rules.get("downstream_effects", []),
            "affected_sectors": impact_rules.get("affected_sectors", []),
            "market_sensitivity": impact_rules.get("market_sensitivity", "Medium"),
        }
        
        # Add country context if available
        if country_context:
            impact["country_context"] = country_context
        
        return impact
    
    def format_impact_summary(self, impact: Dict[str, any]) -> str:
        """
        Format impact analysis into human-readable summary.
        
        Args:
            impact: Impact dict from get_impact()
        
        Returns:
            Formatted summary string
        """
        if not impact.get("impact_available"):
            return "No specific India impact data available for this event."
        
        lines = []
        
        # Header
        lines.append(f"**India Impact Analysis** ({impact['strength']} Impact)")
        lines.append("")
        
        # Channels
        if impact.get("channels"):
            lines.append("**Primary Channels:**")
            for channel in impact["channels"]:
                lines.append(f"- {channel}")
            lines.append("")
        
        # Downstream effects
        if impact.get("downstream_effects"):
            lines.append("**Downstream Effects:**")
            for effect in impact["downstream_effects"]:
                lines.append(f"- {effect}")
            lines.append("")
        
        # Affected sectors
        if impact.get("affected_sectors"):
            lines.append("**Affected Indian Sectors:**")
            for sector in impact["affected_sectors"]:
                lines.append(f"- {sector}")
            lines.append("")
        
        # Country context
        if impact.get("country_context"):
            ctx = impact["country_context"]
            lines.append("**Trade Context:**")
            lines.append(f"- {ctx.get('trade_relationship', 'N/A')}")
            lines.append(f"- {ctx.get('impact_note', 'N/A')}")
            lines.append("")
        
        # Market sensitivity
        lines.append(f"**Market Sensitivity:** {impact.get('market_sensitivity', 'Medium')}")
        
        return "\n".join(lines)


# Singleton instance
_impact_mapper: Optional[IndiaImpactMapper] = None


def get_india_impact_mapper() -> IndiaImpactMapper:
    """Get singleton India impact mapper instance."""
    global _impact_mapper
    if _impact_mapper is None:
        _impact_mapper = IndiaImpactMapper()
    return _impact_mapper
