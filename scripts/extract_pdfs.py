#!/usr/bin/env python3
"""
PDF Extraction Script
Extracts data from annual report PDFs and stores in MongoDB + Pinecone.

Usage:
    python scripts/extract_pdfs.py --chunk-number 0
    python scripts/extract_pdfs.py --chunk-number 0 --chunk-size 10
    python scripts/extract_pdfs.py --test  # Test with 1 PDF
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction.extractors import NarrativeExtractor, TableExtractor, VerticalDetector
from src.extraction.embeddings import OpenAIEmbeddingGenerator
from src.extraction.storage import MongoDBStorage, PineconeStorage
from src.extraction.llm_client import get_llm_client
from src.extraction.temperature_rules import classify_temperature, should_index_in_pinecone
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()


class ExtractionStats:
    """Track extraction statistics."""
    
    def __init__(self):
        self.total_pdfs = 0
        self.successful = 0
        self.failed = 0
        self.narrative_chunks = 0
        self.vertical_chunks = 0
        self.table_chunks = 0
        self.hot_data_count = 0
        self.pinecone_vectors = 0
        self.start_time = time.time()
    
    def summary(self) -> str:
        """Generate summary report."""
        duration = time.time() - self.start_time
        
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                  EXTRACTION SUMMARY                          ║
╚══════════════════════════════════════════════════════════════╝

📊 PDFs Processed:           {self.total_pdfs}
✅ Successful:               {self.successful}
❌ Failed:                   {self.failed}

📄 Chunks Extracted:
   Narrative:                {self.narrative_chunks}
   Vertical:                 {self.vertical_chunks}
   Table:                    {self.table_chunks}
   Total:                    {self.narrative_chunks + self.vertical_chunks + self.table_chunks}

🔥 Hot Data:                 {self.hot_data_count} documents
📌 Pinecone Vectors:         {self.pinecone_vectors}

⏱️  Duration:                 {duration:.1f}s
⚡ Avg per PDF:              {duration/self.total_pdfs:.1f}s (if self.total_pdfs > 0)

Success Rate: {(self.successful/self.total_pdfs*100) if self.total_pdfs > 0 else 0:.1f}%
"""


def get_chunk_isins(chunk_number: int, chunk_size: int) -> List[Dict[str, Any]]:
    """
    Get ISINs for a specific chunk from MongoDB.
    
    Args:
        chunk_number: Chunk number (0-indexed)
        chunk_size: Number of stocks per chunk
        
    Returns:
        List of stock documents with ISIN and metadata
    """
    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_database = os.getenv("MONGODB_DATABASE", "PORTFOLIO_MANAGER")
    
    client = MongoClient(mongodb_uri)
    db = client[mongodb_database]
    
    # Get stocks sorted by ISIN
    skip_count = chunk_number * chunk_size
    
    stocks = list(db.stock_documents.find(
        {},
        {"isin": 1, "company_name": 1, "annual_reports": 1}
    ).sort("isin", 1).skip(skip_count).limit(chunk_size))
    
    client.close()
    
    return stocks


def find_pdf_for_stock(isin: str, base_dir: Path = Path("data/annual_reports")) -> List[Path]:
    """
    Find all PDF files for a given ISIN.
    
    Args:
        isin: Stock ISIN
        base_dir: Base directory for PDFs
        
    Returns:
        List of PDF paths
    """
    stock_dir = base_dir / isin
    if not stock_dir.exists():
        return []
    
    return list(stock_dir.glob("*.pdf"))


def extract_fiscal_year_from_filename(pdf_path: Path) -> int:
    """Extract fiscal year from PDF filename (e.g., 2024.pdf -> 2024)."""
    try:
        return int(pdf_path.stem)
    except:
        return 2024  # Default


def process_pdf(
    pdf_path: Path,
    isin: str,
    company_name: str,
    fiscal_year: int,
    extractors: Dict,
    embedding_gen: OpenAIEmbeddingGenerator,
    mongo_storage: MongoDBStorage,
    pinecone_storage: PineconeStorage,
    stats: ExtractionStats
) -> bool:
    """
    Process a single PDF file.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        start_time = time.time()
        
        # Classify temperature
        temperature = classify_temperature(fiscal_year)
        
        # Store document metadata
        with pdfplumber.open(pdf_path) as pdf:
            pages = len(pdf.pages)
        
        doc_id = mongo_storage.store_document_metadata(
            isin=isin,
            company_name=company_name,
            fiscal_year=fiscal_year,
            pdf_path=str(pdf_path),
            pages=pages,
            temperature=temperature
        )
        
        # Extract narrative (always needed for text search)
        print(f"  Extracting narrative...")
        narrative_chunks = extractors['narrative'].extract(str(pdf_path))
        stats.narrative_chunks += len(narrative_chunks)
        
        # Only process verticals and tables for HOT data
        vertical_chunks = []
        table_chunks = []
        
        if should_index_in_pinecone(temperature):
            # Detect verticals (hot data only)
            print(f"  🔥 Hot data - Detecting verticals...")
            vertical_chunks = extractors['vertical'].detect(narrative_chunks)
            stats.vertical_chunks += len(vertical_chunks)
            
            # Extract tables (hot data only)
            print(f"  🔥 Hot data - Extracting tables...")
            table_chunks = extractors['table'].extract(str(pdf_path))
            stats.table_chunks += len(table_chunks)
        else:
            print(f"  ❄️  {temperature.capitalize()} data - Skipping vertical/table extraction")
        
        # Store in MongoDB
        print(f"  Storing in MongoDB...")
        all_text_chunks = narrative_chunks + vertical_chunks
        mongo_storage.store_text_chunks(
            doc_id, isin, company_name, fiscal_year, all_text_chunks, temperature
        )
        if table_chunks:  # Only store if we extracted tables
            mongo_storage.store_table_chunks(
                doc_id, isin, company_name, fiscal_year, table_chunks, temperature
            )
        
        # Generate embeddings and upload to Pinecone (hot data only)
        if should_index_in_pinecone(temperature):
            print(f"  🔥 Generating embeddings...")
            stats.hot_data_count += 1
            
            # Generate embeddings
            narrative_with_emb = embedding_gen.generate(narrative_chunks, "narrative")
            vertical_with_emb = embedding_gen.generate(vertical_chunks, "vertical")
            table_with_emb = embedding_gen.generate(table_chunks, "table")
            
            # Upload to Pinecone
            print(f"  📌 Uploading to Pinecone...")
            stats.pinecone_vectors += pinecone_storage.upload_chunks(
                narrative_with_emb, "narrative", isin, company_name, fiscal_year
            )
            stats.pinecone_vectors += pinecone_storage.upload_chunks(
                vertical_with_emb, "vertical", isin, company_name, fiscal_year
            )
            stats.pinecone_vectors += pinecone_storage.upload_chunks(
                table_with_emb, "table", isin, company_name, fiscal_year
            )
        
        # Mark complete
        mongo_storage.mark_extraction_complete(doc_id)
        
        # Log success
        duration_ms = int((time.time() - start_time) * 1000)
        mongo_storage.log_extraction(
            doc_id, isin, "complete", "success", duration_ms,
            metadata={
                "narrative_chunks": len(narrative_chunks),
                "vertical_chunks": len(vertical_chunks),
                "table_chunks": len(table_chunks)
            }
        )
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        mongo_storage.log_extraction(
            doc_id if 'doc_id' in locals() else None,
            isin, "extraction", "failed", error=str(e)
        )
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Extract data from annual report PDFs"
    )
    parser.add_argument(
        '--chunk-number',
        type=int,
        default=0,
        help='Chunk number to process (0-indexed)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=100,
        help='Number of stocks per chunk'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode - process only 1 PDF'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("PDF EXTRACTION PIPELINE")
    print("="*60 + "\n")
    
    # Initialize components
    print("Initializing components...")
    extractors = {
        'narrative': NarrativeExtractor(),
        'vertical': VerticalDetector(use_llm=True),
        'table': TableExtractor(use_llm=True)
    }
    
    # Use OpenAI embeddings for hot data (cost-effective)
    embedding_gen = OpenAIEmbeddingGenerator(model="text-embedding-3-small")
    mongo_storage = MongoDBStorage()
    pinecone_storage = PineconeStorage()
    llm_client = get_llm_client()
    
    stats = ExtractionStats()
    
    # Get stocks to process
    if args.test:
        print("\n🧪 TEST MODE - Processing 1 PDF\n")
        stocks = get_chunk_isins(0, 1)
    else:
        print(f"\nProcessing Chunk {args.chunk_number} ({args.chunk_size} stocks)\n")
        stocks = get_chunk_isins(args.chunk_number, args.chunk_size)
    
    if not stocks:
        print("❌ No stocks found to process")
        return
    
    # Process each stock
    for stock in tqdm(stocks, desc="Processing stocks"):
        isin = stock.get("isin")
        company_name = stock.get("company_name", isin)
        
        if not isin:
            continue
        
        # Find PDFs for this stock
        pdfs = find_pdf_for_stock(isin)
        
        if not pdfs:
            print(f"\n⚠️  No PDFs found for {isin}")
            continue
        
        # Process each PDF
        for pdf_path in pdfs:
            fiscal_year = extract_fiscal_year_from_filename(pdf_path)
            
            print(f"\n📄 Processing: {isin} FY{fiscal_year}")
            stats.total_pdfs += 1
            
            success = process_pdf(
                pdf_path, isin, company_name, fiscal_year,
                extractors, embedding_gen, mongo_storage,
                pinecone_storage, stats
            )
            
            if success:
                stats.successful += 1
            else:
                stats.failed += 1
    
    # Print summary
    print(stats.summary())
    
    # Print LLM cost summary
    print("\n" + llm_client.get_cost_summary())
    
    # Print embedding cost summary
    print("\n" + embedding_gen.get_cost_summary())
    
    # Print Pinecone stats
    print("\nPinecone Index Stats:")
    pinecone_stats = pinecone_storage.get_index_stats()
    for idx_type, idx_stats in pinecone_stats.items():
        print(f"  {idx_type}: {idx_stats}")


if __name__ == "__main__":
    import pdfplumber
    main()
