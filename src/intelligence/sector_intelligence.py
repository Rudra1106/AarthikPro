"""
Sector Intelligence Module - Sector-level analysis and comparison.

Provides sector profiles, comparative analysis, and investment guidance
for sector-based queries.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class SectorProfile:
    """Sector characteristics and intelligence."""
    name: str
    business_model: str
    growth_drivers: List[str]
    typical_margins: str
    capital_intensity: str
    cyclicality: str
    currency_exposure: str
    dividend_yield: str
    investor_type: str
    key_risks: List[str]


class SectorIntelligence:
    """
    Sector-level intelligence for comparison and analysis.
    
    Provides sector profiles, comparison logic, and investment guidance.
    """
    
    # Comprehensive sector profiles
    SECTOR_PROFILES = {
        "IT": SectorProfile(
            name="Information Technology",
            business_model="Export-oriented, asset-light services driven by global demand for digital transformation, cloud migration, and enterprise outsourcing",
            growth_drivers=[
                "Global digital transformation spending",
                "Cloud migration and SaaS adoption",
                "Emerging tech (AI, automation, cybersecurity)",
                "Outsourcing and cost optimization"
            ],
            typical_margins="20-25% (High)",
            capital_intensity="Low",
            cyclicality="Medium (tied to global economic cycles)",
            currency_exposure="High (70-80% USD revenue)",
            dividend_yield="1-2% (Low-Medium)",
            investor_type="Growth investors seeking earnings expansion",
            key_risks=[
                "Global recession impacting client spending",
                "Currency volatility (USD/INR)",
                "Talent cost inflation and attrition",
                "Technology disruption and competition"
            ]
        ),
        
        "Energy": SectorProfile(
            name="Energy",
            business_model="Domestically-driven, capital-intensive operations focused on power generation, distribution, and renewable energy transition",
            growth_drivers=[
                "India's economic growth and infrastructure",
                "Renewable energy transition (solar, wind)",
                "Electrification and EV adoption",
                "Energy security and self-sufficiency"
            ],
            typical_margins="10-15% (Medium)",
            capital_intensity="Very High",
            cyclicality="High (commodity prices and demand cycles)",
            currency_exposure="Low (mostly domestic)",
            dividend_yield="2-4% (Medium-High)",
            investor_type="Value/income investors, cyclical plays",
            key_risks=[
                "Commodity price swings (oil, gas, coal)",
                "Regulatory changes and policy shifts",
                "High capital expenditure execution risk",
                "Environmental and ESG concerns"
            ]
        ),
        
        "Banking": SectorProfile(
            name="Banking & Financial Services",
            business_model="Leveraged business model earning spread between deposits and loans, fee income from services",
            growth_drivers=[
                "Credit growth and financial inclusion",
                "Digital banking and fintech adoption",
                "Economic growth and consumption",
                "CASA (low-cost deposits) expansion"
            ],
            typical_margins="15-20% (Medium-High)",
            capital_intensity="Medium (regulatory capital)",
            cyclicality="High (economic cycles, credit quality)",
            currency_exposure="Low",
            dividend_yield="2-3% (Medium)",
            investor_type="Balanced investors, economic growth plays",
            key_risks=[
                "Asset quality and NPA cycles",
                "Interest rate risk",
                "Regulatory changes (RBI policies)",
                "Competition from fintech"
            ]
        ),
        
        "Auto": SectorProfile(
            name="Automobile",
            business_model="Manufacturing and distribution of vehicles (2W, 4W, CV) with cyclical demand patterns",
            growth_drivers=[
                "Rising income levels and urbanization",
                "EV transition and government incentives",
                "Rural demand and replacement cycles",
                "Export opportunities"
            ],
            typical_margins="8-12% (Medium)",
            capital_intensity="High",
            cyclicality="Very High (economic cycles, commodity prices)",
            currency_exposure="Medium (export revenue)",
            dividend_yield="1-3% (Medium)",
            investor_type="Cyclical investors, turnaround plays",
            key_risks=[
                "Commodity price volatility (steel, aluminum)",
                "Regulatory changes (emission norms, safety)",
                "EV disruption to traditional OEMs",
                "Demand cyclicality"
            ]
        ),
        
        "Pharma": SectorProfile(
            name="Pharmaceuticals",
            business_model="Research, manufacturing, and distribution of generic and specialty drugs with global reach",
            growth_drivers=[
                "Aging population and chronic diseases",
                "Generic drug opportunities in US/Europe",
                "Domestic healthcare penetration",
                "Specialty and complex generics"
            ],
            typical_margins="18-22% (High)",
            capital_intensity="Medium",
            cyclicality="Low (defensive sector)",
            currency_exposure="High (export-oriented)",
            dividend_yield="1-2% (Low-Medium)",
            investor_type="Defensive investors, healthcare themes",
            key_risks=[
                "Regulatory approvals (USFDA, EMA)",
                "Pricing pressure in generic markets",
                "Patent challenges and litigation",
                "Currency headwinds"
            ]
        ),
        
        "FMCG": SectorProfile(
            name="Fast Moving Consumer Goods",
            business_model="Mass consumption products with brand power, distribution reach, and pricing power",
            growth_drivers=[
                "Rising disposable incomes",
                "Rural penetration and premiumization",
                "Brand strength and innovation",
                "Distribution expansion"
            ],
            typical_margins="15-20% (Medium-High)",
            capital_intensity="Low-Medium",
            cyclicality="Low (defensive, staple demand)",
            currency_exposure="Low",
            dividend_yield="2-3% (Medium)",
            investor_type="Defensive investors, quality plays",
            key_risks=[
                "Raw material cost inflation",
                "Competition and market share loss",
                "Rural demand slowdown",
                "Regulatory changes (GST, labeling)"
            ]
        ),
        
        "Metals": SectorProfile(
            name="Metals & Mining",
            business_model="Capital-intensive commodity production with global pricing, cyclical demand, and high operating leverage",
            growth_drivers=[
                "Infrastructure and construction demand",
                "Global commodity price cycles",
                "Manufacturing and auto sector growth",
                "Export opportunities and China demand"
            ],
            typical_margins="10-15% (Medium, volatile)",
            capital_intensity="Very High",
            cyclicality="Very High (commodity cycles)",
            currency_exposure="High (export-oriented)",
            dividend_yield="2-4% (Medium-High, cyclical)",
            investor_type="Cyclical investors, commodity traders",
            key_risks=[
                "Global commodity price volatility",
                "China demand slowdown",
                "Environmental regulations and ESG",
                "High debt and capex requirements"
            ]
        ),
        
        "Telecom": SectorProfile(
            name="Telecom & Media",
            business_model="Network infrastructure with subscription revenue, high capex, and regulatory oversight",
            growth_drivers=[
                "5G rollout and data consumption",
                "Digital services and enterprise solutions",
                "ARPU improvement and tariff hikes",
                "Broadband and fiber expansion"
            ],
            typical_margins="25-35% (High EBITDA)",
            capital_intensity="Very High (spectrum, towers)",
            cyclicality="Low (essential service)",
            currency_exposure="Medium (equipment imports)",
            dividend_yield="1-2% (Low, reinvesting)",
            investor_type="Infrastructure investors, long-term plays",
            key_risks=[
                "Regulatory changes and spectrum costs",
                "Intense competition and price wars",
                "High debt from capex",
                "Technology disruption"
            ]
        ),
        
        "Realty": SectorProfile(
            name="Realty & Infrastructure",
            business_model="Real estate development and leasing with long gestation, high leverage, and cyclical demand",
            growth_drivers=[
                "Urbanization and housing demand",
                "Commercial office space growth",
                "Infrastructure and smart cities",
                "RERA and sector consolidation"
            ],
            typical_margins="20-30% (High, project-based)",
            capital_intensity="Very High",
            cyclicality="Very High (economic cycles)",
            currency_exposure="Low",
            dividend_yield="1-2% (Low)",
            investor_type="Long-term investors, turnaround plays",
            key_risks=[
                "Execution delays and cost overruns",
                "High debt and interest rate sensitivity",
                "Regulatory changes and approvals",
                "Demand cyclicality"
            ]
        ),
        
        "Capital Goods": SectorProfile(
            name="Capital Goods & Engineering",
            business_model="Project-based manufacturing and EPC with long order cycles and execution risk",
            growth_drivers=[
                "Infrastructure capex and PLI schemes",
                "Manufacturing growth and Make in India",
                "Defense and railways modernization",
                "Renewable energy projects"
            ],
            typical_margins="8-12% (Medium)",
            capital_intensity="Medium-High",
            cyclicality="High (capex cycles)",
            currency_exposure="Medium (exports + imports)",
            dividend_yield="1-3% (Medium)",
            investor_type="Cyclical investors, infrastructure themes",
            key_risks=[
                "Order execution delays",
                "Working capital intensity",
                "Commodity price volatility",
                "Government capex dependency"
            ]
        ),
        
        "Cement": SectorProfile(
            name="Cement & Construction Materials",
            business_model="Regional oligopolies with volume-driven growth, freight costs, and pricing power",
            growth_drivers=[
                "Infrastructure and housing demand",
                "Government capex on roads, railways",
                "Urbanization and real estate",
                "Consolidation and market share gains"
            ],
            typical_margins="18-25% (High EBITDA)",
            capital_intensity="Very High",
            cyclicality="Medium-High (construction cycles)",
            currency_exposure="Low",
            dividend_yield="2-3% (Medium)",
            investor_type="Infrastructure investors, defensive plays",
            key_risks=[
                "Coal and power cost volatility",
                "Overcapacity and price wars",
                "Monsoon and seasonal demand",
                "Environmental regulations"
            ]
        ),
        
        "Consumer Durables": SectorProfile(
            name="Consumer Durables",
            business_model="Discretionary purchases with brand power, distribution, and replacement cycles",
            growth_drivers=[
                "Rising incomes and aspirations",
                "Premiumization and product innovation",
                "Rural electrification and penetration",
                "Replacement demand and upgrades"
            ],
            typical_margins="8-12% (Medium)",
            capital_intensity="Medium",
            cyclicality="Medium-High (discretionary)",
            currency_exposure="Medium (imports)",
            dividend_yield="1-2% (Low-Medium)",
            investor_type="Growth investors, consumer themes",
            key_risks=[
                "Commodity price volatility (copper, steel)",
                "Competition and margin pressure",
                "Demand cyclicality",
                "Currency fluctuations (imports)"
            ]
        )
    }
    
    def get_profile(self, sector: str) -> Optional[SectorProfile]:
        """Get sector profile by name."""
        # Try exact match (case-insensitive)
        for key in self.SECTOR_PROFILES.keys():
            if key.upper() == sector.upper():
                return self.SECTOR_PROFILES[key]
        
        # Try partial match
        sector_upper = sector.upper()
        for key, profile in self.SECTOR_PROFILES.items():
            if sector_upper in key.upper() or key.upper() in sector_upper:
                return profile
        
        return None
    
    def compare_sectors(
        self,
        sector_a: str,
        sector_b: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive sector comparison.
        
        Args:
            sector_a: First sector name
            sector_b: Second sector name
            
        Returns:
            Dict with comparison data for template
        """
        profile_a = self.get_profile(sector_a)
        profile_b = self.get_profile(sector_b)
        
        if not profile_a or not profile_b:
            return {
                "error": f"Sector profile not found for {sector_a if not profile_a else sector_b}"
            }
        
        return {
            "sector_a_name": profile_a.name,
            "sector_b_name": profile_b.name,
            "business_models": {
                "sector_a": profile_a.business_model,
                "sector_b": profile_b.business_model
            },
            "comparison_table": {
                "growth_drivers": {
                    "sector_a": profile_a.growth_drivers[0] if profile_a.growth_drivers else "N/A",
                    "sector_b": profile_b.growth_drivers[0] if profile_b.growth_drivers else "N/A"
                },
                "margins": {
                    "sector_a": profile_a.typical_margins,
                    "sector_b": profile_b.typical_margins
                },
                "capital_intensity": {
                    "sector_a": profile_a.capital_intensity,
                    "sector_b": profile_b.capital_intensity
                },
                "cyclicality": {
                    "sector_a": profile_a.cyclicality,
                    "sector_b": profile_b.cyclicality
                },
                "dividend_yield": {
                    "sector_a": profile_a.dividend_yield,
                    "sector_b": profile_b.dividend_yield
                },
                "currency_exposure": {
                    "sector_a": profile_a.currency_exposure,
                    "sector_b": profile_b.currency_exposure
                }
            },
            "growth_drivers": {
                "sector_a": profile_a.growth_drivers,
                "sector_b": profile_b.growth_drivers
            },
            "risks": {
                "sector_a": profile_a.key_risks,
                "sector_b": profile_b.key_risks
            },
            "investor_suitability": {
                "sector_a": profile_a.investor_type,
                "sector_b": profile_b.investor_type
            }
        }
    
    def generate_comparison_summary(
        self,
        sector_a: str,
        sector_b: str
    ) -> str:
        """Generate 2-3 sentence comparison summary."""
        profile_a = self.get_profile(sector_a)
        profile_b = self.get_profile(sector_b)
        
        if not profile_a or not profile_b:
            return "Sector comparison not available."
        
        # Generate intelligent summary
        summary = f"{profile_a.name} is a {profile_a.cyclicality.split('(')[0].strip().lower()}-cyclicality sector "
        summary += f"with {profile_a.typical_margins.split('(')[0].strip().lower()} margins, "
        summary += f"suited for {profile_a.investor_type.lower()}. "
        
        summary += f"{profile_b.name} is a {profile_b.cyclicality.split('(')[0].strip().lower()}-cyclicality sector "
        summary += f"with {profile_b.typical_margins.split('(')[0].strip().lower()} margins, "
        summary += f"suited for {profile_b.investor_type.lower()}. "
        
        # Add key differentiator
        if profile_a.capital_intensity != profile_b.capital_intensity:
            summary += f"Key difference: {profile_a.name} is {profile_a.capital_intensity.lower()} capital intensity "
            summary += f"vs {profile_b.name}'s {profile_b.capital_intensity.lower()} capital intensity."
        
        return summary


# Singleton instance
_sector_intelligence: Optional[SectorIntelligence] = None


def get_sector_intelligence() -> SectorIntelligence:
    """Get singleton sector intelligence instance."""
    global _sector_intelligence
    if _sector_intelligence is None:
        _sector_intelligence = SectorIntelligence()
    return _sector_intelligence
