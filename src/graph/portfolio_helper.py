"""
Helper function to inject portfolio context into prompts.
"""


def inject_portfolio_context(user_prompt: str, portfolio_context: str = None) -> str:
    """
    Inject user's portfolio context into the prompt.
    
    Args:
        user_prompt: The original user prompt
        portfolio_context: Formatted portfolio data
        
    Returns:
        Enhanced prompt with portfolio context prepended
    """
    if not portfolio_context:
        return user_prompt
    
    # Prepend portfolio context to the prompt
    enhanced_prompt = f"""=== USER'S ZERODHA PORTFOLIO ===
{portfolio_context}

===================================

{user_prompt}"""
    
    return enhanced_prompt
