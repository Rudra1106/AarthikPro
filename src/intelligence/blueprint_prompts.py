"""
Blueprint-specific prompts for question-specific reasoning.

Each prompt is tailored to the question type and guides the LLM
to focus on relevant information and avoid irrelevant details.
"""
from typing import Dict, Any
from src.intelligence.question_classifier import QuestionType


def get_blueprint_prompt(
    question_type: QuestionType,
    question: str,
    filtered_data: str,
    tldr: str
) -> str:
    """
    Get the appropriate prompt for the question type.
    
    Args:
        question_type: Classified question type
        question: Original user question
        filtered_data: Pre-filtered relevant data
        tldr: Generated TL;DR
        
    Returns:
        Complete prompt for LLM
    """
    prompts = {
        QuestionType.INDEX_COMPARISON: _index_comparison_prompt,
        QuestionType.VERTICAL_ANALYSIS: _vertical_analysis_prompt,
        QuestionType.SECTOR_ROTATION: _sector_rotation_prompt,
        QuestionType.SCENARIO_ANALYSIS: _scenario_analysis_prompt,
        QuestionType.MACRO_VS_FUNDAMENTAL: _macro_fundamental_prompt,
        QuestionType.STOCK_DEEP_DIVE: _stock_deep_dive_prompt,
        QuestionType.MARKET_OVERVIEW: _market_overview_prompt,
        QuestionType.PRICE_CHECK: _price_check_prompt,
    }
    
    prompt_fn = prompts.get(question_type, _market_overview_prompt)
    return prompt_fn(question, filtered_data, tldr)


def _index_comparison_prompt(question: str, data: str, tldr: str) -> str:
    return f"""You are answering: "{question}"

This is an INDEX COMPARISON question. The user wants to understand WHY one index performed differently from another.

## TL;DR (use this as your opening line)
{tldr}

## Available Data
{data}

## Instructions
1. Start with the TL;DR as your opening sentence
2. Explain the ATTRIBUTION (which stocks caused the divergence)
3. Quantify the impact (weight × move = contribution to index)
4. Conclude with the key insight

## DO NOT INCLUDE (these are not relevant to this question)
- RSI, MACD, or any technical indicators
- P/E, P/B, or valuation metrics
- Support/resistance levels
- VIX analysis (unless specifically asked)
- Generic market snapshot
- Sector performance (unless directly explaining the divergence)

## Format
Start with the TL;DR, then explain the attribution clearly. Be concise and focused.
Use bullet points for stock attribution. End with a key insight.
"""


def _vertical_analysis_prompt(question: str, data: str, tldr: str) -> str:
    return f"""You are answering: "{question}"

This is a VERTICAL/SEGMENT ANALYSIS question. The user wants to understand business segment performance.

## TL;DR (use this as your opening line)
{tldr}

## Available Data
{data}

## Instructions
1. Start with the TL;DR
2. Break down segment-wise revenue/growth
3. Identify the key growth driver
4. Assess sustainability for next 2 quarters
5. Use concall commentary if available

## DO NOT INCLUDE (completely irrelevant to this question)
- Nifty/Sensex/Bank Nifty data
- Index snapshots
- Technical indicators (RSI, MACD)
- Market breadth
- VIX analysis
- Support/resistance levels

## Format
Focus entirely on the company's business verticals. Structure as:
1. Key Driver (which vertical is growing)
2. Breakdown (segment-wise contribution)
3. Sustainability (2-quarter outlook with reasoning)
"""


def _sector_rotation_prompt(question: str, data: str, tldr: str) -> str:
    return f"""You are answering: "{question}"

This is a SECTOR ROTATION question. The user wants institutional-grade sector leadership analysis.

## TL;DR (use this as your opening line)
{tldr}

## Available Data
{data}

## CRITICAL Bloomberg-Grade Requirements

### 1. Data Rigor
- Show ABSOLUTE index values, not just % change
  Example: "Nifty IT: 38,420 → 38,422 (+0.01%)"
- Include Nifty reference explicitly
  Example: "Nifty 50: 24,500 (-0.01%)"
- Validate breadth with stock counts
  Example: "2/10 stocks advancing (20%)" NOT "1% positive"

### 2. Relative Strength Calculation
ALWAYS show the calculation:
```
Nifty WTD: -0.01%
IT WTD: +0.00%
Relative Strength: +0.01% (outperforming)
```

### 3. Breadth Interpretation
DO NOT just dump numbers. Interpret:
- < 30%: "⚠️ Narrow leadership - stock-specific, not sector-wide"
- 30-70%: "⚖️ Mixed - selective performance"
- > 70%: "✅ Broad participation - sector-wide strength"

### 4. Leadership Definition
CRITICAL: "Leadership" = relative outperformance, NOT absolute gains
- IT +0.00% can be a "leader" if Nifty is -0.01%
- Use language: "relative outperformer" not "strong gains"

### 5. Conviction Signaling
If breadth < 30% AND absolute returns < 0.5%:
```
**Conviction Level**: 🔴 Low

Given flat absolute returns and weak breadth (20%), IT leadership is 
low-conviction and stock-specific rather than sector-wide rotation.
```

### 6. Required Format

Present as ranked table:

| Rank | Sector | Index Value | WTD % | vs Nifty | Breadth | Signal |
|------|--------|-------------|-------|----------|---------|--------|
| 1 📈 | IT | 38,420 (+2) | +0.00% | +0.01% | 2/10 (20%) | ⚠️ Narrow |
| 2 📉 | Financials | 45,200 (-225) | -0.50% | -0.49% | 9/20 (45%) | ⚖️ Mixed |

### 7. Rotation Insight
Go ONE LEVEL DEEPER than generic "cyclical vs defensive":
- Tie to drivers: "IT resilience → USD strength (₹84+), deal commentary"
- Reference breadth: "Despite flat index, weak breadth suggests stock-specific, not sector momentum"

### 8. Data Source Footer (MANDATORY)
```
---
**Data Source**: NSE Sectoral Indices via Zerodha Kite  
**As of**: [timestamp from data]  
**Timeframe**: Week-to-date (Mon-Thu close)
```

## DO NOT INCLUDE
- Individual stock attribution (unless explaining narrow breadth)
- RSI, MACD for indices
- P/E, P/B valuations
- Scenario analysis
- Stock-specific news

## Response Structure
1. TL;DR (with conviction assessment)
2. Nifty Reference (show the baseline)
3. Ranked Sector Table
4. Breadth Interpretation
5. Rotation Drivers (one level deeper)
6. Data Source Footer

Keep response under 500 words. Prioritize data rigor over verbosity.
"""


def _scenario_analysis_prompt(question: str, data: str, tldr: str) -> str:
    return f"""You are answering: "{question}"

This is a SCENARIO ANALYSIS question. The user is asking "what if" or "what happens next".

## TL;DR (use this as your opening line)
{tldr}

## Available Data
{data}

## Instructions
1. Start with the TL;DR (most likely outcome)
2. Define the current regime/condition
3. Present 3 scenarios with probabilities:
   - Bullish scenario (X% probability)
   - Base case (Y% probability)
   - Bearish scenario (Z% probability)
4. Reference historical analogs if available
5. State the most likely behavior

## DO NOT INCLUDE (not relevant to scenarios)
- Detailed index snapshot
- Sector breakdown
- Individual stock attribution
- Earnings data
- Vertical analysis

## Format
Structure clearly with scenarios and probabilities.
Be specific about conditions and outcomes.
"""


def _macro_fundamental_prompt(question: str, data: str, tldr: str) -> str:
    return f"""You are answering: "{question}"

This is a MACRO vs FUNDAMENTAL question. The user wants to understand what's driving a move.

## TL;DR (use this as your opening line)
{tldr}

## Available Data
{data}

## Instructions
1. Start with the TL;DR (the weighted conclusion)
2. Present fundamental signals:
   - Earnings momentum
   - Revenue growth
   - Margin trends
3. Present macro signals:
   - Currency (USD/INR)
   - Global sentiment
   - Policy factors
4. Quantify: "X% fundamental, Y% macro-driven"
5. Conclude with the primary driver

## DO NOT INCLUDE (not relevant)
- Index snapshot
- Technical indicators
- VIX analysis
- Sector rotation
- Support/resistance

## Format
Structure as:
1. Fundamental Drivers (with evidence)
2. Macro Factors (with evidence)
3. Conclusion: "X is [primarily/partially] [fundamental/macro]-driven because..."
"""


def _stock_deep_dive_prompt(question: str, data: str, tldr: str) -> str:
    return f"""You are answering: "{question}"

This is a STOCK DEEP DIVE question. The user wants comprehensive analysis of a specific stock.

## TL;DR (use this as your opening line)
{tldr}

## Available Data
{data}

## Instructions
1. Start with the TL;DR (valuation + growth + risk summary)
2. Price & Performance: Current price, day's change, 52-week range
3. Valuation: P/E, P/B vs historical and peers
4. Growth: Revenue/profit trends, key drivers
5. Risks: What could go wrong
6. Verdict: Clear view (Buy/Hold/Sell with reasoning)

## DO NOT INCLUDE (not the focus)
- Broad market index snapshot
- Bank Nifty data
- Sector rotation analysis
- VIX commentary
- Other stocks (unless for peer comparison)

## Format
Structure as:
📊 Price Action: ...
📈 Valuation: ...
📉 Growth: ...
⚠️ Risks: ...
🎯 Verdict: ...
"""


def _market_overview_prompt(question: str, data: str, tldr: str) -> str:
    return f"""You are answering: "{question}"

This is a MARKET OVERVIEW question. Give a comprehensive but concise market snapshot.

## TL;DR (use this as your opening line)
{tldr}

## Available Data
{data}

## Instructions
1. Start with the TL;DR
2. Index Snapshot: Nifty, Sensex, Bank Nifty with changes
3. Sector View: Top/bottom 3 sectors
4. Volatility: VIX level and interpretation
5. Sentiment: One-line market mood
6. Brief technical health (DMAs only if relevant)

## INCLUDE (relevant for market overview)
- All major indices
- Sector performance
- VIX interpretation
- FII/DII if significant

## KEEP BRIEF
- Don't deep dive into any single stock
- Don't include detailed RSI/MACD analysis
- Don't include earnings details
- Focus on the big picture

## Format
Use clear sections with emojis for scannability.
Keep it under 400 words.
"""


def _price_check_prompt(question: str, data: str, tldr: str) -> str:
    return f"""You are answering: "{question}"

This is a simple PRICE CHECK question. Give the price directly and concisely.

## TL;DR (this IS your answer)
{tldr}

## Available Data
{data}

## Instructions
1. Give the price immediately with the TL;DR
2. Include day's change (% and absolute)
3. If news context is available in the data, add a brief "Quick Context" section (2-3 lines max)
4. Keep the total response under 100 words

## DO NOT INCLUDE
- Market overview
- Sector analysis
- Technical indicators (RSI, MACD, etc.)
- Support/resistance levels
- VIX commentary
- Long-form analysis
- Detailed earnings data

## Format
**Price:** Direct answer with change
**Quick Context:** (only if news is available) 1-2 line summary of recent developments

Example with news:
"TCS is trading at ₹4,250.50 (+1.2%, +₹50.35).

**Quick Context:** TCS announced strong Q3 results with 15% YoY growth. The stock is benefiting from positive IT sector sentiment."

Example without news:
"TCS is trading at ₹4,250.50 (+1.2%, +₹50.35)."
"""


# System prompt for all blueprints
BLUEPRINT_SYSTEM_PROMPT = """You are AarthikAI, an intelligent financial analyst for Indian markets.

## Core Principles
1. ANSWER THE QUESTION DIRECTLY - Don't dump irrelevant information
2. FOCUS ON WHAT'S ASKED - Each question type has specific relevant data
3. BE SPECIFIC WITH NUMBERS - Quantify everything
4. NO GENERIC MARKET REPORTS - Tailor every response to the question
5. START WITH THE TL;DR - This is the direct answer

## Quality Standards
- Never show "Data unavailable" for sections that shouldn't be included
- If data is missing for required sections, acknowledge briefly and explain
- Use Indian market context (₹, NSE/BSE, IST timezone)
- Be concise but complete

## Response Style
- Use markdown formatting
- Use emojis for visual scannability (📊 📈 📉 ⚠️ 🎯)
- Bold key numbers and conclusions
- Keep responses focused and scannable
"""
