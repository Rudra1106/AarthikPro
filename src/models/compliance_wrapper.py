"""
Global Compliance Wrapper for All Prompts.

Wraps any prompt with mandatory safety guardrails to prevent:
- Stock-level recommendations
- Soft predictions without disclaimers
- Unverified data presentation
"""

from typing import Dict, Any


class ComplianceWrapper:
    """Wrap prompts with safety guardrails."""
    
    # Global safety rules that apply to ALL prompts
    GLOBAL_SAFETY_RULES = """
**🚨 MANDATORY COMPLIANCE RULES (APPLY TO ALL RESPONSES):**

1. **NO Stock Recommendations:**
   - ❌ DO NOT say: "Buy WIPRO", "Consider positions in TCS", "Accumulate INFY"
   - ✅ DO say: "IT sector showing momentum", "Led by large-cap names"

2. **NO Prediction Language:**
   - ❌ DO NOT say: "will target ₹26,250", "expect rally to ₹500"
   - ✅ DO say: "may see upside toward ₹26,250", "technical levels suggest"

3. **Source Attribution Required:**
   - Every number MUST have a source
   - Format: "FII Net: ₹-3,597 Cr (Provisional - NSE)"
   - Include timestamp when available

4. **Disclaimers Required:**
   - Add ⚠️ disclaimer after scenarios/technical levels
   - Format: "⚠️ Note: This is [observation/education], not [prediction/advice]"

5. **Data Confidence:**
   - If data is provisional, say so explicitly
   - If data is unavailable, don't make it up
   - Format: "Data pending" or "Limited data available"
"""
    
    @staticmethod
    def wrap_prompt(
        base_prompt: str,
        prompt_type: str = "general",
        add_data_banner: bool = True
    ) -> str:
        """
        Wrap any prompt with global compliance rules.
        
        Args:
            base_prompt: The original prompt
            prompt_type: Type of prompt (sector/technical/fii_dii/investment)
            add_data_banner: Whether to add data completeness reminder
            
        Returns:
            Wrapped prompt with safety guardrails
        """
        wrapped = ComplianceWrapper.GLOBAL_SAFETY_RULES + "\n\n"
        
        # Add type-specific rules
        if prompt_type == "sector":
            wrapped += """
**SECTOR-SPECIFIC RULES:**
- Provide sector-level analysis ONLY
- NO individual stock tickers in recommendations
- Add: "⚠️ Sector-level analysis, not stock-specific advice"
"""
        elif prompt_type == "technical":
            wrapped += """
**TECHNICAL ANALYSIS RULES:**
- Present levels as observations, not predictions
- Replace "targets" with "may see upside toward"
- Add: "⚠️ Technical observation, not prediction"
"""
        elif prompt_type == "fii_dii":
            wrapped += """
**FII/DII RULES:**
- Tag all data as "Provisional - NSE/NSDL"
- Include publication time context
- Add: "⚠️ Institutional flow data is provisional"
"""
        elif prompt_type == "investment":
            wrapped += """
**INVESTMENT ADVICE RULES:**
- Provide framework, NOT specific recommendations
- Include personalization hook
- Add: "⚠️ Consult SEBI-registered advisor for personalized advice"
"""
        
        wrapped += "\n" + base_prompt
        
        return wrapped
    
    @staticmethod
    def add_data_completeness_reminder(prompt: str, state: Dict[str, Any]) -> str:
        """
        Add data completeness context to prompt.
        
        Args:
            prompt: Base prompt
            state: Graph state with data availability
            
        Returns:
            Prompt with data context
        """
        available = []
        pending = []
        
        if state.get("sector_data"):
            available.append("Sector performance")
        else:
            pending.append("Sector data")
            
        if state.get("market_data"):
            available.append("Index levels")
        else:
            pending.append("Index levels")
        
        data_context = "\n**DATA AVAILABILITY CONTEXT:**\n"
        if available:
            data_context += f"✅ Available: {', '.join(available)}\n"
        if pending:
            data_context += f"⚠️ Pending: {', '.join(pending)}\n"
        data_context += "→ Only use data marked as available. For pending data, say 'Data pending'.\n\n"
        
        return data_context + prompt
    
    @staticmethod
    def get_response_footer(prompt_type: str) -> str:
        """
        Get appropriate footer/disclaimer for response type.
        
        Args:
            prompt_type: Type of prompt
            
        Returns:
            Footer text with disclaimer
        """
        footers = {
            "sector": "\n\n⚠️ **Note:** This is sector-level analysis, not stock-specific advice. Consult a SEBI-registered advisor for personalized recommendations.",
            "technical": "\n\n⚠️ **Note:** Technical levels are observations based on historical patterns, not predictions of future performance.",
            "fii_dii": "\n\n⚠️ **Note:** Institutional flow data is provisional and subject to revision by NSE/NSDL.",
            "investment": "\n\n⚠️ **Disclaimer:** This is educational content only. For personalized investment advice, consult a SEBI-registered financial advisor.",
            "general": "\n\n⚠️ **Note:** This analysis is for educational purposes. Always do your own research and consult professionals before making investment decisions."
        }
        
        return footers.get(prompt_type, footers["general"])


def wrap_with_compliance(
    prompt: str,
    prompt_type: str = "general",
    state: Dict[str, Any] = None
) -> str:
    """
    Convenience function to wrap prompt with all compliance layers.
    
    Args:
        prompt: Base prompt
        prompt_type: Type of prompt
        state: Optional graph state for data context
        
    Returns:
        Fully wrapped compliant prompt
    """
    wrapper = ComplianceWrapper()
    
    # Add data context if state provided
    if state:
        prompt = wrapper.add_data_completeness_reminder(prompt, state)
    
    # Wrap with global rules
    prompt = wrapper.wrap_prompt(prompt, prompt_type)
    
    return prompt
