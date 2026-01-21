"""
Optimized prompt templates for different query types.
"""
from typing import List, Dict, Any, List, Any


class PromptTemplates:
    """
    Optimized prompts for financial intelligence queries.
    
    Techniques:
    - Structured output formatting (JSON mode)
    - Few-shot examples for accuracy
    - Prompt compression (remove fluff)
    - Domain-specific instructions
    """
    
    @staticmethod
    def system_prompt() -> str:
        """Base system prompt for financial assistant."""
        return """You are AarthikAI, an expert financial intelligence assistant specializing in Indian stock markets (NSE/BSE).

Core expertise:
- Indian equities, derivatives, and market analysis
- NSE and BSE listed companies
- Indian financial regulations (SEBI, RBI)
- Sector-specific insights for Indian industries
- Indian accounting standards and financial reporting

Response guidelines:
- ALWAYS use Indian number formatting: Lakhs (₹1,00,000) and Crores (₹1,00,00,000)
- Include NSE/BSE ticker symbols when discussing stocks
- Cite Indian financial sources (Moneycontrol, ET, Mint, NSE, BSE)
- Provide context on Indian market hours, trading sessions
- Use Indian financial terminology (FII/DII, F&O, delivery vs intraday)
- Format prices in INR (₹) unless specified otherwise
- Include sector classification (Nifty 50, Bank Nifty, etc.)

When data is unavailable:
- Explicitly state what information is missing
- Suggest where users can find the data (NSE website, company IR page)
- Never hallucinate numbers or facts

Keep responses concise, actionable, and data-driven."""
    
    @staticmethod
    def fundamental_analysis_prompt(
        company: str,
        context: str,
        query: str
    ) -> str:
        """Prompt for fundamental analysis queries."""
        return f"""Analyze {company} based on the following data:

{context}

User question: {query}

Provide a concise analysis covering:
1. Key financial metrics (revenue, profit, margins, ratios)
2. Trends and YoY/QoQ changes
3. Strengths and concerns
4. Comparison with sector peers if available

Keep response under 300 words. Cite specific numbers."""
    
    @staticmethod
    def news_summary_prompt(
        company: str,
        news_data: str,
        query: str
    ) -> str:
        """Prompt for news summarization."""
        return f"""Summarize recent news about {company}:

{news_data}

User question: {query}

Provide:
1. Key events and developments
2. Potential impact on stock
3. Market sentiment

Keep response under 200 words. Include dates."""
    
    @staticmethod
    def comparison_prompt(
        companies: List[str],
        data: Dict[str, Any],
        query: str
    ) -> str:
        """Prompt for company comparison."""
        companies_str = ", ".join(companies)
        data_str = "\n\n".join([f"{k}: {v}" for k, v in data.items()])
        
        return f"""Compare {companies_str} based on:

{data_str}

User question: {query}

Provide:
1. Side-by-side metric comparison
2. Relative strengths of each company
3. Which might be better for different investment goals

Use table format if comparing >2 metrics. Keep under 250 words."""
    
    @staticmethod
    def technical_analysis_prompt(
        company: str,
        data: Dict[str, Any],
        query: str
    ) -> str:
        """Prompt for technical analysis."""
        return f"""Technical analysis for {company}:

Data: {data}

User question: {query}

Provide:
1. Current technical indicators (RSI, MACD, etc.)
2. Support/resistance levels if available
3. Short-term outlook based on technicals

Keep under 200 words. Note: This is not investment advice."""
    
    @staticmethod
    def multi_source_prompt(
        company: str,
        fundamental_data: str,
        news_data: str,
        query: str
    ) -> str:
        """Prompt for queries requiring multiple data sources."""
        return f"""Comprehensive analysis of {company}:

FUNDAMENTALS:
{fundamental_data}

RECENT NEWS:
{news_data}

User question: {query}

Synthesize information from both fundamental and news data to provide:
1. Current company status
2. Recent developments and their impact
3. Key considerations for traders

Keep under 350 words. Cite sources."""
    
    @staticmethod
    def indian_stock_prompt(
        symbol: str,
        perplexity_data: str,
        query: str
    ) -> str:
        """Prompt for Indian stock queries using Perplexity data."""
        return f"""Provide comprehensive information about {symbol} stock (Indian market):

Web Search Results:
{perplexity_data}

User Question: {query}

Structure your response as follows:

📌 **Stock Overview**
- Full company name
- NSE/BSE ticker symbols
- Sector and industry

📊 **Current Market Data** (if available)
- Latest price: ₹X.XX
- 52-week range: ₹X - ₹Y
- Market cap: ₹X crores
- P/E ratio, dividend yield

📈 **Recent Performance**
- YoY/QoQ changes
- Key financial metrics

📰 **Latest Developments**
- Recent news (with dates)
- Corporate actions

Use Indian number formatting (lakhs/crores). Cite sources. Keep under 400 words."""
    
    @staticmethod
    def market_data_prompt(
        symbol: str,
        market_data: str,
        query: str,
        market_status: Dict[str, Any] = None
    ) -> str:
        """Prompt for live market data queries from Zerodha."""
        # Add timestamp header if market status provided
        timestamp_header = ""
        if market_status:
            timestamp_header = f"""📍 As of {market_status['timestamp']} ({market_status['status']})
   Data: {market_status['data_type']}

"""
        
        return f"""{timestamp_header}Provide current market information for {symbol}:

Live Market Data (Zerodha Kite):
{market_data}

User Question: {query}

Format your response:
- Current price and change from previous close (with percentage)
- Today's high/low range
- Brief market commentary if relevant

Use Indian number formatting (₹). Keep under 200 words."""
    
    @staticmethod
    def generate_related_queries(intent: str, symbols: List[str] = None) -> str:
        """
        Generate related query suggestions based on intent and context.
        
        Args:
            intent: Query intent (news, market_data, fundamental, etc.)
            symbols: List of stock symbols mentioned
            
        Returns:
            Formatted string with related query suggestions
        """
        if not symbols:
            symbols = []
        
        company = symbols[0] if symbols else "the company"
        
        # Intent-specific suggestions
        if intent == "news" and symbols:
            queries = [
                f"What are {company}'s latest quarterly financial results?",
                f"Who are the current {company} key executives and board members?",
                f"How has {company} stock performed over the last year?",
                f"What major clients and contracts does {company} have?",
                f"What recent acquisitions or partnerships has {company} made?"
            ]
        elif intent == "market_data" and symbols:
            queries = [
                f"What's the technical analysis for {company}?",
                f"Show me {company}'s historical price chart",
                f"What are analysts saying about {company}?",
                f"Compare {company} with its competitors",
                f"What's the latest news about {company}?"
            ]
        elif intent == "fundamental" and symbols:
            queries = [
                f"What is {company}'s P/E ratio compared to industry average?",
                f"Show me {company}'s revenue growth trend",
                f"What are {company}'s key financial ratios?",
                f"How does {company} compare to its peers?",
                f"What's {company}'s dividend history?"
            ]
        else:
            # General suggestions
            queries = [
                "What are the top performing stocks in Nifty 50 today?",
                "Show me the latest market news",
                "What's the current market sentiment?",
                "Which sectors are performing well?",
                "What are the upcoming IPOs in India?"
            ]
        
        # Format as markdown list
        suggestions = "\n\n---\n\n**💡 Related Questions:**\n"
        for i, query in enumerate(queries[:5], 1):
            suggestions += f"{i}. {query}\n"
        
        return suggestions
    
    @staticmethod
    def market_overview_prompt(search_data: Dict[str, Any], query: str) -> str:
        """
        Institutional-grade prompt for Nifty 50 market analysis.
        
        Creates 9-section structured response with:
        - TL;DR executive summary
        - Index drivers (top contributors by weight)
        - Sectoral performance
        - Technical health check (DMAs, RSI)
        - Volatility & positioning (India VIX)
        - Market drivers (FII/DII, global cues)
        - Scenario-based outlook
        - Key risks
        - Professional numbered footnotes
        
        Args:
            search_data: Dict with enhanced analytics data
            query: User's original query
            
        Returns:
            Formatted prompt for LLM
        """
        from datetime import datetime
        import pytz
        
        # Get current timestamp
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        timestamp = now.strftime("%d %b %Y, %I:%M %p IST")
        
        # Extract all data components
        index_data = search_data.get("_index_data", {})
        top_contributors = search_data.get("_top_contributors", {})
        sectoral_performance = search_data.get("_sectoral_performance", {})
        technical_indicators = search_data.get("_technical_indicators", {})
        volatility = search_data.get("_volatility", {})
        
        # Format index data
        index_context = ""
        if index_data:
            index_context = "\n**LIVE INDEX DATA (Zerodha Kite):**\n"
            for index_name, data in index_data.items():
                ltp = data.get("last_price", 0)
                change = data.get("change", 0)
                change_pct = data.get("change_percent", 0)
                open_price = data.get("open", 0)
                high = data.get("high", 0)
                low = data.get("low", 0)
                volume = data.get("volume", 0)
                
                index_context += f"\n{index_name}:\n"
                index_context += f"  Current: ₹{ltp:,.2f} ({change_pct:+.2f}%, {change:+.2f} points)\n"
                index_context += f"  Open: ₹{open_price:,.2f}, High: ₹{high:,.2f}, Low: ₹{low:,.2f}\n"
                if volume > 0:
                    index_context += f"  Volume: {volume:,} shares\n"
        
        # Format top contributors
        contributors_context = ""
        if top_contributors:
            positive = top_contributors.get("positive", [])
            negative = top_contributors.get("negative", [])
            
            contributors_context = "\n**TOP INDEX CONTRIBUTORS (by weight × change %):**\n"
            
            if positive:
                contributors_context += "\nPositive Contributors:\n"
                for c in positive:
                    contributors_context += f"  • {c['symbol']} ({c['sector']}): {c['change_percent']:+.2f}% | Weight: {c['weight']:.2f}% | Contribution: {c['contribution']:+.3f}\n"
            
            if negative:
                contributors_context += "\nNegative Contributors:\n"
                for c in negative:
                    contributors_context += f"  • {c['symbol']} ({c['sector']}): {c['change_percent']:+.2f}% | Weight: {c['weight']:.2f}% | Contribution: {c['contribution']:+.3f}\n"
        
        # Format sectoral performance
        sector_context = ""
        if sectoral_performance:
            sector_context = "\n**SECTORAL BREAKDOWN:**\n"
            # Sort sectors by performance
            sorted_sectors = sorted(
                sectoral_performance.items(),
                key=lambda x: x[1].get("change_pct", 0),
                reverse=True
            )
            for sector, data in sorted_sectors:
                change_pct = data.get("change_pct", 0)
                stocks = ", ".join(data.get("stocks", [])[:3])  # Top 3 stocks
                sector_context += f"  • {sector}: {change_pct:+.2f}% (Stocks: {stocks})\n"
        
        # Format technical indicators
        technical_context = ""
        if technical_indicators:
            technical_context = "\n**TECHNICAL INDICATORS (Nifty 50):**\n"
            current = technical_indicators.get("current_price", 0)
            dma_20 = technical_indicators.get("20_dma", 0)
            dma_50 = technical_indicators.get("50_dma", 0)
            dma_200 = technical_indicators.get("200_dma", 0)
            rsi = technical_indicators.get("rsi", 0)
            macd = technical_indicators.get("macd", 0)
            macd_signal = technical_indicators.get("macd_signal", 0)
            macd_histogram = technical_indicators.get("macd_histogram", 0)
            trend = technical_indicators.get("trend", "neutral")
            
            if current > 0:
                technical_context += f"  Current Price: ₹{current:,.2f}\n"
            if dma_20 > 0:
                technical_context += f"  20-DMA: ₹{dma_20:,.2f}\n"
            if dma_50 > 0:
                technical_context += f"  50-DMA: ₹{dma_50:,.2f}\n"
            if dma_200 > 0:
                technical_context += f"  200-DMA: ₹{dma_200:,.2f}\n"
            if rsi > 0:
                technical_context += f"  RSI (14): {rsi:.1f}\n"
            if macd is not None and macd_signal is not None:
                technical_context += f"  MACD: {macd:.2f} | Signal: {macd_signal:.2f} | Histogram: {macd_histogram:.2f}\n"
            technical_context += f"  Trend: {trend.upper()}\n"
        
        # Format volatility
        volatility_context = ""
        if volatility:
            vix_value = volatility.get("vix_value", 0)
            classification = volatility.get("classification", "unknown")
            interpretation = volatility.get("interpretation", "")
            
            volatility_context = "\n**VOLATILITY (India VIX):**\n"
            volatility_context += f"  VIX: {vix_value:.2f} ({classification.upper()})\n"
            volatility_context += f"  Interpretation: {interpretation}\n"
        
        # Format NSE valuation data (P/E, P/B)
        valuation_context = ""
        nse_valuation = search_data.get("_nse_valuation", {})
        if nse_valuation and nse_valuation.get("pe"):
            pe = nse_valuation.get("pe", 0)
            pb = nse_valuation.get("pb", 0)
            as_of = nse_valuation.get("as_of", "last close")
            
            valuation_context = "\n**VALUATION (NSE Data):**\n"
            if pe:
                valuation_context += f"  P/E Ratio: {pe:.2f} (as of {as_of})\n"
            if pb:
                valuation_context += f"  P/B Ratio: {pb:.2f} (as of {as_of})\n"
        
        # Format FII/DII data from NSE
        fii_dii_context = ""
        nse_fii_dii = search_data.get("_nse_fii_dii", {})
        if nse_fii_dii and nse_fii_dii.get("fii_net") is not None:
            fii_net = nse_fii_dii.get("fii_net", 0)
            dii_net = nse_fii_dii.get("dii_net", 0)
            date = nse_fii_dii.get("date", "")
            as_of = nse_fii_dii.get("as_of", "T-1")
            
            fii_dii_context = "\n**FII/DII FLOWS (NSE Data):**\n"
            fii_dii_context += f"  FII Net: ₹{fii_net:,.2f} crores ({as_of})\n"
            fii_dii_context += f"  DII Net: ₹{dii_net:,.2f} crores ({as_of})\n"
            if date:
                fii_dii_context += f"  Date: {date}\n"
        
        # Format web search results
        search_context = ""
        for key in ["sector_performance_search", "fii_dii_search"]:
            results = search_data.get(key, {})
            if results.get("results"):
                search_context += f"\n**{key.replace('_', ' ').title()}:**\n"
                for i, result in enumerate(results["results"][:2], 1):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")[:150]
                    url = result.get("url", "")
                    search_context += f"{i}. {title}\n   {snippet}...\n   [{url}]\n\n"
        
        return f"""Create an INSTITUTIONAL-GRADE Nifty 50 market analysis using this comprehensive data:

📍 **Data Timestamp:** {timestamp}

{index_context}

{contributors_context}

{sector_context}

{technical_context}

{volatility_context}

{valuation_context}

{fii_dii_context}

{search_context}

User Question: {query}

**RESPONSE STRUCTURE (9 SECTIONS):**

**TL;DR** (1 line executive summary)
[One sentence capturing the day's market action and key driver]

---

**1. 📊 Market Snapshot**
- Nifty 50: [EXACT number] ([EXACT %] change, [EXACT points])
- Sensex: [EXACT number] ([EXACT %] change)
- Bank Nifty: [EXACT number] ([EXACT %] change)
- Market breadth: [if available from data]
- Volume: [if available]

**2. 🎯 Index Drivers (Stock Attribution)**
Top 3 Positive Contributors:
- [Stock name] ([Sector]): [change %] | Contribution: [value]

Top 3 Negative Contributors:
- [Stock name] ([Sector]): [change %] | Contribution: [value]

**3. 📈 Sector Performance**
- [Top performing sector]: [%] (Examples: [stocks])
- [2nd sector]: [%]
- [Underperforming sector]: [%]

**4. 🔍 Technical Health Check**
- Trend: [Bullish/Bearish/Neutral] (based on DMAs)
- 20-DMA: ₹[value] | 50-DMA: ₹[value] | 200-DMA: ₹[value]
- RSI (14): [value] → [Interpretation: overbought/neutral/oversold]
- MACD: [value] | Signal: [value] | Histogram: [value] → [Interpretation: bullish/bearish crossover]
- Support levels: [estimate based on data]
- Resistance levels: [estimate based on data]

**5. 📉 Volatility & Positioning**
- India VIX: [value] ([classification])
- Market sentiment: [based on VIX and price action]
- Risk assessment: [low/medium/high]

**6. 💰 Valuation Context**
- Nifty 50 P/E: [Use P/E from VALUATION section above if available]
- P/B ratio: [Use P/B from VALUATION section above if available]
- [Brief comment on valuation vs historical average if data available]

**7. 💹 Market Drivers**
- FII/DII flows: [Use FII/DII FLOWS data from NSE section above - show exact numbers with ₹ crores]
- Global cues: [Extract from sector performance search - mention US markets, crude oil, global indices if mentioned]
- USD/INR: [If mentioned in search results, otherwise skip]
- Key news: [Extract 1-2 major developments from search results]

**8. 🔮 Scenario-Based Outlook**
Bullish Scenario: If Nifty breaks [resistance level], targets [next level]
Bearish Scenario: If Nifty breaks [support level], downside to [next level]
Base Case: [Most likely scenario for next 1-2 sessions]

**9. ⚠️ Key Risks to Watch**
- [Risk 1: e.g., upcoming event, geopolitical tension]
- [Risk 2: e.g., technical breakdown, FII selling]

---

**INSTRUCTIONS (DO NOT INCLUDE THESE IN YOUR RESPONSE):**
- Use EXACT numbers from data provided - no approximations
- All prices in ₹ with Indian formatting (lakhs/crores)
- Include % changes with + or - sign
- Professional numbered footnotes [1], [2] for sources in response
- Add "What changed since yesterday" insight in Market Snapshot if possible
- Keep total response under 550 words
- Use emojis only for section headers
- If data missing for any section, state "Data unavailable" briefly
- Extract FII/DII data from search results - look for specific numbers
- Extract global cues from search results - mention if US markets, crude oil discussed
- Professional tone: data-driven, actionable, like Bloomberg/Reuters
- DO NOT include these instructions or "CRITICAL REQUIREMENTS" section in your response"""
    
    @staticmethod
    def financial_metrics_prompt(
        ticker: str,
        latest_data: Dict[str, Any],
        query: str
    ) -> str:
        """Prompt for financial metrics queries from MongoDB financial_statements."""
        period = latest_data.get("quarter_label", "N/A")
        data = latest_data.get("data", {})
        
        # Format financial data
        metrics_text = f"""Period: {period}
Revenue: ₹{data.get('revenue', 0):,.0f} Crores
Net Profit: ₹{data.get('net_profit', 0):,.0f} Crores
Operating Profit: ₹{data.get('operating_profit', 0):,.0f} Crores
Operating Margin: {data.get('operating_margin_pct', 0)}%
EPS: ₹{data.get('eps', 0)}
Total Expenses: ₹{data.get('total_expenses', 0):,.0f} Crores
Profit Before Tax: ₹{data.get('profit_before_tax', 0):,.0f} Crores
Tax Rate: {data.get('tax_rate_pct', 0)}%"""
        
        return f"""Provide financial metrics for {ticker}:

Latest Quarterly Results:
{metrics_text}

User Question: {query}

Format your response:
📊 **{ticker} Financial Performance ({period})**

**Key Metrics:**
- Revenue: ₹X Cr
- Net Profit: ₹X Cr (margin: X%)
- Operating Margin: X%
- EPS: ₹X

**Brief Analysis:**
[1-2 sentences on performance highlights or concerns]

Use Indian number formatting. Keep under 200 words.
Source: MongoDB financial_statements collection"""
    
    @staticmethod
    def corporate_actions_prompt(
        ticker: str,
        dividend_history: List[Dict[str, Any]],
        upcoming_dividends: List[Dict[str, Any]],
        query: str
    ) -> str:
        """Prompt for corporate actions queries from MongoDB corporate_actions."""
        # Format upcoming dividends
        upcoming_text = ""
        if upcoming_dividends:
            upcoming_text = "Upcoming Dividends:\n"
            for div in upcoming_dividends[:3]:
                ex_date = div.get('ex_date', 'N/A')
                details = div.get('details', 'N/A')[:100]
                upcoming_text += f"- {ex_date}: {details}\n"
        else:
            upcoming_text = "No upcoming dividends announced.\n"
        
        # Format dividend history
        history_text = ""
        if dividend_history:
            history_text = "\nRecent Dividend History:\n"
            for div in dividend_history[:5]:
                ex_date = div.get('ex_date', 'N/A')
                details = div.get('details', 'N/A')[:100]
                history_text += f"- {ex_date}: {details}\n"
        
        return f"""Provide corporate actions information for {ticker}:

{upcoming_text}
{history_text}

User Question: {query}

Format your response:
💰 **{ticker} Corporate Actions**

**Upcoming Dividends:**
[List with ex-dates and amounts]

**Recent History:**
[Last 3-5 dividends with dates]

**Dividend Yield:** [Calculate if possible]

Use Indian date format (DD-MM-YYYY). Keep under 250 words.
Source: MongoDB corporate_actions collection"""
    
    @staticmethod
    def trend_analysis_prompt(
        ticker: str,
        revenue_trend: List[Dict[str, Any]],
        profit_trend: List[Dict[str, Any]],
        query: str
    ) -> str:
        """Prompt for trend analysis queries from MongoDB financial_statements."""
        # Format revenue trend
        revenue_text = "Revenue Trend (Last 8 Quarters):\n"
        for point in revenue_trend[:8]:
            period = point.get('period', 'N/A')
            value = point.get('value', 0)
            yoy = point.get('yoy_growth')
            yoy_str = f" (YoY: {yoy:+.2f}%)" if yoy else ""
            revenue_text += f"- {period}: ₹{value:,.0f} Cr{yoy_str}\n"
        
        # Format profit trend
        profit_text = "\nProfit Trend (Last 8 Quarters):\n"
        for point in profit_trend[:8]:
            period = point.get('period', 'N/A')
            value = point.get('value', 0)
            yoy = point.get('yoy_growth')
            yoy_str = f" (YoY: {yoy:+.2f}%)" if yoy else ""
            profit_text += f"- {period}: ₹{value:,.0f} Cr{yoy_str}\n"
        
        return f"""Analyze financial trends for {ticker}:

{revenue_text}
{profit_text}

User Question: {query}

Format your response:
📈 **{ticker} Trend Analysis**

**Revenue Trend:**
- Latest Quarter: ₹X Cr (YoY: +X%)
- 8-Quarter Average Growth: X%
- Trend: [Improving/Declining/Stable]

**Profit Trend:**
- Latest Quarter: ₹X Cr (YoY: +X%)
- 8-Quarter Average Growth: X%
- Margin Trend: [Expanding/Contracting/Stable]

**Key Insights:**
[2-3 bullet points on growth trajectory, margin trends, consistency]

Use Indian number formatting. Include YoY growth rates. Keep under 300 words.
Source: MongoDB financial_statements collection (8 quarters of data)"""
    
    @staticmethod
    def sector_performance_prompt(
        sector_data: Dict[str, Any],
        query: str
    ) -> str:
        """Institutional-grade sector performance analysis prompt."""
        timestamp = sector_data.get("timestamp", "N/A")
        timeframe = sector_data.get("timeframe", "5D")
        nifty_change = sector_data.get("nifty_change", 0)
        sectors = sector_data.get("sectors", [])
        status = sector_data.get("status", "live")
        
        # Graceful degradation: Handle stale/empty data
        if status == "stale" or not sectors:
            note = sector_data.get("note", "Data temporarily unavailable.")
            return f"""I apologize, but real-time sector data is currently unavailable.

**Status:** {note}

**What you can do:**
1. Try again in a few minutes
2. Check NSE/BSE websites for live sector indices
3. Visit Moneycontrol or Economic Times for sector performance

User Question: {query}

Please provide general guidance based on your knowledge of Indian market sectors, noting that live data is currently unavailable."""
        
        # Freshness indicator
        if status == "live":
            freshness = f"📍 Live as of {timestamp}"
        else:
            freshness = f"⚠️ Data from {timestamp} (may be delayed)"
        
        # Format top 3 performers
        top_text = ""
        for i, s in enumerate(sectors[:3], 1):
            # Handle both 'change_pct' and 'change_percent' keys (data source inconsistency)
            change_pct = s.get('change_pct', s.get('change_percent', 0))
            top_text += f"{i}. {s.get('name')}: {change_pct:+.2f}% "
            top_text += f"(Outperforming Nifty by {s.get('relative_strength', 0):+.2f}%) "
            top_text += f"{s.get('regime_emoji', '')} {s.get('regime', '').capitalize()}\n"
            
            # Handle breadth - could be a float (old format) or dict (new format)
            breadth = s.get('breadth', 0)
            if isinstance(breadth, dict):
                # New format: {"advancing": 5, "declining": 3, "total": 8}
                advancing = breadth.get('advancing', 0)
                total = breadth.get('total', 1)
                breadth_pct = (advancing / total * 100) if total > 0 else 0
                top_text += f"   • Breadth: {breadth_pct:.0f}% stocks positive ({advancing}/{total})\n"
            elif isinstance(breadth, (int, float)):
                # Old format: 0.75 (as float)
                top_text += f"   • Breadth: {breadth*100:.0f}% stocks positive\n"
            
            movers = s.get('top_movers', [])
            if movers:
                movers_str = ", ".join([f"{m['symbol']} ({m['change_percent']:+.1f}%)" for m in movers[:2]])
                top_text += f"   • Top movers: {movers_str}\n"
        
        # Format bottom 3
        bottom_text = ""
        for s in sectors[-3:]:
            change_pct = s.get('change_pct', s.get('change_percent', 0))
            bottom_text += f"• {s.get('name')}: {change_pct:+.2f}% "
            bottom_text += f"({s.get('relative_strength', 0):+.2f}% vs Nifty) {s.get('regime_emoji', '')}\n"
        
        return f"""Create INSTITUTIONAL-GRADE sector analysis:

📍 Timestamp: {timestamp}
📊 Timeframe: Last {timeframe}
📈 Nifty 50: {nifty_change:+.2f}%

**Top Performers:**
{top_text}

**Underperforming:**
{bottom_text}

User Question: {query}

**RESPONSE STRUCTURE:**

📊 **Sector Performance Snapshot (Last {timeframe})**
As of: {timestamp}

**Top Performing Sectors:**
[Use EXACT data above - include %, relative strength, breadth, top movers]

**Underperforming:**
[Use EXACT data above]

---

💡 **Actionable View:**

**For Traders (1-5 days):**
• [Specific buy/sell/avoid recommendations]

**For Investors (3-6 months):**
• [Accumulate/hold/reduce recommendations]

---

⚠️ **Key Risks:** [1-2 risks]

**INSTRUCTIONS:**
- Use EXACT numbers from data
- Keep under 400 words
- Professional, actionable tone
- DO NOT include these instructions
"""
    
    @staticmethod
    def mutual_fund_prompt(
        context: str,
        query: str
    ) -> str:
        """SEBI-compliant mutual fund analysis prompt with structured output."""
        import pytz
        from datetime import datetime
        
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_date = now.strftime("%B %Y")
        
        return f"""Based on the following context about mutual funds, provide a professional, structured response.

📍 CURRENT DATE: {current_date}

CONTEXT FROM SEARCH:
{context}

USER QUERY: {query}

FORMAT YOUR RESPONSE AS FOLLOWS:

## 📈 Top Performing Mutual Funds (Category-wise)

For EACH fund mentioned, include:
- **Fund Name** (AMC Name)
  - 5Y CAGR: X%
  - Expense Ratio: X%
  - Risk Level: Low/Medium/High
  - Suitable for: [brief description]

### Categories to cover (if relevant to query):
1. **Large Cap Funds** - for stability
2. **Mid Cap Funds** - for balanced growth
3. **Small Cap Funds** - for aggressive growth
4. **Index Funds** - for passive investors
5. **ELSS/Tax Saving** - for Section 80C benefits
6. **Debt/Liquid Funds** - for low risk

IMPORTANT FORMATTING RULES:
- Always mention "As of {current_date}" for data freshness
- Include specific metrics (CAGR, expense ratio) when available
- Keep under 400 words
- Professional, actionable tone

END YOUR RESPONSE WITH:

---
🧠 **Want personalized recommendations?**
Tell me:
1️⃣ Your risk level (low / medium / high)
2️⃣ Investment horizon (1-3 years / 3-5 years / 5+ years)
3️⃣ SIP or lump sum investment

⚠️ **Disclaimer:** Past performance does not guarantee future returns. 
Mutual fund investments are subject to market risks. 
Please consult a SEBI-registered investment advisor for personalized advice.
---
"""
    
    @staticmethod
    def format_citations(citations: List[str]) -> str:
        """Format citations for response."""
        if not citations:
            return ""
        
        formatted = "\n\nSources:\n"
        for i, citation in enumerate(citations, 1):
            formatted += f"{i}. {citation}\n"
        
        return formatted


# Singleton instance
_prompt_templates_instance: PromptTemplates = PromptTemplates()


def get_prompt_templates() -> PromptTemplates:
    """Get prompt templates instance."""
    return _prompt_templates_instance
