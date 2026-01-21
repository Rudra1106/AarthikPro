"""
Document Citation Formatter.

Formats citations for annual reports, concalls, and announcements
to be included in chatbot responses.
"""

from typing import List, Dict, Any, Optional


class CitationFormatter:
    """
    Formats document citations for Bloomberg-style responses.
    """
    
    @staticmethod
    def format_annual_reports(reports: List[Dict[str, Any]], limit: int = 3) -> str:
        """
        Format annual report citations.
        
        Args:
            reports: List of annual report dicts with year, url, source
            limit: Maximum number of reports to cite
        
        Returns:
            Formatted citation string
        """
        if not reports:
            return ""
        
        citations = "\n\n---\n**📄 Annual Reports:**\n"
        for report in reports[:limit]:
            year = report.get('year', 'N/A')
            url = report.get('url', '#')
            citations += f"- [{year} Annual Report]({url})\n"
        
        return citations
    
    @staticmethod
    def format_concalls(concalls: List[Dict[str, Any]], limit: int = 3) -> str:
        """
        Format concall citations.
        
        Args:
            concalls: List of concall dicts with date, transcript, ppt, rec
            limit: Maximum number of concalls to cite
        
        Returns:
            Formatted citation string
        """
        if not concalls:
            return ""
        
        citations = "\n\n---\n**📞 Concall Transcripts:**\n"
        for concall in concalls[:limit]:
            date = concall.get('date', 'N/A')
            transcript = concall.get('transcript')
            recording = concall.get('rec')
            
            if transcript:
                citations += f"- [{date} Transcript]({transcript})"
                if recording:
                    citations += f" | [Recording]({recording})"
                citations += "\n"
        
        return citations
    
    @staticmethod
    def format_announcements(announcements: List[Dict[str, Any]], limit: int = 3) -> str:
        """
        Format announcement citations.
        
        Args:
            announcements: List of announcement dicts with title, date, url
            limit: Maximum number of announcements to cite
        
        Returns:
            Formatted citation string
        """
        if not announcements:
            return ""
        
        citations = "\n\n---\n**📢 Recent Announcements:**\n"
        for ann in announcements[:limit]:
            title = ann.get('title', 'Announcement')[:60]  # Truncate long titles
            url = ann.get('url', '#')
            date = ann.get('date', '')
            
            # Extract just the date part if it's a long string
            if ' - ' in date:
                date = date.split(' - ')[0]
            
            citations += f"- [{title}...]({url}) - {date}\n"
        
        return citations
    
    @staticmethod
    def format_all_citations(
        reports: Optional[List[Dict]] = None,
        concalls: Optional[List[Dict]] = None,
        announcements: Optional[List[Dict]] = None
    ) -> str:
        """
        Format all available document citations.
        
        Args:
            reports: Annual reports
            concalls: Concall transcripts
            announcements: Recent announcements
        
        Returns:
            Combined formatted citations
        """
        citations = ""
        
        if reports:
            citations += CitationFormatter.format_annual_reports(reports)
        
        if concalls:
            citations += CitationFormatter.format_concalls(concalls)
        
        if announcements:
            citations += CitationFormatter.format_announcements(announcements)
        
        if citations:
            citations += "\n---\n"
        
        return citations


# Singleton instance
_citation_formatter: Optional[CitationFormatter] = None


def get_citation_formatter() -> CitationFormatter:
    """Get singleton citation formatter instance."""
    global _citation_formatter
    if _citation_formatter is None:
        _citation_formatter = CitationFormatter()
    return _citation_formatter
