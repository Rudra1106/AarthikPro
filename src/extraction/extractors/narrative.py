"""
Narrative Text Extractor
Extracts narrative text from PDFs using pdfplumber.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
import pdfplumber


class NarrativeExtractor:
    """Extract narrative text from PDF documents."""
    
    def __init__(self):
        self.min_text_length = 200  # Minimum characters for a valid chunk
        
    def extract(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract narrative text from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of narrative chunks with metadata
        """
        chunks = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text()
                    
                    if not text:
                        continue
                    
                    # Clean text
                    text = self._clean_text(text)
                    
                    # Skip if too short
                    if len(text) < self.min_text_length:
                        continue
                    
                    chunks.append({
                        "type": "narrative",
                        "page": page_num,
                        "text": text,
                        "char_count": len(text),
                        "word_count": len(text.split())
                    })
        
        except Exception as e:
            print(f"Error extracting narrative from {pdf_path}: {e}")
            return []
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers (common patterns)
        text = re.sub(r'Page\s+\d+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Remove common headers/footers
        text = re.sub(r'Annual Report \d{4}', '', text, flags=re.IGNORECASE)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
