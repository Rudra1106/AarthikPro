"""
Simplified Market Overview Prompt Template.

Removes complex technical indicators and adds section summaries
for better user understanding.
"""


def simplified_market_overview_prompt(
    nifty_data: dict,
    bank_nifty_data: dict,
    top_contributors: list,
    sector_performance: dict,
    fii_dii_data: dict,
    news_headlines: list,
    query: str
) -> str:
    """
    Generate simplified market overview prompt.
    
    Improvements:
    1. Impact statements instead of contribution decimals
    2. Simplified technical indicators (no RSI/MACD exact values)
    3. Section summaries for context
    4. Better structured output
    
    Args:
        nifty_data: Nifty 50 data with price, change, technical trend
        bank_nifty_data: Bank Nifty data
        top_contributors: List of top 3 positive and negative contributors
        sector_performance: Sector-wise performance data
        fii_dii_data: FII/DII flow data (if available)
        news_headlines: List of news headlines from Perplexity
        query: User's original question
        
    Returns:
        Formatted prompt for LLM
    """
    
    # Build contributors section with impact statements
    from src.blueprints.evidence import get_impact_statement
    
    contributors_text = "**Top 3 Positive Contributors:**\n"
    for stock in top_contributors.get("positive", [])[:3]:
        impact = get_impact_statement(stock.get("contribution", 0))
        contributors_text += f"• {stock['symbol']} ({stock['sector']}): {stock['change']}% | {impact}\n"
    
    contributors_text += "\n**Top 3 Negative Contributors:**\n"
    for stock in top_contributors.get("negative", [])[:3]:
        impact = get_impact_statement(stock.get("contribution", 0))
        contributors_text += f"• {stock['symbol']} ({stock['sector']}): {stock['change']}% | {impact}\n"
    
    # Build simplified technical section
    nifty_trend = nifty_data.get("trend", "Neutral")  # Bullish/Neutral/Bearish
    nifty_momentum = nifty_data.get("momentum", "Neutral")  # Positive/Neutral/Negative
    price_vs_200dma = "Above" if nifty_data.get("price", 0) > nifty_data.get("dma_200", 0) else "Below"
    
    technical_text = f"""**Trend:** {nifty_trend}
**Momentum:** {nifty_momentum}
**Price vs 200-DMA:** {price_vs_200dma} ({"bullish" if price_vs_200dma == "Above" else "bearish"} signal)"""
    
    # Build FII/DII section
    fii_dii_text = ""
    if fii_dii_data.get("status") == "pending":
        fii_dii_text = f"⚠️ {fii_dii_data.get('message', 'FII/DII data pending publication')}"
    else:
        fii_net = fii_dii_data.get("fii_net", 0)
        dii_net = fii_dii_data.get("dii_net", 0)
        fii_status = "net sellers" if fii_net < 0 else "net buyers"
        dii_status = "net sellers" if dii_net < 0 else "net buyers"
        fii_dii_text = f"""• FII: ₹{abs(fii_net):.0f} Cr ({fii_status})
• DII: ₹{abs(dii_net):.0f} Cr ({dii_status})
• Source: NSE/NSDL (Provisional)"""
    
    # Build news section
    news_text = ""
    if news_headlines:
        news_text = "\n".join([f"• {headline}" for headline in news_headlines[:5]])
    else:
        news_text = "⚠️ News data pending - check financial news sites for latest updates"
    
    return f"""You are a financial markets analyst providing a daily market summary.

**CRITICAL RULES:**
🚨 Use ONLY the data provided below
🚨 Do NOT invent numbers or make up facts
🚨 Add section summaries (💡 Summary) for context
🚨 Keep language simple and clear

**USER QUERY:** {query}

**DATA PROVIDED:**

📊 **Index Performance:**
• Nifty 50: ₹{nifty_data.get('price', 0):,.2f} ({nifty_data.get('change_pct', 0):+.2f}%)
• Bank Nifty: ₹{bank_nifty_data.get('price', 0):,.2f} ({bank_nifty_data.get('change_pct', 0):+.2f}%)

🎯 **Index Drivers:**
{contributors_text}

📈 **Sector Performance:**
{sector_performance.get('summary', 'Sector data pending')}

🔍 **Technical Health:**
{technical_text}

💰 **FII/DII Activity:**
{fii_dii_text}

📰 **Key Headlines:**
{news_text}

---

**OUTPUT STRUCTURE (MANDATORY):**

## TL;DR
[1-2 sentence summary of the day - what moved markets and why]

## 📊 Market Snapshot
• Nifty 50: [price and change]
• Bank Nifty: [price and change]

💡 **Summary:** [1-sentence takeaway on overall market direction]

## 🎯 Index Drivers
[List top 3 positive and negative contributors with impact statements]

💡 **Summary:** [1-sentence on what sectors/stocks drove the market]

## 📈 Sector Performance
[Top 2-3 performing sectors and underperformers]

💡 **Summary:** [1-sentence on sector rotation theme]

## 🔍 Technical Health
• Trend: [Bullish/Neutral/Bearish]
• Momentum: [Positive/Neutral/Negative]
• Price vs 200-DMA: [Above/Below]

💡 **Summary:** [1-sentence technical interpretation]

## 💰 FII/DII Activity
[FII/DII flows with source attribution]

💡 **Summary:** [1-sentence on institutional flow impact]

## 📰 Key Headlines
[3-5 bullet points of major news]

💡 **Summary:** [1-sentence on key market themes from news]

---

**FINAL REMINDERS:**
- Every section MUST have a 💡 Summary
- Use impact statements (Major/Moderate/Minor contributor)
- Keep technical section simple (no RSI/MACD exact values)
- Add source attribution where applicable
- If data is missing, say "Data pending" - do NOT make it up

Generate the market summary following this exact structure."""


def get_simplified_market_prompt():
    """Get the simplified market overview prompt function."""
    return simplified_market_overview_prompt
