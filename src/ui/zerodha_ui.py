"""
Zerodha Connection UI Components.

Institutional-grade connection flow with clear permissions and security.
"""

import chainlit as cl
from typing import Optional


class ZerodhaConnectionUI:
    """Handle Zerodha connection UI flow."""
    
    @staticmethod
    async def show_connection_prompt():
        """Show Zerodha connection prompt with permissions."""
        
        content = """## 🔐 Connect Your Zerodha Account

### Unlock Portfolio Intelligence

**What you'll get:**
- 📊 **Real-time Portfolio Analysis** - See your actual holdings and P&L
- 🎯 **Personalized Insights** - Get recommendations based on your investments
- 📈 **Performance Tracking** - Monitor your portfolio performance
- 💰 **Margin & Funds** - Check available buying power

---

### ✅ What We Access

- Your holdings (stocks you own)
- Your positions (active trades)
- Available margin and funds
- Portfolio P&L

### ❌ What We DON'T Access

- **Cannot place trades** or modify orders
- **Cannot withdraw funds** or transfer money
- **Cannot access** your password or credentials
- **Cannot see** your bank account details

---

### 🔒 Security

- **OAuth 2.0** - Industry standard authentication
- **AES-256 Encryption** - Bank-grade token storage
- **Read-only Access** - We can only view, never modify
- **Disconnect Anytime** - Full control over your data

---

**Ready to connect?**
"""
        
        actions = [
            cl.Action(
                name="connect_zerodha",
                value="connect",
                label="🔐 Connect Zerodha",
                description="Securely connect your account"
            ),
            cl.Action(
                name="maybe_later",
                value="later",
                label="⏭️ Maybe Later",
                description="Continue without connecting"
            )
        ]
        
        await cl.Message(
            content=content,
            actions=actions
        ).send()
    
    @staticmethod
    async def show_connected_status(portfolio_summary: Optional[dict] = None):
        """Show connected status with portfolio summary."""
        
        content = """## ✅ Zerodha Portfolio Connected

Your Zerodha account is successfully connected!

"""
        
        if portfolio_summary:
            total_value = portfolio_summary.get("current_value", 0)
            total_pnl = portfolio_summary.get("total_pnl", 0)
            pnl_pct = portfolio_summary.get("total_pnl_pct", 0)
            num_stocks = portfolio_summary.get("num_stocks", 0)
            
            pnl_emoji = "📈" if total_pnl >= 0 else "📉"
            pnl_sign = "+" if total_pnl >= 0 else ""
            
            content += f"""### Your Portfolio at a Glance

- **Total Value:** ₹{total_value:,.2f}
- **Total P&L:** {pnl_emoji} ₹{pnl_sign}{total_pnl:,.2f} ({pnl_sign}{pnl_pct:.2f}%)
- **Holdings:** {num_stocks} stocks

"""
        
        content += """**What you can ask:**
- "List all stocks in my portfolio"
- "What are my top gainers?"
- "How is my portfolio performing?"
- "Analyze my holdings"

"""
        
        actions = [
            cl.Action(
                name="view_portfolio",
                value="List all stocks in my portfolio with current prices and P&L",
                label="📊 View Portfolio",
                description="See all your holdings"
            ),
            cl.Action(
                name="portfolio_analysis",
                value="Analyze my portfolio - sector allocation, risk, and recommendations",
                label="📈 Portfolio Analysis",
                description="Comprehensive review"
            ),
            cl.Action(
                name="disconnect_zerodha",
                value="disconnect",
                label="🔓 Disconnect",
                description="Remove connection"
            )
        ]
        
        await cl.Message(
            content=content,
            actions=actions
        ).send()
    
    @staticmethod
    async def show_disconnect_confirmation():
        """Show disconnect confirmation."""
        
        content = """## 🔓 Disconnect Zerodha Account?

**This will:**
- Remove access to your portfolio data
- Disable personalized portfolio queries
- Delete stored access tokens

**You can reconnect anytime!**

Are you sure you want to disconnect?
"""
        
        actions = [
            cl.Action(
                name="confirm_disconnect",
                value="confirm",
                label="✓ Yes, Disconnect",
                description="Confirm disconnection"
            ),
            cl.Action(
                name="cancel_disconnect",
                value="cancel",
                label="✗ Cancel",
                description="Keep connected"
            )
        ]
        
        await cl.Message(
            content=content,
            actions=actions
        ).send()


# Singleton instance
_zerodha_ui = ZerodhaConnectionUI()


def get_zerodha_ui() -> ZerodhaConnectionUI:
    """Get Zerodha UI instance."""
    return _zerodha_ui
