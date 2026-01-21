#!/usr/bin/env python3
"""
PDF Download Script for AarthikAI
Downloads annual reports and concall transcripts from MongoDB URLs.

Features:
- Chunked processing (default: 100 stocks per run)
- Sequential ISIN-based ordering for consistent chunk processing
- Annual reports only mode (for extraction pipeline)
- Progress tracking with resume capability
- Retry logic with exponential backoff
- Rate limiting to be respectful to servers
- Comprehensive error logging
- Dry-run mode for testing

Usage:
    python scripts/download_pdfs.py                           # Download next 100 stocks
    python scripts/download_pdfs.py --annual-only             # Annual reports only
    python scripts/download_pdfs.py --chunk-size 50           # Custom chunk size
    python scripts/download_pdfs.py --chunk-number 5          # Process specific chunk
    python scripts/download_pdfs.py --dry-run                 # Test without downloading
    python scripts/download_pdfs.py --reset                   # Reset progress and start over
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

import requests
from pymongo import MongoClient
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "PORTFOLIO_MANAGER")
BASE_DIR = Path(__file__).parent.parent / "data"
ANNUAL_DIR = BASE_DIR / "annual_reports"
CONCALL_DIR = BASE_DIR / "concalls"
STATE_FILE = BASE_DIR / "download_state.json"
ERROR_LOG_FILE = BASE_DIR / "download_errors.log"

# Download settings
DEFAULT_CHUNK_SIZE = 100
RATE_LIMIT_DELAY = 0.3  # seconds between downloads
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # exponential backoff multiplier


class DownloadStats:
    """Track download statistics."""
    
    def __init__(self):
        self.total_pdfs = 0
        self.downloaded = 0
        self.skipped = 0
        self.failed = 0
        self.annual_reports = 0
        self.concalls = 0
        
    def summary(self) -> str:
        """Generate summary report."""
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    DOWNLOAD SUMMARY                          ║
╚══════════════════════════════════════════════════════════════╝

📊 Total PDFs Processed:     {self.total_pdfs}
✅ Successfully Downloaded:  {self.downloaded}
⏭️  Skipped (already exist): {self.skipped}
❌ Failed:                   {self.failed}

📄 Annual Reports:           {self.annual_reports}
📞 Concalls:                 {self.concalls}

Success Rate: {(self.downloaded / self.total_pdfs * 100) if self.total_pdfs > 0 else 0:.1f}%
"""


class DownloadState:
    """Manage download progress state."""
    
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.completed_isins: Set[str] = set()
        self.processed_chunks: Set[int] = set()
        self.current_chunk: int = 0
        self.failed_downloads: List[Dict] = []
        self.last_processed_index = 0
        self.load()
    
    def load(self):
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.completed_isins = set(data.get('completed_isins', []))
                    self.processed_chunks = set(data.get('processed_chunks', []))
                    self.current_chunk = data.get('current_chunk', 0)
                    self.failed_downloads = data.get('failed_downloads', [])
                    self.last_processed_index = data.get('last_processed_index', 0)
                    logging.info(f"Loaded state: {len(self.completed_isins)} ISINs completed, current chunk: {self.current_chunk}")
            except Exception as e:
                logging.error(f"Error loading state file: {e}")
    
    def save(self):
        """Save state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump({
                    'completed_isins': list(self.completed_isins),
                    'processed_chunks': list(self.processed_chunks),
                    'current_chunk': self.current_chunk,
                    'failed_downloads': self.failed_downloads,
                    'last_processed_index': self.last_processed_index,
                    'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving state file: {e}")
    
    def mark_completed(self, isin: str):
        """Mark ISIN as completed."""
        self.completed_isins.add(isin)
        self.save()
    
    def add_failed(self, isin: str, url: str, error: str):
        """Record failed download."""
        self.failed_downloads.append({
            'isin': isin,
            'url': url,
            'error': str(error),
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save()
    
    def mark_chunk_completed(self, chunk_number: int):
        """Mark a chunk as completed."""
        self.processed_chunks.add(chunk_number)
        self.current_chunk = chunk_number + 1
        self.save()
    
    def reset(self):
        """Reset all progress."""
        self.completed_isins.clear()
        self.processed_chunks.clear()
        self.current_chunk = 0
        self.failed_downloads.clear()
        self.last_processed_index = 0
        if self.state_file.exists():
            self.state_file.unlink()
        logging.info("Progress reset successfully")


def setup_logging(log_file: Path):
    """Configure logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )


def download_pdf(url: str, save_path: Path, max_retries: int = MAX_RETRIES) -> bool:
    """
    Download a single PDF with retry logic.
    
    Args:
        url: PDF URL to download
        save_path: Path to save the PDF
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if successful, False otherwise
    """
    # Browser headers to avoid 403 errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT, stream=True)
            response.raise_for_status()
            
            # Write to file
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Validate file size
            if save_path.stat().st_size == 0:
                save_path.unlink()
                raise ValueError("Downloaded file is empty")
            
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = RETRY_BACKOFF ** attempt
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logging.error(f"Failed to download {url} after {max_retries} attempts: {e}")
                return False
    
    return False


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to remove invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')
    
    return filename


def process_stock(
    stock: Dict,
    state: DownloadState,
    stats: DownloadStats,
    dry_run: bool = False,
    annual_only: bool = False
) -> None:
    """
    Process a single stock's PDFs.
    
    Args:
        stock: Stock document from MongoDB
        state: Download state tracker
        stats: Statistics tracker
        dry_run: If True, don't actually download
        annual_only: If True, only download annual reports
    """
    isin = stock.get("isin")
    if not isin:
        logging.warning(f"Stock missing ISIN: {stock.get('_id')}")
        return
    
    # Skip if already completed
    if isin in state.completed_isins:
        return
    
    # Process annual reports
    annual_reports = stock.get("annual_reports", [])
    for report in annual_reports:
        url = report.get("url")
        year = report.get("year", "unknown")
        
        if not url:
            continue
        
        stats.total_pdfs += 1
        stats.annual_reports += 1
        
        # Create directory
        save_dir = ANNUAL_DIR / isin
        if not dry_run:
            save_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine filename
        filename = sanitize_filename(f"{year}.pdf")
        file_path = save_dir / filename
        
        # Skip if already exists
        if file_path.exists():
            stats.skipped += 1
            continue
        
        if dry_run:
            logging.info(f"[DRY RUN] Would download: {url} -> {file_path}")
            stats.downloaded += 1
        else:
            # Download
            if download_pdf(url, file_path):
                stats.downloaded += 1
                logging.info(f"✓ Downloaded: {isin}/{year}.pdf")
            else:
                stats.failed += 1
                state.add_failed(isin, url, "Download failed")
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
    
    # Process concalls (skip if annual_only mode)
    if not annual_only:
        concalls = stock.get("concalls", [])
        for call in concalls:
            url = call.get("url")
            quarter = call.get("quarter", "unknown")
            
            if not url:
                continue
            
            stats.total_pdfs += 1
            stats.concalls += 1
            
            # Create directory
            save_dir = CONCALL_DIR / isin
            if not dry_run:
                save_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine filename (sanitize quarter name)
            filename = sanitize_filename(f"{quarter}.pdf".replace(" ", "_"))
            file_path = save_dir / filename
            
            # Skip if already exists
            if file_path.exists():
                stats.skipped += 1
                continue
            
            if dry_run:
                logging.info(f"[DRY RUN] Would download: {url} -> {file_path}")
                stats.downloaded += 1
            else:
                # Download
                if download_pdf(url, file_path):
                    stats.downloaded += 1
                    logging.info(f"✓ Downloaded: {isin}/{quarter}.pdf")
                else:
                    stats.failed += 1
                    state.add_failed(isin, url, "Download failed")
                
                # Rate limiting
                time.sleep(RATE_LIMIT_DELAY)
    
    # Mark ISIN as completed
    if not dry_run:
        state.mark_completed(isin)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Download PDFs from MongoDB stock_documents collection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f'Number of stocks to process per run (default: {DEFAULT_CHUNK_SIZE})'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - show what would be downloaded without actually downloading'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset progress and start from beginning'
    )
    parser.add_argument(
        '--skip',
        type=int,
        default=0,
        help='Skip first N stocks (useful for manual control)'
    )
    parser.add_argument(
        '--annual-only',
        action='store_true',
        help='Download only annual reports (skip concalls)'
    )
    parser.add_argument(
        '--chunk-number',
        type=int,
        default=None,
        help='Process specific chunk number (0-indexed)'
    )
    
    args = parser.parse_args()
    
    # Setup
    BASE_DIR.mkdir(exist_ok=True)
    ANNUAL_DIR.mkdir(parents=True, exist_ok=True)
    CONCALL_DIR.mkdir(parents=True, exist_ok=True)
    setup_logging(ERROR_LOG_FILE)
    
    # Initialize state
    state = DownloadState(STATE_FILE)
    if args.reset:
        state.reset()
    
    # Initialize stats
    stats = DownloadStats()
    
    # Connect to MongoDB
    logging.info("Connecting to MongoDB...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DATABASE]
    collection = db["stock_documents"]
    
    # Get total count
    total_stocks = collection.count_documents({})
    logging.info(f"Total stocks in database: {total_stocks}")
    logging.info(f"Already completed: {len(state.completed_isins)}")
    
    # Determine chunk to process
    if args.chunk_number is not None:
        chunk_number = args.chunk_number
        logging.info(f"Processing specific chunk: {chunk_number}")
    else:
        chunk_number = state.current_chunk
        logging.info(f"Processing next chunk: {chunk_number}")
    
    # Calculate skip count based on chunk number
    skip_count = chunk_number * args.chunk_size
    
    # Get stocks to process (sorted by ISIN for consistency)
    projection = {"isin": 1, "annual_reports": 1}
    if not args.annual_only:
        projection["concalls"] = 1
    
    cursor = collection.find(
        {},
        projection
    ).sort("isin", 1).skip(skip_count).limit(args.chunk_size)
    
    stocks = list(cursor)
    
    if not stocks:
        logging.info("✅ No more stocks to process!")
        print(stats.summary())
        return
    
    logging.info(f"Processing chunk {chunk_number}: {len(stocks)} stocks (chunk size: {args.chunk_size})")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files will be downloaded\n")
    
    if args.annual_only:
        print("\n📄 ANNUAL REPORTS ONLY MODE\n")
    
    # Process stocks with progress bar
    for stock in tqdm(stocks, desc=f"Chunk {chunk_number}", unit="stock"):
        process_stock(stock, state, stats, dry_run=args.dry_run, annual_only=args.annual_only)
    
    # Mark chunk as completed
    if not args.dry_run:
        state.mark_chunk_completed(chunk_number)
    
    # Print summary
    print(stats.summary())
    
    if not args.dry_run:
        logging.info(f"Progress saved to: {STATE_FILE}")
        logging.info(f"Error log: {ERROR_LOG_FILE}")
        
        # Show next steps
        total_chunks = (total_stocks + args.chunk_size - 1) // args.chunk_size
        next_chunk = chunk_number + 1
        
        if next_chunk < total_chunks:
            print(f"\n📌 Next Steps:")
            print(f"   Chunk {chunk_number} completed ({len(stocks)} stocks)")
            print(f"   Next chunk: {next_chunk}/{total_chunks - 1}")
            print(f"   Stocks remaining: {total_stocks - (next_chunk * args.chunk_size)}")
            print(f"\n   Run extraction pipeline on chunk {chunk_number}:")
            print(f"   python scripts/extract_pdfs.py --chunk-number {chunk_number}")
            print(f"\n   Then download next chunk:")
            if args.annual_only:
                print(f"   python scripts/download_pdfs.py --annual-only")
            else:
                print(f"   python scripts/download_pdfs.py")
        else:
            print(f"\n🎉 All chunks processed!")
            print(f"   Total chunks: {total_chunks}")
            print(f"   Total stocks: {total_stocks}")
            print(f"\n📌 Next Steps:")
            print(f"   1. Verify downloaded PDFs: find data -name '*.pdf' -size 0")
            print(f"   2. Run final extraction if needed")
            print(f"   3. Generate embeddings with BAAI/bge-large-en-v1.5")
    
    # Cleanup
    client.close()


if __name__ == "__main__":
    main()
