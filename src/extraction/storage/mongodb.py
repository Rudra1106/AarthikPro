"""
MongoDB Storage Module
Handles storage of extracted data in MongoDB.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient as PyMongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()


class MongoDBStorage:
    """MongoDB storage for extraction pipeline."""
    
    def __init__(self):
        """Initialize MongoDB connection."""
        mongodb_uri = os.getenv("MONGODB_URI")
        mongodb_database = os.getenv("MONGODB_DATABASE", "PORTFOLIO_MANAGER")
        
        if not mongodb_uri:
            raise ValueError("MONGODB_URI not found in environment")
        
        self.client = PyMongoClient(mongodb_uri)
        self.db = self.client[mongodb_database]
        
        # Collections
        self.extraction_documents = self.db["extraction_documents"]
        self.text_chunks = self.db["text_chunks"]
        self.table_chunks = self.db["table_chunks"]
        self.extraction_logs = self.db["extraction_logs"]
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create necessary indexes."""
        # extraction_documents
        self.extraction_documents.create_index([("isin", ASCENDING), ("fiscal_year", ASCENDING)], unique=True)
        self.extraction_documents.create_index([("temperature", ASCENDING)])
        self.extraction_documents.create_index([("extraction_status", ASCENDING)])
        
        # text_chunks
        self.text_chunks.create_index([("isin", ASCENDING), ("fiscal_year", ASCENDING)])
        self.text_chunks.create_index([("chunk_type", ASCENDING)])
        self.text_chunks.create_index([("vertical", ASCENDING)])
        self.text_chunks.create_index([("temperature", ASCENDING)])
        
        # table_chunks
        self.table_chunks.create_index([("isin", ASCENDING), ("fiscal_year", ASCENDING)])
        self.table_chunks.create_index([("table_type", ASCENDING)])
        self.table_chunks.create_index([("temperature", ASCENDING)])
    
    def store_document_metadata(
        self,
        isin: str,
        company_name: str,
        fiscal_year: int,
        pdf_path: str,
        pages: int,
        temperature: str
    ) -> str:
        """
        Store document metadata.
        
        Returns:
            Document ID
        """
        doc = {
            "isin": isin,
            "company_name": company_name,
            "fiscal_year": fiscal_year,
            "document_type": "annual_report",
            "pdf_path": pdf_path,
            "pages": pages,
            "temperature": temperature,
            "pinecone_indexed": False,
            "extraction_status": "in_progress",
            "extracted_at": datetime.utcnow(),
            "chunk_count": {
                "narrative": 0,
                "vertical": 0,
                "table": 0
            }
        }
        
        result = self.extraction_documents.update_one(
            {"isin": isin, "fiscal_year": fiscal_year},
            {"$set": doc},
            upsert=True
        )
        
        # Get document ID
        doc_id = self.extraction_documents.find_one(
            {"isin": isin, "fiscal_year": fiscal_year}
        )["_id"]
        
        return str(doc_id)
    
    def store_text_chunks(
        self,
        document_id: str,
        isin: str,
        company_name: str,
        fiscal_year: int,
        chunks: List[Dict[str, Any]],
        temperature: str
    ):
        """Store text chunks (narrative and vertical)."""
        if not chunks:
            return
        
        for chunk in chunks:
            chunk_doc = {
                "document_id": document_id,
                "isin": isin,
                "company_name": company_name,
                "fiscal_year": fiscal_year,
                "chunk_type": chunk["type"],
                "vertical": chunk.get("primary_vertical"),
                "page": chunk.get("page"),
                "text": chunk["text"],
                "temperature": temperature,
                "created_at": datetime.utcnow()
            }
            
            self.text_chunks.insert_one(chunk_doc)
        
        # Update document chunk count
        chunk_type = chunks[0]["type"]
        self.extraction_documents.update_one(
            {"_id": document_id},
            {"$inc": {f"chunk_count.{chunk_type}": len(chunks)}}
        )
    
    def store_table_chunks(
        self,
        document_id: str,
        isin: str,
        company_name: str,
        fiscal_year: int,
        tables: List[Dict[str, Any]],
        temperature: str
    ):
        """Store table chunks."""
        if not tables:
            return
        
        for table in tables:
            table_doc = {
                "document_id": document_id,
                "isin": isin,
                "company_name": company_name,
                "fiscal_year": fiscal_year,
                "table_type": "financial_table",
                "page": table.get("page"),
                "normalized_text": table["normalized_text"],
                "raw_table": table.get("raw_table"),
                "confidence": table.get("confidence"),
                "temperature": temperature,
                "created_at": datetime.utcnow()
            }
            
            self.table_chunks.insert_one(table_doc)
        
        # Update document chunk count
        self.extraction_documents.update_one(
            {"_id": document_id},
            {"$inc": {"chunk_count.table": len(tables)}}
        )
    
    def mark_extraction_complete(self, document_id: str):
        """Mark document extraction as complete."""
        self.extraction_documents.update_one(
            {"_id": document_id},
            {"$set": {"extraction_status": "completed"}}
        )
    
    def log_extraction(
        self,
        document_id: str,
        isin: str,
        stage: str,
        status: str,
        duration_ms: int = 0,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """Log extraction progress."""
        log_doc = {
            "document_id": document_id,
            "isin": isin,
            "stage": stage,
            "status": status,
            "duration_ms": duration_ms,
            "error": error,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow()
        }
        
        self.extraction_logs.insert_one(log_doc)
