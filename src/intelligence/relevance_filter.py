"""
Relevance Filter - Filter out irrelevant data before LLM.

Rule: Before sending to LLM, filter OUT irrelevant data.

If data is N/A for a RELEVANT section → omit the section
If section is FORBIDDEN for blueprint → remove entirely
If data exists but IRRELEVANT → don't show
"""
from typing import Dict, Any, List, Optional
import logging

from src.intelligence.answer_blueprints import AnswerBlueprint, Section

logger = logging.getLogger(__name__)


class RelevanceFilter:
    """
    Filter out data not relevant to the question.
    
    This is critical for focused responses. The LLM should only
    see data that's relevant to the specific question type.
    """
    
    def filter(
        self,
        data: Dict[str, Any],
        blueprint: AnswerBlueprint
    ) -> Dict[str, Any]:
        """
        Filter data based on blueprint.
        
        Args:
            data: All available data
            blueprint: Answer blueprint with section rules
            
        Returns:
            Filtered data with only relevant sections
        """
        filtered = {}
        omitted_sections = []
        
        for section, content in data.items():
            # Skip forbidden sections
            if self._is_forbidden(section, blueprint):
                omitted_sections.append(f"{section} (forbidden)")
                continue
            
            # Skip if no meaningful data
            if self._is_empty(content):
                if section in [s.value for s in blueprint.required_sections]:
                    # Required but empty - note it but don't show "Data unavailable"
                    omitted_sections.append(f"{section} (no data)")
                continue
            
            # Check if section is relevant
            if self._is_relevant(section, blueprint):
                filtered[section] = content
            else:
                omitted_sections.append(f"{section} (not relevant)")
        
        # Log what was omitted
        if omitted_sections:
            logger.debug(f"Omitted sections: {', '.join(omitted_sections)}")
        
        # Add metadata about filtering
        filtered["_filter_metadata"] = {
            "omitted_count": len(omitted_sections),
            "included_count": len(filtered) - 1,  # Exclude metadata itself
            "blueprint_type": blueprint.question_type.value
        }
        
        return filtered
    
    def _is_forbidden(self, section: str, blueprint: AnswerBlueprint) -> bool:
        """Check if section is forbidden by blueprint."""
        forbidden = [s.value if isinstance(s, Section) else s for s in blueprint.forbidden_sections]
        return section in forbidden
    
    def _is_relevant(self, section: str, blueprint: AnswerBlueprint) -> bool:
        """Check if section is relevant to blueprint."""
        required = [s.value if isinstance(s, Section) else s for s in blueprint.required_sections]
        optional = [s.value if isinstance(s, Section) else s for s in blueprint.optional_sections]
        
        return section in required or section in optional
    
    def _is_empty(self, content: Any) -> bool:
        """Check if content is empty or placeholder."""
        if content is None:
            return True
        if isinstance(content, str):
            empty_values = ["", "data unavailable", "n/a", "none", "null"]
            return content.lower().strip() in empty_values
        if isinstance(content, dict):
            return len(content) == 0
        if isinstance(content, list):
            return len(content) == 0
        return False
    
    def prepare_for_llm(
        self,
        filtered_data: Dict[str, Any],
        blueprint: AnswerBlueprint,
        question: str
    ) -> str:
        """
        Prepare filtered data as context for LLM.
        
        Args:
            filtered_data: Already filtered data
            blueprint: Answer blueprint
            question: Original question
            
        Returns:
            Formatted context string for LLM
        """
        context_parts = []
        
        # Add focus instruction
        context_parts.append(f"QUESTION: {question}")
        context_parts.append(f"QUESTION TYPE: {blueprint.question_type.value}")
        context_parts.append(f"FOCUS: {blueprint.prompt_focus}")
        context_parts.append("")
        context_parts.append("AVAILABLE DATA:")
        context_parts.append("-" * 40)
        
        # Add each section with clear labels
        for section, content in filtered_data.items():
            if section.startswith("_"):  # Skip metadata
                continue
            
            section_label = section.upper().replace("_", " ")
            context_parts.append(f"\n[{section_label}]")
            
            if isinstance(content, dict):
                for key, value in content.items():
                    if not self._is_empty(value):
                        context_parts.append(f"  {key}: {value}")
            elif isinstance(content, list):
                for item in content[:5]:  # Limit to top 5
                    if isinstance(item, dict):
                        item_str = ", ".join([f"{k}: {v}" for k, v in item.items()])
                        context_parts.append(f"  - {item_str}")
                    else:
                        context_parts.append(f"  - {item}")
            else:
                context_parts.append(f"  {content}")
        
        context_parts.append("-" * 40)
        context_parts.append("")
        context_parts.append("FORBIDDEN (DO NOT INCLUDE IN RESPONSE):")
        for section in blueprint.forbidden_sections:
            section_name = section.value if isinstance(section, Section) else section
            context_parts.append(f"  - {section_name.replace('_', ' ').title()}")
        
        return "\n".join(context_parts)
    
    def get_missing_required_data(
        self,
        filtered_data: Dict[str, Any],
        blueprint: AnswerBlueprint
    ) -> List[str]:
        """
        Get list of required sections that are missing.
        
        Args:
            filtered_data: Filtered data
            blueprint: Answer blueprint
            
        Returns:
            List of missing required section names
        """
        required = [s.value if isinstance(s, Section) else s for s in blueprint.required_sections]
        available = set(filtered_data.keys())
        
        missing = []
        for section in required:
            if section not in available or self._is_empty(filtered_data.get(section)):
                missing.append(section)
        
        return missing


# Singleton
_relevance_filter: Optional[RelevanceFilter] = None


def get_relevance_filter() -> RelevanceFilter:
    """Get singleton relevance filter."""
    global _relevance_filter
    if _relevance_filter is None:
        _relevance_filter = RelevanceFilter()
    return _relevance_filter
