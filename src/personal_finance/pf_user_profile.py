"""
Personal Finance User Profile Management

Minimal, safe user profile schema and CRUD operations.
Privacy-first: soft-confirm before saving, support forget/edit.
"""
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class PFUserProfile:
    """
    Minimal user profile for personal finance.
    
    Design principles:
    - Only decision-relevant info (no PAN, Aadhaar, bank details)
    - Partial profiles are normal
    - Derived fields computed dynamically, never stored
    """
    user_id: str
    
    # Financial data (optional)
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    emergency_fund_amount: Optional[float] = None
    
    # Demographics (optional)
    age: Optional[int] = None
    
    # Context (optional)
    income_type: str = "unknown"  # "salaried", "variable", "unknown"
    risk_tolerance: str = "unknown"  # "low", "medium", "high", "unknown"
    city_tier: str = "unknown"  # "tier1", "tier2", "tier3", "unknown"
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for MongoDB storage."""
        data = asdict(self)
        # Convert datetime to ISO string
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PFUserProfile":
        """Create from MongoDB dict."""
        # Parse datetime strings
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        return cls(**data)
    
    def is_empty(self) -> bool:
        """Check if profile has any financial data."""
        return (
            self.monthly_income is None and
            self.monthly_expenses is None and
            self.emergency_fund_amount is None and
            self.age is None
        )
    
    def get_missing_fields_for_action(self) -> list[str]:
        """Get missing fields required for PF_ACTION intent."""
        missing = []
        if self.monthly_income is None:
            missing.append("monthly_income")
        if self.monthly_expenses is None:
            missing.append("monthly_expenses")
        return missing
    
    def get_missing_fields_for_goal_planning(self) -> list[str]:
        """Get missing fields required for PF_GOAL_PLANNING intent."""
        # Goal planning needs income OR current savings
        # We'll ask for income if not available
        missing = []
        if self.monthly_income is None:
            missing.append("monthly_income")
        return missing


class PFUserProfileManager:
    """
    Manages PF user profiles with privacy-first approach.
    
    Features:
    - Soft-confirm before saving
    - Partial profile support
    - Forget/edit commands
    """
    
    def __init__(self, mongodb_client):
        """
        Initialize profile manager.
        
        Args:
            mongodb_client: MongoDB client instance
        """
        self.db = mongodb_client
        self.collection_name = "pf_user_profiles"
    
    def get_profile(self, user_id: str) -> PFUserProfile:
        """
        Get user profile from MongoDB.
        
        Args:
            user_id: User session ID
            
        Returns:
            PFUserProfile (empty if not found)
        """
        try:
            collection = self.db.get_collection(self.collection_name)
            data = collection.find_one({"user_id": user_id})
            
            if data:
                # Remove MongoDB _id field
                data.pop("_id", None)
                return PFUserProfile.from_dict(data)
            else:
                # Return empty profile
                return PFUserProfile(
                    user_id=user_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
        except Exception as e:
            logger.error(f"Error getting PF profile for {user_id}: {e}")
            return PFUserProfile(user_id=user_id)
    
    def save_profile(self, profile: PFUserProfile) -> bool:
        """
        Save user profile to MongoDB.
        
        Args:
            profile: PFUserProfile to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            profile.updated_at = datetime.now()
            if profile.created_at is None:
                profile.created_at = datetime.now()
            
            collection = self.db.get_collection(self.collection_name)
            collection.replace_one(
                {"user_id": profile.user_id},
                profile.to_dict(),
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error saving PF profile for {profile.user_id}: {e}")
            return False
    
    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in user profile.
        
        Rule: Only update if value is not None (never overwrite with guesses).
        
        Args:
            user_id: User session ID
            updates: Dict of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get existing profile
            profile = self.get_profile(user_id)
            
            # Update only non-None values
            for key, value in updates.items():
                if value is not None and hasattr(profile, key):
                    setattr(profile, key, value)
            
            # Save updated profile
            return self.save_profile(profile)
        except Exception as e:
            logger.error(f"Error updating PF profile for {user_id}: {e}")
            return False
    
    def delete_profile(self, user_id: str) -> bool:
        """
        Delete user profile (for "forget my data" command).
        
        Args:
            user_id: User session ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.db.get_collection(self.collection_name)
            result = collection.delete_one({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting PF profile for {user_id}: {e}")
            return False
    
    def extract_profile_data_from_message(self, message: str) -> Dict[str, Any]:
        """
        Extract profile data from user message.
        
        Examples:
        - "I earn 50k per month" → {"monthly_income": 50000}
        - "My expenses are 30k" → {"monthly_expenses": 30000}
        - "I'm 25 years old" → {"age": 25}
        
        Args:
            message: User message
            
        Returns:
            Dict of extracted profile data
        """
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
                # Convert k to actual amount
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
        
        # Extract age
        age_patterns = [
            r'(?:i\'?m|i am|age|aged).*?(\d{2})\s*(?:years?|yrs?)?',
            r'(\d{2})\s*(?:years?|yrs?)\s*old',
        ]
        for pattern in age_patterns:
            match = re.search(pattern, message_lower)
            if match:
                age = int(match.group(1))
                if 18 <= age <= 100:  # Sanity check
                    extracted["age"] = age
                break
        
        # Extract emergency fund
        ef_patterns = [
            r'(?:emergency fund|savings).*?(\d+)(?:k|000|\s*thousand|\s*lakh)',
        ]
        for pattern in ef_patterns:
            match = re.search(pattern, message_lower)
            if match:
                amount = int(match.group(1))
                if 'lakh' in message_lower:
                    amount *= 100000
                elif 'k' in message_lower or 'thousand' in message_lower:
                    amount *= 1000
                extracted["emergency_fund_amount"] = float(amount)
                break
        
        return extracted


def get_pf_profile_manager(mongodb_client) -> PFUserProfileManager:
    """
    Get PF profile manager instance.
    
    Args:
        mongodb_client: MongoDB client instance
        
    Returns:
        PFUserProfileManager instance
    """
    return PFUserProfileManager(mongodb_client)
