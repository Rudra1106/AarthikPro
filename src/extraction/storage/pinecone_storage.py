"""
Pinecone Storage Module
Handles uploading embeddings to Pinecone (hot data only).
"""

import os
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()


class PineconeStorage:
    """Pinecone storage for hot data embeddings."""
    
    def __init__(self):
        """Initialize Pinecone connection."""
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY not found in environment")
        
        self.pc = Pinecone(api_key=api_key)
        
        # Index names
        self.index_names = {
            "narrative": "finance-general-v1",
            "vertical": "finance-vertical-v1",
            "table": "finance-table-v1"
        }
        
        # Ensure indexes exist
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure all required indexes exist."""
        dimension = 1536  # text-embedding-3-small dimension
        
        for index_type, index_name in self.index_names.items():
            if index_name not in self.pc.list_indexes().names():
                print(f"Creating Pinecone index: {index_name}")
                self.pc.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                print(f"Index {index_name} created successfully")
    
    def upload_chunks(
        self,
        chunks: List[Dict[str, Any]],
        chunk_type: str,
        isin: str,
        company_name: str,
        fiscal_year: int
    ) -> int:
        """
        Upload chunks to Pinecone.
        
        Args:
            chunks: List of chunks with embeddings
            chunk_type: Type of chunks (narrative, vertical, table)
            isin: Company ISIN
            company_name: Company name
            fiscal_year: Fiscal year
            
        Returns:
            Number of vectors uploaded
        """
        if not chunks:
            return 0
        
        # Get appropriate index
        index_name = self.index_names.get(chunk_type, "finance-general-v1")
        index = self.pc.Index(index_name)
        
        # Prepare vectors
        vectors = []
        for i, chunk in enumerate(chunks):
            # Generate unique ID
            vector_id = f"{isin}_{fiscal_year}_{chunk_type}_{i}"
            
            # Prepare metadata
            metadata = {
                "isin": isin,
                "company_name": company_name,
                "fiscal_year": fiscal_year,
                "chunk_type": chunk_type,
                "page": chunk.get("page", 0),
                "text": chunk["text"][:1000]  # Truncate for metadata
            }
            
            # Add vertical-specific metadata
            if chunk_type == "vertical":
                metadata["vertical"] = chunk.get("primary_vertical", "")
            
            # Add table-specific metadata
            if chunk_type == "table":
                metadata["table_id"] = chunk.get("table_id", 0)
                metadata["confidence"] = chunk.get("confidence", 0.0)
            
            vectors.append({
                "id": vector_id,
                "values": chunk["embedding"],
                "metadata": metadata
            })
        
        # Upload in batches
        batch_size = 100
        uploaded = 0
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            index.upsert(vectors=batch)
            uploaded += len(batch)
            print(f"Uploaded {uploaded}/{len(vectors)} {chunk_type} vectors to {index_name}")
        
        return uploaded
    
    def delete_document_vectors(self, isin: str, fiscal_year: int):
        """
        Delete all vectors for a document (used when demoting from hot to warm).
        
        Args:
            isin: Company ISIN
            fiscal_year: Fiscal year
        """
        for index_name in self.index_names.values():
            index = self.pc.Index(index_name)
            
            # Delete by filter
            index.delete(
                filter={
                    "isin": isin,
                    "fiscal_year": fiscal_year
                }
            )
            print(f"Deleted vectors for {isin} FY{fiscal_year} from {index_name}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics for all indexes."""
        stats = {}
        
        for index_type, index_name in self.index_names.items():
            try:
                index = self.pc.Index(index_name)
                index_stats = index.describe_index_stats()
                stats[index_type] = {
                    "name": index_name,
                    "total_vectors": index_stats.total_vector_count,
                    "dimension": index_stats.dimension
                }
            except Exception as e:
                stats[index_type] = {"error": str(e)}
        
        return stats
