"""
UI/UX Components for AarthikAI Chatbot.

Implements institutional-grade interface with:
- Mode selection (Personal Finance vs Pro)
- Guided prompts
- Structured responses
- Data freshness indicators
"""

from enum import Enum
from typing import List, Dict
import chainlit as cl


class UserMode(Enum):
    """User interaction modes."""
    PERSONAL = "personal"
    PRO = "pro"


class GuidedPrompts:
    """Context-aware guided prompts for different modes."""
    
    PERSONAL_FINANCE = [
        {
            "label": "📈 Understand this stock",
            "value": "Explain {stock} in simple terms - what does the company do and is it a good long-term investment?",
            "description": "Get beginner-friendly stock analysis"
        },
        {
            "label": "🔄 Compare two sectors",
            "value": "Compare {sector1} vs {sector2} sectors - which is better for long-term growth?",
            "description": "Sector comparison for long-term investors"
        },
        {
            "label": "⚠️ Explain investment risks",
            "value": "What are the main risks I should know about when investing in {stock}?",
            "description": "Understand risks before investing"
        },
        {
            "label": "📊 Portfolio basics",
            "value": "How should I build a balanced portfolio for long-term wealth creation?",
            "description": "Learn portfolio construction"
        },
        {
            "label": "💡 Long-term strategy",
            "value": "What's a good investment strategy for someone just starting out?",
            "description": "Get started with investing"
        }
    ]
    
    PRO_MODE = [
        {
            "label": "🔬 Deep dive: Stock",
            "value": "Provide a comprehensive analysis of {stock} including financials, valuation, risks, and outlook",
            "description": "Institutional-grade stock analysis"
        },
        {
            "label": "📉 Sector rotation",
            "value": "Analyze current sector rotation trends and identify sectors with momentum",
            "description": "Sector performance analysis"
        },
        {
            "label": "📄 Annual report summary",
            "value": "Summarize the latest annual report for {stock} - key highlights and concerns",
            "description": "Extract insights from reports"
        },
        {
            "label": "⚡ Price action analysis",
            "value": "Analyze recent price action for {stock} - trend, momentum, key levels",
            "description": "Technical analysis"
        },
        {
            "label": "🎯 Risk-adjusted returns",
            "value": "Compare {stock1} vs {stock2} on risk-adjusted return metrics",
            "description": "Quantitative comparison"
        }
    ]
    
    PORTFOLIO_PROMPTS = [
        {
            "label": "📊 My holdings",
            "value": "List all stocks in my portfolio with current prices and P&L",
            "description": "View your portfolio"
        },
        {
            "label": "📈 Top gainers",
            "value": "What are my top gainers and losers?",
            "description": "Portfolio performance"
        },
        {
            "label": "⚖️ Portfolio analysis",
            "value": "Analyze my portfolio - sector allocation, risk, and recommendations",
            "description": "Comprehensive portfolio review"
        },
        {
            "label": "💰 Available funds",
            "value": "How much buying power do I have?",
            "description": "Check margin and funds"
        }
    ]
    
    @classmethod
    def get_prompts(cls, mode: UserMode, has_portfolio: bool = False) -> List[Dict]:
        """Get guided prompts based on mode and portfolio connection."""
        if mode == UserMode.PERSONAL:
            prompts = cls.PERSONAL_FINANCE.copy()
        else:
            prompts = cls.PRO_MODE.copy()
        
        # Add portfolio prompts if connected
        if has_portfolio:
            prompts.extend(cls.PORTFOLIO_PROMPTS)
        
        return prompts


class ResponseFormatter:
    """Format AI responses with structure and clarity."""
    
    @staticmethod
    def format_stock_analysis(
        symbol: str,
        summary: str,
        key_points: List[str],
        risks: List[str],
        data_sources: Dict[str, str]
    ) -> str:
        """Format stock analysis response."""
        
        response = f"## 📊 {symbol} Analysis\n\n"
        response += f"### Summary\n{summary}\n\n"
        
        response += "### Key Points\n"
        for point in key_points:
            response += f"✓ {point}\n"
        response += "\n"
        
        if risks:
            response += "### Risks\n"
            for risk in risks:
                response += f"⚠️ {risk}\n"
            response += "\n"
        
        response += "### Data Sources\n"
        for source, info in data_sources.items():
            response += f"• {source}: {info}\n"
        
        return response
    
    @staticmethod
    def format_data_coverage(available: List[str], pending: List[str]) -> str:
        """Format data coverage indicator."""
        
        coverage = "📊 **Data Coverage**\n"
        
        if available:
            coverage += "✅ **Available:** " + ", ".join(available) + "\n"
        
        if pending:
            coverage += "⚠️ **Pending:** " + ", ".join(pending) + "\n"
        
        return coverage
    
    @staticmethod
    def get_follow_up_actions(query: str, symbols: List[str] = None, intent: str = None):
        """Generate follow-up action buttons based on query context."""
        import chainlit as cl
        
        actions = []
        
        # Stock-specific follow-ups
        if symbols and len(symbols) > 0:
            symbol = symbols[0]
            
            actions.append(
                cl.Action(
                    name="explain_more",
                    value=f"Explain {symbol} in more detail - what are the key drivers and outlook?",
                    label="📖 Explain More",
                    description="Get detailed explanation"
                )
            )
            
            actions.append(
                cl.Action(
                    name="show_financials",
                    value=f"Show me the latest financial results for {symbol}",
                    label="📊 Show Financials",
                    description="View financial data"
                )
            )
            
            actions.append(
                cl.Action(
                    name="compare_peers",
                    value=f"Compare {symbol} with its sector peers",
                    label="⚖️ Compare Peers",
                    description="Sector comparison"
                )
            )
            
            actions.append(
                cl.Action(
                    name="check_news",
                    value=f"What's the latest news about {symbol}?",
                    label="📰 Latest News",
                    description="Recent updates"
                )
            )
        
        # General follow-ups
        else:
            actions.append(
                cl.Action(
                    name="market_overview",
                    value="What's the current market overview?",
                    label="🌐 Market Overview",
                    description="Nifty, Sensex, sectors"
                )
            )
            
            actions.append(
                cl.Action(
                    name="top_sectors",
                    value="Which sectors are performing best today?",
                    label="📈 Top Sectors",
                    description="Sector performance"
                )
            )
        
        return actions


class ModeSelector:
    """Handle mode selection UI."""
    
    @staticmethod
    async def show_selection():
        """Display mode selection screen."""
        
        actions = [
            cl.Action(
                name="select_personal",
                value="personal",
                label="📊 Personal Finance",
                description="Long-term investing, portfolio basics, risk understanding"
            ),
            cl.Action(
                name="select_pro",
                value="pro",
                label="⚡ Pro / Advanced",
                description="Deep analysis, data-driven insights, institutional-grade research"
            )
        ]
        
        await cl.Message(
            content="""# Welcome to AarthikAI 🚀

**Choose your mode to get started:**

**📊 Personal Finance** - Perfect for beginners and long-term investors
- Understand stocks and sectors
- Learn investment basics
- Build a balanced portfolio
- Manage risk effectively

**⚡ Pro / Advanced** - For experienced traders and analysts
- Institutional-grade analysis
- Financial statement deep dives
- Sector rotation insights
- Quantitative comparisons

*You can switch modes anytime from settings ⚙️*
""",
            actions=actions
        ).send()
    
    @staticmethod
    async def show_guided_prompts(mode: UserMode, has_portfolio: bool = False):
        """Show guided prompts for selected mode."""
        
        prompts = GuidedPrompts.get_prompts(mode, has_portfolio)
        
        # Create action buttons for each prompt
        actions = []
        for i, prompt in enumerate(prompts[:5]):  # Show top 5
            actions.append(
                cl.Action(
                    name=f"prompt_{i}",
                    value=prompt["value"],
                    label=prompt["label"],
                    description=prompt.get("description", "")
                )
            )
        
        # Add Zerodha connection button if not connected
        if not has_portfolio:
            actions.append(
                cl.Action(
                    name="connect_zerodha",
                    value="connect",
                    label="🔐 Connect Zerodha",
                    description="Unlock portfolio intelligence"
                )
            )
        
        mode_name = "Personal Finance" if mode == UserMode.PERSONAL else "Pro"
        
        content = f"""### {mode_name} Mode Selected ✓

**Quick Actions:**
Choose a suggested prompt below or type your own question.
"""
        
        if has_portfolio:
            content += "\n💼 **Your Zerodha portfolio is connected** - You can ask about your holdings!\n"
        else:
            content += "\n💡 **Tip:** Connect your Zerodha account to unlock personalized portfolio insights!\n"
        
        await cl.Message(
            content=content,
            actions=actions
        ).send()


# Singleton instances
_mode_selector = ModeSelector()
_response_formatter = ResponseFormatter()


def get_mode_selector() -> ModeSelector:
    """Get mode selector instance."""
    return _mode_selector


def get_response_formatter() -> ResponseFormatter:
    """Get response formatter instance."""
    return _response_formatter
