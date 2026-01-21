"""
Table Extractor
Extracts tables from PDFs using camelot with LLM fallback.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    print("Warning: camelot-py not available. Table extraction will be limited.")


class TableExtractor:
    """Extract and normalize tables from PDF documents."""
    
    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm
        
    def extract(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of table chunks with metadata
        """
        if not CAMELOT_AVAILABLE:
            return []
        
        tables = []
        
        try:
            # Extract tables using camelot
            extracted_tables = camelot.read_pdf(
                pdf_path,
                pages='all',
                flavor='stream',  # Use stream for better detection
                edge_tol=50
            )
            
            for i, table in enumerate(extracted_tables):
                df = table.df
                
                # Skip empty tables
                if df.empty or df.shape[0] < 2:
                    continue
                
                # Calculate confidence
                confidence = table.parsing_report.get('accuracy', 0) / 100
                
                # Normalize table
                normalized_text = self._normalize_table(df, confidence)
                
                if normalized_text:
                    tables.append({
                        "type": "table",
                        "table_id": i,
                        "page": table.page,
                        "rows": df.shape[0],
                        "cols": df.shape[1],
                        "confidence": confidence,
                        "normalized_text": normalized_text,
                        "raw_table": df.to_dict('records')
                    })
        
        except Exception as e:
            print(f"Error extracting tables from {pdf_path}: {e}")
            return []
        
        return tables
    
    def _normalize_table(self, df: pd.DataFrame, confidence: float) -> str:
        """
        Normalize table to text format.
        
        Args:
            df: DataFrame containing table data
            confidence: Confidence score from camelot
            
        Returns:
            Normalized text representation
        """
        # Try rule-based normalization first
        normalized = self._rule_based_normalization(df)
        
        # If confidence is low and LLM is enabled, enhance with LLM
        if confidence < 0.7 and self.use_llm:
            from ..llm_client import get_llm_client
            llm_client = get_llm_client()
            
            llm_result = llm_client.normalize_table(normalized, confidence)
            if llm_result:
                normalized = llm_result
        
        return normalized
    
    def _rule_based_normalization(self, df: pd.DataFrame) -> str:
        """
        Rule-based table normalization.
        
        Args:
            df: DataFrame containing table data
            
        Returns:
            Normalized text
        """
        rows = []
        
        for _, row in df.iterrows():
            # Clean and join row values
            cleaned = [str(cell).strip() for cell in row.tolist() if str(cell).strip()]
            if cleaned:
                rows.append(", ".join(cleaned))
        
        # Join all rows
        text = " | ".join(rows)
        
        # Clean up
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
