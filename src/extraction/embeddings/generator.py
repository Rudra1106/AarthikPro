"""
Embedding Generator
Generates embeddings using sentence-transformers (free, local).
"""

from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingGenerator:
    """Generate embeddings for text chunks."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Dimension: {self.dimension}")
        
    def generate(self, chunks: List[Dict[str, Any]], chunk_type: str) -> List[Dict[str, Any]]:
        """
        Generate embeddings for chunks.
        
        Args:
            chunks: List of text chunks
            chunk_type: Type of chunks (narrative, vertical, table)
            
        Returns:
            List of chunks with embeddings added
        """
        if not chunks:
            return []
        
        # Extract texts
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        print(f"Generating {len(texts)} {chunk_type} embeddings...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i].tolist()
            chunk["embedding_model"] = self.model.model_card_data.model_name
            chunk["embedding_dimension"] = self.dimension
        
        return chunks
    
    def generate_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embedding = self.model.encode([text])[0]
        return embedding.tolist()
