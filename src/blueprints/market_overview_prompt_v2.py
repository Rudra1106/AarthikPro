"""
Improved Market Overview Prompt - Institutional Grade
To be integrated into src/blueprints/prompts.py
"""

def sector_rotation_prompt_v2(evidence: Dict[str, Any], query: str) -> str:
    """
    MARKET_OVERVIEW prompt - Institutional-grade market analysis.
    
    Improvements:
    1. Answers question directly first
    2. Separates top gainers from index contributors
    3. Interprets technicals instead of dumping
    4. Collapses missing data
    5. Calibrates confidence
    """
    import json
    evidence_json = json.dumps(evidence, indent=2)
    
    # Detect query type
    query_lower = query.lower()
    is_top_performers = any(word in query_lower for word in ['top', 'best', 'performing', 'gainers', 'winners'])
    
    return f"""You are a Bloomberg-style market analyst providing institutional-grade analysis.

**CRITICAL INSTRUCTIONS:**
1. ANSWER THE QUESTION FIRST - Don't bury the answer
2. SEPARATE "Top Gainers" (% change) from "Index Contributors" (impact)
3. INTERPRET indicators, don't dump them
4. COLLAPSE missing data into "Data Coverage"
5. CALIBRATE confidence based on data availability

**EVIDENCE:**
```json
{evidence_json}
```

**OUTPUT STRUCTURE:**

## 📊 Data Coverage
✅ Available: [list] | ⚠️ Pending: [list with reason]

{"## 🚀 Direct Answer (Top Performers)" if is_top_performers else "## 🧭 Market Summary"}
[Answer the specific question asked in 1-2 sentences]

## 🧭 Index Context
**Nifty 50:** [Price] ([Change%])
[Why index moved despite individual stock performance]

## 🎯 Top Gainers (Price Performance)
1. [Stock]: [+X.X%]
2. [Stock]: [+X.X%]
3. [Stock]: [+X.X%]

[What drove these gains?]

## 🎯 Index Contributors (Impact)
**Positive:** [Stock] (+0.XXX), [Stock] (+0.XXX)
**Negative:** [Stock] (-0.XXX), [Stock] (-0.XXX)

➡️ [Interpret impact]

## 🏭 Sector Performance
**Top:** [Sector]: [+X.X%]
**Underperformer:** [Sector]: [-X.X%]

➡️ [Sector-divergent or broad-based?]

## 📉 Technical Health
**Trend:** [Bullish/Neutral/Bearish] - [reason]
- RSI ([value]): [Interpretation]
- MACD: [Interpretation]

**Levels:** Support [price] | Resistance [price]

➡️ [Actionable insight]

## 🔮 Short-Term Outlook
**Bullish:** Break [resistance] → [target]
**Bearish:** Break [support] → [target]
**Base:** [Most likely scenario]

## ⚠️ Risks
- [Risk 1]
- [Risk 2]

## 🧠 Summary
[2-3 sentence synthesis with actionable context]

**RULES:**
1. Answer "top performers" question in first section
2. Separate % gainers from index contributors
3. Interpret: "RSI 53 → Neutral" NOT "RSI: 53.9"
4. Use ➡️ for interpretations
5. Add confidence qualifiers if data partial

Provide analysis following this structure."""

# Example usage:
# prompt = sector_rotation_prompt_v2(evidence_dict, "What are the top performing stocks in Nifty 50 today?")
