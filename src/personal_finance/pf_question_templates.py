"""
Personal Finance Question Templates

Progressive disclosure: Never block users upfront.
Earn the right to ask questions based on intent.

UX Principle: "If you're comfortable sharing..." not "I can't answer without..."
"""
from typing import List, Dict, Any
from .pf_intent_classifier import PFIntent


class PFQuestionTemplates:
    """
    Question templates for progressive disclosure.
    
    Design:
    - PF_EDUCATION: Ask nothing
    - PF_EVALUATION: Optional personalization invite
    - PF_ACTION: Minimal mandatory questions (income + expenses)
    - PF_GOAL_PLANNING: Math-required fields only
    - PF_MARKET_CONTEXT: Single clarifier
    """
    
    # Soft, inviting language (never demanding)
    OPTIONAL_PERSONALIZATION_INVITE = (
        "I can give you a general answer, or tailor it to your situation if you'd like. "
        "Would you like personalized guidance?"
    )
    
    SOFT_CONFIRMATION = (
        "Got it — I'll remember this to personalize future advice. "
        "You can ask me to forget or update this anytime."
    )
    
    @staticmethod
    def get_questions_for_intent(
        intent: PFIntent,
        missing_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Get questions to ask based on intent and missing profile fields.
        
        Args:
            intent: PF intent type
            missing_fields: List of missing profile fields
            
        Returns:
            Dict with:
                - questions: List of question strings
                - is_optional: Whether questions are optional
                - explanation: Why we're asking
        """
        if intent == PFIntent.PF_EDUCATION:
            # No questions for education
            return {
                "questions": [],
                "is_optional": True,
                "explanation": None
            }
        
        elif intent == PFIntent.PF_EVALUATION:
            # Optional personalization
            if missing_fields:
                return {
                    "questions": [PFQuestionTemplates.OPTIONAL_PERSONALIZATION_INVITE],
                    "is_optional": True,
                    "explanation": "I can provide a more tailored answer if you share a bit about your situation."
                }
            return {
                "questions": [],
                "is_optional": True,
                "explanation": None
            }
        
        elif intent == PFIntent.PF_ACTION:
            # Mandatory minimal questions
            questions = []
            
            if "monthly_income" in missing_fields:
                questions.append("What is your monthly income (take-home)?")
            
            if "monthly_expenses" in missing_fields:
                questions.append("What are your monthly expenses?")
            
            if questions:
                intro = (
                    "To answer this responsibly, I need to understand your cash flow. "
                    "This helps me ensure the advice is safe for your situation."
                )
                return {
                    "questions": questions,
                    "is_optional": False,
                    "explanation": intro
                }
            
            return {
                "questions": [],
                "is_optional": False,
                "explanation": None
            }
        
        elif intent == PFIntent.PF_GOAL_PLANNING:
            # Math-required fields
            questions = []
            
            if "monthly_income" in missing_fields:
                questions.append("What is your monthly income or current monthly savings?")
            
            # Goal-specific questions (extracted from query separately)
            # These are handled in the graph node
            
            if questions:
                intro = "I can calculate this exactly. Let me understand your current situation:"
                return {
                    "questions": questions,
                    "is_optional": False,
                    "explanation": intro
                }
            
            return {
                "questions": [],
                "is_optional": False,
                "explanation": None
            }
        
        elif intent == PFIntent.PF_MARKET_CONTEXT:
            # Single clarifier
            questions = []
            
            # Check if we need to know time horizon
            if "time_horizon" in missing_fields:
                questions.append("Are you investing for the long term (5+ years)?")
            
            if questions:
                return {
                    "questions": questions,
                    "is_optional": True,
                    "explanation": "This helps me give you context-appropriate advice."
                }
            
            return {
                "questions": [],
                "is_optional": True,
                "explanation": None
            }
        
        # Default: no questions
        return {
            "questions": [],
            "is_optional": True,
            "explanation": None
        }
    
    @staticmethod
    def format_question_message(
        questions_data: Dict[str, Any]
    ) -> str:
        """
        Format questions into a conversational message.
        
        Args:
            questions_data: Output from get_questions_for_intent
            
        Returns:
            Formatted question message
        """
        if not questions_data["questions"]:
            return ""
        
        parts = []
        
        # Add explanation if present
        if questions_data["explanation"]:
            parts.append(questions_data["explanation"])
        
        # Add questions
        questions = questions_data["questions"]
        if len(questions) == 1:
            parts.append(questions[0])
        else:
            parts.append("\n".join(f"{i+1}. {q}" for i, q in enumerate(questions)))
        
        # Add optional note if applicable
        if questions_data["is_optional"]:
            parts.append("\n*(This is optional, but helps me personalize my response)*")
        
        return "\n\n".join(parts)
    
    @staticmethod
    def get_soft_confirmation_message(extracted_data: Dict[str, Any]) -> str:
        """
        Generate soft confirmation message after extracting user data.
        
        Args:
            extracted_data: Dict of extracted profile data
            
        Returns:
            Confirmation message
        """
        if not extracted_data:
            return ""
        
        # Format extracted data
        data_summary = []
        if "monthly_income" in extracted_data:
            data_summary.append(f"Monthly income: ₹{extracted_data['monthly_income']:,.0f}")
        if "monthly_expenses" in extracted_data:
            data_summary.append(f"Monthly expenses: ₹{extracted_data['monthly_expenses']:,.0f}")
        if "age" in extracted_data:
            data_summary.append(f"Age: {extracted_data['age']}")
        if "emergency_fund_amount" in extracted_data:
            data_summary.append(f"Emergency fund: ₹{extracted_data['emergency_fund_amount']:,.0f}")
        
        if not data_summary:
            return ""
        
        summary_text = ", ".join(data_summary)
        
        return (
            f"Thanks! I've noted: {summary_text}.\n\n"
            f"{PFQuestionTemplates.SOFT_CONFIRMATION}"
        )


# UX Copy Library (for consistent messaging)
class PFUXCopy:
    """Consistent UX copy for PF chatbot."""
    
    # Privacy messages
    PRIVACY_FIRST = (
        "🔒 **Privacy First**: I only ask for information needed to help you. "
        "You can ask me to forget your data anytime."
    )
    
    FORGET_DATA_CONFIRMATION = (
        "I've deleted all your financial data. "
        "Feel free to share again if you'd like personalized advice in the future."
    )
    
    UPDATE_DATA_CONFIRMATION = "Updated! I'll use this for future advice."
    
    # Compliance messages
    NOT_FINANCIAL_ADVICE = (
        "*This is educational guidance, not financial advice. "
        "Please consult a certified financial advisor for personalized recommendations.*"
    )
    
    # Encouraging messages
    GOOD_START = "Great question! Let me help you understand this."
    
    BUILDING_FOUNDATION = (
        "You're taking the right first step by understanding this. "
        "Financial literacy is the foundation of wealth building."
    )
    
    # Gentle warnings (not refusals)
    MISSING_DATA_GENTLE = (
        "I can give you a general answer, but for personalized guidance, "
        "I'd need to know a bit about your financial situation."
    )
    
    SAFETY_FIRST = (
        "Before we discuss investments, let's make sure your financial foundation is solid. "
        "This protects you from taking unnecessary risks."
    )
