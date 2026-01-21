    @staticmethod
    def vertical_analysis_prompt(
        vertical_data: Dict[str, Any],
        query: str
    ) -> str:
        """Institutional-grade vertical/segment analysis prompt - Bloomberg quality."""
        ticker = vertical_data.get("ticker", "")
        fiscal_year = vertical_data.get("fiscal_year", "FY2024")
        industry = vertical_data.get("industry", "")
        verticals = vertical_data.get("verticals", [])
        total_revenue = vertical_data.get("total_revenue", 0)
        
        if not verticals:
            return f"No vertical data available for {ticker}. {query}"
        
        # Classify verticals into primary, secondary, lagging
        primary = verticals[0] if verticals else None  # Largest revenue
        secondary = [v for v in verticals[1:4] if v.get("yoy_growth", 0) > 8]  # Strong growth
        lagging = [v for v in verticals if v.get("yoy_growth", 0) < 5]  # Weak growth
        
        # Format primary driver
        primary_text = ""
        if primary:
            name = primary.get("display_name", primary.get("vertical"))
            revenue = primary.get("revenue", 0)
            revenue_pct = primary.get("revenue_pct", 0)
            yoy = primary.get("yoy_growth", 0)
            notes = primary.get("notes", "")
            
            primary_text = f"""**Primary Growth Driver:**
{name}: ~{revenue_pct:.0f}% of revenue ({yoy:+.1f}% YoY) 🏦
• Revenue: ₹{revenue:,.0f} Cr
{f"• {notes}" if notes else ""}"""
        
        # Format secondary contributors
        secondary_text = ""
        if secondary:
            secondary_text = "**Secondary Contributors:**\n"
            for v in secondary:
                name = v.get("display_name", v.get("vertical"))
                revenue_pct = v.get("revenue_pct", 0)
                yoy = v.get("yoy_growth", 0)
                secondary_text += f"{name}: ~{revenue_pct:.0f}% of revenue ({yoy:+.1f}% YoY)\n"
        
        # Format lagging verticals
        lagging_text = ""
        if lagging:
            lagging_names = [v.get("display_name", v.get("vertical")) for v in lagging[:2]]
            lagging_text = f"\n**Lagging Verticals:** {', '.join(lagging_names)}"
        
        return f"""Create INSTITUTIONAL-GRADE vertical analysis for {ticker}:

📊 **Vertical Data ({fiscal_year})**

{primary_text}

{secondary_text}
{lagging_text}

Total Revenue: ₹{total_revenue:,.0f} Cr

User Question: {query}

**RESPONSE FORMAT (Bloomberg-Quality):**

📊 **{ticker} – Growth Drivers by Vertical ({fiscal_year})**

{primary_text}

{secondary_text}

🔍 **Bottom Line (Analyst Take):**
• [Primary vertical] remains core growth engine
• [Secondary verticals] provide incremental upside
• [Key trend or insight from data]

---

**Data Source:** {fiscal_year} Annual Report
**Extracted:** [Current timestamp]
**Confidence:** ✅ High (from annual report segment data)

**CRITICAL INSTRUCTIONS:**
1. Use EXACT numbers from data above
2. Include time anchor ({fiscal_year})
3. Show hierarchy: Primary → Secondary → Lagging
4. Add analyst bottom-line (2-3 bullets, data-driven)
5. Keep under 300 words
6. Professional, conviction-driven tone
7. DO NOT include these instructions in response
"""

