"""
Personal Finance Graph Nodes

LangGraph nodes for PF chatbot flow.
"""
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI

from ..pf_intent_classifier import get_pf_intent_classifier, PFIntent
from ..pf_user_profile import get_pf_profile_manager
from ..pf_rules_engine import get_pf_rules_engine
from ..pf_question_templates import PFQuestionTemplates, PFUXCopy
from ..pf_prompts import PFPrompts, COMPLIANCE_FOOTER
from .pf_state import PFChatState

from src.config import settings
from src.data.mongo_client import get_mongo_client

logger = logging.getLogger(__name__)


def classify_pf_intent_node(state: PFChatState) -> Dict[str, Any]:
    """
    Classify PF intent from user query.
    
    Returns:
        Updated state with intent classification
    """
    query = state["query"]
    
    # Get classifier
    classifier = get_pf_intent_classifier()
    
    # Classify
    classification = classifier.classify(query)
    
    logger.info(f"PF Intent: {classification.intent.value}, Confidence: {classification.confidence:.2f}, Personalization: {classification.personalization_level}")
    
    return {
        "pf_intent": classification.intent.value,
        "intent_confidence": classification.confidence,
        "personalization_level": classification.personalization_level
    }


def check_user_profile_node(state: PFChatState) -> Dict[str, Any]:
    """
    Load user profile from MongoDB.
    
    Returns:
        Updated state with user profile
    """
    user_id = state["user_id"]
    pf_intent = state["pf_intent"]
    
    # Get MongoDB client
    mongo_client = get_mongo_client()
    
    # For now, create empty profile (will implement MongoDB storage later)
    # This allows the system to work without MongoDB dependency initially
    from ..pf_user_profile import PFUserProfile
    from datetime import datetime
    
    profile = PFUserProfile(
        user_id=user_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Determine missing fields based on intent
    missing_fields = []
    if pf_intent == PFIntent.PF_ACTION.value:
        missing_fields = profile.get_missing_fields_for_action()
    elif pf_intent == PFIntent.PF_GOAL_PLANNING.value:
        missing_fields = profile.get_missing_fields_for_goal_planning()
    
    logger.info(f"Profile loaded for {user_id}. Empty: {profile.is_empty()}, Missing fields: {missing_fields}")
    
    return {
        "user_profile": profile.to_dict(),
        "profile_is_empty": profile.is_empty(),
        "missing_fields": missing_fields
    }


def determine_questions_node(state: PFChatState) -> Dict[str, Any]:
    """
    Determine if we need to ask questions based on intent and profile.
    
    Returns:
        Updated state with questions (if needed)
    """
    pf_intent = state["pf_intent"]
    missing_fields = state.get("missing_fields", [])
    personalization_level = state["personalization_level"]
    
    # Get questions for this intent
    try:
        intent_enum = PFIntent(pf_intent)
    except ValueError:
        intent_enum = PFIntent.PF_EDUCATION
    
    questions_data = PFQuestionTemplates.get_questions_for_intent(
        intent_enum,
        missing_fields
    )
    
    needs_questions = len(questions_data["questions"]) > 0
    
    logger.info(f"Questions needed: {needs_questions}, Count: {len(questions_data['questions'])}")
    
    return {
        "needs_questions": needs_questions,
        "questions_to_ask": questions_data["questions"],
        "questions_explanation": questions_data.get("explanation"),
        "waiting_for_user_input": needs_questions and not questions_data["is_optional"]
    }


def run_rules_engine_node(state: PFChatState) -> Dict[str, Any]:
    """
    Run rules engine if intent requires it (PF_ACTION, PF_GOAL_PLANNING).
    
    Returns:
        Updated state with rules output
    """
    pf_intent = state["pf_intent"]
    user_profile = state.get("user_profile", {})
    
    # Only run for intents that need it
    if pf_intent not in [PFIntent.PF_ACTION.value, PFIntent.PF_GOAL_PLANNING.value]:
        return {"rules_output": None}
    
    # Get rules engine
    rules_engine = get_pf_rules_engine()
    
    # Run rules
    rules_result = rules_engine.run(user_profile)
    
    logger.info(f"Rules engine output: Investment ready: {rules_result.investment_ready}, Warnings: {len(rules_result.warnings)}, Blockers: {len(rules_result.blockers)}")
    
    return {
        "rules_output": rules_result.to_dict()
    }


def synthesize_pf_response_node(state: PFChatState) -> Dict[str, Any]:
    """
    Synthesize final response using LLM with safety prompts.
    
    Returns:
        Updated state with response
    """
    query = state["query"]
    pf_intent = state["pf_intent"]
    user_profile = state.get("user_profile", {})
    rules_output = state.get("rules_output")
    needs_questions = state.get("needs_questions", False)
    questions_to_ask = state.get("questions_to_ask", [])
    questions_explanation = state.get("questions_explanation")
    
    # If we need to ask questions first, return question message
    if needs_questions and questions_to_ask:
        questions_data = {
            "questions": questions_to_ask,
            "is_optional": state["personalization_level"] == "optional",
            "explanation": questions_explanation
        }
        question_message = PFQuestionTemplates.format_question_message(questions_data)
        
        return {
            "response": question_message,
            "waiting_for_user_input": True
        }
    
    # Get prompt for intent
    try:
        intent_enum = PFIntent(pf_intent)
    except ValueError:
        intent_enum = PFIntent.PF_EDUCATION
    
    prompt = PFPrompts.get_prompt_for_intent(
        intent_enum,
        query,
        user_profile,
        rules_output,
        context=state.get("market_context")
    )
    
    # Call LLM with OpenRouter (matching existing chatbot configuration)
    try:
        llm = ChatOpenAI(
            model=settings.default_model,  # "openai/gpt-4o-mini"
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0.3,  # Lower temperature for financial advice
            max_tokens=1000
        )
        
        response = llm.invoke(prompt)
        response_text = response.content
        
        # Add compliance footer
        response_text += COMPLIANCE_FOOTER
        
        logger.info(f"Generated PF response, length: {len(response_text)}")
        
        return {
            "response": response_text,
            "waiting_for_user_input": False
        }
        
    except Exception as e:
        logger.error(f"Error generating PF response: {e}")
        
        # INTELLIGENT FALLBACK: Provide educational response for PF_EDUCATION queries
        # Never show technical errors to users
        if intent_enum == PFIntent.PF_EDUCATION:
            fallback_response = get_education_fallback(query)
            return {
                "response": fallback_response + COMPLIANCE_FOOTER,
                "waiting_for_user_input": False
            }
        
        # For other intents, provide helpful guidance
        fallback_response = """I'm having trouble generating a detailed response right now, but let me help you with some general guidance.

**For investing questions:**
- Start with understanding your financial goals (short-term vs long-term)
- Build an emergency fund first (6 months of expenses)
- Consider your risk tolerance and time horizon
- Diversification is key to managing risk

**For mutual fund questions:**
- Mutual funds pool money from many investors
- They're managed by professionals
- Index funds and large-cap funds are good for beginners
- SIPs (monthly investments) help average out market volatility

Would you like me to explain any specific concept in more detail?

---
*This is educational guidance, not financial advice. Please consult a certified financial advisor for personalized recommendations.*"""
        
        return {
            "response": fallback_response,
            "waiting_for_user_input": False
        }


def get_education_fallback(query: str) -> str:
    """
    Provide intelligent fallback educational responses.
    
    This ensures users always get helpful guidance even if LLM fails.
    """
    query_lower = query.lower()
    
    # Mutual fund queries
    if any(kw in query_lower for kw in ["mutual fund", "mf", "sip"]):
        if "3000" in query or "small amount" in query_lower or "new" in query_lower or "beginner" in query_lower:
            return """That's a great starting amount 👍

Investing ₹3,000 is perfectly fine when you're new to mutual funds.

**First, a quick reassurance:**
Mutual funds are a good way to start because they are diversified. You don't need large capital or deep market knowledge.

**🧠 As a beginner, focus on learning + safety**

Instead of picking a "complex" fund, beginners usually start with:
- **Index Funds** (track the market like Nifty 50)
- **Large-cap diversified funds** (invest in established companies)

These are simpler and lower-risk compared to sector or thematic funds.

**📌 How you can start safely:**
1. Start with a **monthly SIP of ₹3,000** (instead of investing all at once)
2. Think **long-term (5+ years)** — short-term ups and downs are normal
3. Don't worry about daily market movements
4. Focus on consistency over timing

**⚠️ Important to know:**
- Mutual funds can go up and down in the short term
- There are no guaranteed returns
- Staying invested matters more than timing the market
- Build an emergency fund alongside (for unexpected expenses)

**Next steps:**
- Learn about SIPs (Systematic Investment Plans)
- Understand the difference between equity and debt funds
- Check if you have an emergency fund (recommended: 6 months of expenses)

If you want, I can help you understand:
- How SIPs work in simple terms
- The difference between index funds and actively managed funds
- How to choose the right type of fund based on your goals"""
        
        return """**Mutual funds** are investment vehicles that pool money from many investors to invest in stocks, bonds, or other securities.

**Key benefits:**
- **Professional management**: Experts manage your money
- **Diversification**: Your money is spread across many investments
- **Accessibility**: Start with small amounts (as low as ₹500)
- **Liquidity**: Can withdraw when needed (with some conditions)

**Types of mutual funds:**
1. **Equity funds**: Invest in stocks (higher risk, higher potential returns)
2. **Debt funds**: Invest in bonds (lower risk, stable returns)
3. **Hybrid funds**: Mix of equity and debt

**For beginners:**
- Start with **index funds** or **large-cap funds**
- Use **SIP (Systematic Investment Plan)** for monthly investments
- Think long-term (5+ years minimum)
- Don't chase past returns

**Important considerations:**
- Build an emergency fund first
- Understand your risk tolerance
- Know your investment goals (retirement, house, education)
- Diversify across fund types

Would you like to know more about SIPs, or how to choose the right fund type for your goals?"""
    
    # Emergency fund queries
    if "emergency fund" in query_lower:
        return """**Emergency fund** is money set aside specifically for unexpected expenses.

**Why it's important:**
- Medical emergencies
- Job loss
- Urgent home/vehicle repairs
- Prevents you from selling investments at a loss

**How much to save:**
- **Salaried individuals**: 6 months of expenses
- **Self-employed/variable income**: 12 months of expenses

**Where to keep it:**
- Savings account
- Liquid mutual funds
- Fixed deposits (with easy withdrawal)

**Key principle**: Should be easily accessible (liquid) and safe (low risk)

**Example:**
If your monthly expenses are ₹30,000:
- Target emergency fund = ₹1,80,000 (6 months)
- Start by saving ₹10,000/month
- Will take ~18 months to build

**Build it BEFORE aggressive investing** — this is your financial safety net."""
    
    # SIP queries
    if "sip" in query_lower:
        return """**SIP (Systematic Investment Plan)** is a method of investing a fixed amount regularly in mutual funds.

**How it works:**
- Invest a fixed amount monthly (e.g., ₹3,000)
- Money is automatically deducted from your bank
- Units are purchased at current market price
- Over time, you accumulate units

**Key benefits:**
1. **Rupee cost averaging**: Buy more units when prices are low, fewer when high
2. **Discipline**: Automates investing, removes emotion
3. **Compounding**: Returns generate more returns over time
4. **Flexibility**: Start/stop/increase anytime

**Example:**
- Monthly SIP: ₹5,000
- Duration: 10 years
- Assumed return: 12% p.a.
- Approximate corpus: ₹11.5 lakhs (you invested ₹6 lakhs)

**Best practices:**
- Start early (time is your biggest advantage)
- Stay consistent (don't stop during market falls)
- Increase SIP with salary hikes
- Review annually, don't check daily

**Perfect for:**
- Salaried individuals
- Long-term goals (5+ years)
- Beginners who want discipline"""
    
    # Default fallback
    return """I'd be happy to help you understand personal finance concepts!

**Popular topics I can explain:**
- **Mutual funds**: What they are and how they work
- **SIP**: Systematic Investment Plans for regular investing
- **Emergency fund**: Building your financial safety net
- **Equity vs Debt**: Understanding risk and returns
- **Index funds**: Simple, low-cost investing
- **Financial goals**: Planning for retirement, house, education

**For personalized guidance**, I can help you with:
- How much to invest based on your income
- Building a financial plan for specific goals
- Understanding if a strategy suits your situation

What would you like to learn about?"""


def extract_and_save_profile_data_node(state: PFChatState) -> Dict[str, Any]:
    """
    Extract profile data from user's message.
    
    This node is called when user provides data in response to questions.
    For now, just extracts data without saving to MongoDB.
    
    Returns:
        Updated state with extracted data
    """
    query = state["query"]
    user_id = state["user_id"]
    
    # Import profile manager utilities
    from ..pf_user_profile import PFUserProfileManager
    
    # Create a temporary instance just for extraction
    class TempProfileManager:
        def extract_profile_data_from_message(self, message: str) -> Dict[str, Any]:
            import re
            extracted = {}
            message_lower = message.lower()
            
            # Extract income
            income_patterns = [
                r'(?:earn|income|salary|make).*?(\d+)(?:k|000|\s*thousand)',
                r'(\d+)(?:k|000|\s*thousand).*?(?:income|salary|per month|monthly)',
            ]
            for pattern in income_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    amount = int(match.group(1))
                    if 'k' in message_lower or 'thousand' in message_lower:
                        amount *= 1000
                    extracted["monthly_income"] = float(amount)
                    break
            
            # Extract expenses
            expense_patterns = [
                r'(?:expenses?|spend|spending).*?(\d+)(?:k|000|\s*thousand)',
                r'(\d+)(?:k|000|\s*thousand).*?(?:expenses?|spending|per month)',
            ]
            for pattern in expense_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    amount = int(match.group(1))
                    if 'k' in message_lower or 'thousand' in message_lower:
                        amount *= 1000
                    extracted["monthly_expenses"] = float(amount)
                    break
            
            return extracted
    
    temp_manager = TempProfileManager()
    extracted_data = temp_manager.extract_profile_data_from_message(query)
    
    if extracted_data:
        logger.info(f"Extracted data for {user_id}: {list(extracted_data.keys())}")
        
        # Generate soft confirmation
        from ..pf_question_templates import PFQuestionTemplates
        confirmation = PFQuestionTemplates.get_soft_confirmation_message(extracted_data)
        
        return {
            "extracted_data": extracted_data,
            "response": confirmation
        }
    
    return {
        "extracted_data": {},
        "response": None
    }
