"""
UI Helpers - Formatting utilities for Chainlit messages.

Provides:
- Status badges
- Formatted sections
- Action buttons
- Visual elements
"""

from typing import List, Dict
import chainlit as cl


def format_data_coverage(available: List[str], pending: List[str]) -> str:
    """
    Format data coverage section with badges.
    
    Args:
        available: List of available data types
        pending: List of pending data types
    
    Returns:
        Formatted markdown string
    """
    lines = ["## 📊 Data Coverage\n"]
    
    if available:
        lines.append("✅ **Available**: " + ", ".join(available))
    
    if pending:
        lines.append("⚠️ **Pending**: " + ", ".join(pending))
    
    return "\n".join(lines) + "\n"


def create_quick_actions(symbol: str) -> List[cl.Action]:
    """
    Create quick action buttons for a stock.
    
    Args:
        symbol: Stock symbol
    
    Returns:
        List of Chainlit actions
    """
    return [
        cl.Action(
            name=f"compare_{symbol}",
            value=f"Compare {symbol} with peers",
            label="📊 Compare",
            description=f"Compare {symbol} with similar companies"
        ),
        cl.Action(
            name=f"news_{symbol}",
            value=f"Latest news about {symbol}",
            label="📰 News",
            description=f"Get latest news for {symbol}"
        ),
        cl.Action(
            name=f"technical_{symbol}",
            value=f"Technical analysis of {symbol}",
            label="📈 Technical",
            description=f"View technical analysis for {symbol}"
        )
    ]


def format_price_badge(price: float, change_pct: float) -> str:
    """
    Format price with color-coded badge.
    
    Args:
        price: Current price
        change_pct: Percentage change
    
    Returns:
        Formatted price string with emoji
    """
    emoji = "🟢" if change_pct >= 0 else "🔴"
    sign = "+" if change_pct >= 0 else ""
    return f"₹{price:,.2f} ({sign}{change_pct:.2f}%) {emoji}"


def format_metric_table(metrics: Dict[str, str]) -> str:
    """
    Format metrics as a clean table.
    
    Args:
        metrics: Dictionary of metric name to value
    
    Returns:
        Markdown table string
    """
    if not metrics:
        return ""
    
    lines = ["| Metric | Value |", "|--------|-------|"]
    for key, value in metrics.items():
        lines.append(f"| {key} | {value} |")
    
    return "\n".join(lines)


def create_collapsible_section(title: str, content: str) -> str:
    """
    Create a collapsible section.
    
    Args:
        title: Section title
        content: Section content
    
    Returns:
        Markdown collapsible section
    """
    return f"""<details>
<summary>{title}</summary>

{content}
</details>"""
