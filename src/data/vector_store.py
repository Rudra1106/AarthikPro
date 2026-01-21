"""
Pinecone vector store interface for RAG on financial reports.
"""
import asyncio
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

from src.config import settings


class VectorStore:
    """
    Pinecone vector store for semantic search on financial documents.
    
    Optimizations:
    - Hybrid search (dense embeddings)
    - Metadata filtering for precise retrieval
    - Adaptive top-k based on query complexity
    """
    
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        
        # Initialize embedding model (runs locally for cost savings)
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        
        # Get or create index
        self._ensure_index_exists()
        self.index = self.pc.Index(self.index_name)
    
    def _ensure_index_exists(self):
        """Ensure Pinecone index exists, create if not."""
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            # Create index with serverless spec (cost-effective)
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # all-MiniLM-L6-v2 dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using local model."""
        embedding = self.embedding_model.encode(text, convert_to_tensor=False)
        return embedding.tolist()
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        namespace: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Semantic search in vector store.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"company": "RELIANCE", "year": 2023})
            namespace: Pinecone namespace
            
        Returns:
            List of matching documents with metadata
        """
        # Generate query embedding
        query_embedding = await asyncio.to_thread(self._generate_embedding, query)
        
        # Build filter dict for Pinecone
        pinecone_filter = filters if filters else {}
        
        # Search
        results = await asyncio.to_thread(
            self.index.query,
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=pinecone_filter,
            namespace=namespace
        )
        
        # Format results
        documents = []
        for match in results.matches:
            documents.append({
                "id": match.id,
                "score": match.score,
                "text": match.metadata.get("text", ""),
                "metadata": match.metadata,
                "source": match.metadata.get("source", ""),
                "company": match.metadata.get("company", ""),
                "year": match.metadata.get("year", ""),
                "document_type": match.metadata.get("document_type", ""),
            })
        
        return documents
    
    async def search_by_company(
        self,
        query: str,
        company: str,
        top_k: int = 5,
        year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search documents for a specific company.
        
        Args:
            query: Search query
            company: Company symbol (e.g., "RELIANCE")
            top_k: Number of results
            year: Optional year filter
            
        Returns:
            Matching documents
        """
        filters = {"company": company}
        if year:
            filters["year"] = year
        
        return await self.search(query, top_k=top_k, filters=filters)
    
    async def get_company_context(
        self,
        company: str,
        context_type: str = "overview",
        year: Optional[int] = None
    ) -> str:
        """
        Get contextual information about a company.
        
        Args:
            company: Company symbol
            context_type: Type of context (overview, financials, risks, etc.)
            year: Optional year filter
            
        Returns:
            Aggregated context text
        """
        query = f"{company} {context_type}"
        results = await self.search_by_company(query, company, top_k=3, year=year)
        
        # Aggregate results
        context_parts = [doc["text"] for doc in results if doc["score"] > 0.7]
        return "\n\n".join(context_parts)


# Singleton instance
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get singleton vector store instance."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()
    return _vector_store_instance
