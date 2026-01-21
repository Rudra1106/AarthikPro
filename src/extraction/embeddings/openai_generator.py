"""
OpenAI Embedding Generator
Uses OpenAI's text-embedding-3-small for cost-effective embeddings.
Only for HOT data - warm/cold data stays as text in MongoDB.
"""

import os
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv

load_dotenv()


class OpenAIEmbeddingGenerator:
    """
    Generate embeddings using OpenAI's text-embedding-3-small.
    
    Cost: $0.02 per 1M tokens
    Dimension: 1536
    """
    
    def __init__(self, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding generator.
        
        Args:
            model: OpenAI embedding model to use
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.dimension = 1536  # text-embedding-3-small dimension
        
        # Cost tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        
        print(f"OpenAI Embedding Generator initialized")
        print(f"Model: {self.model}")
        print(f"Dimension: {self.dimension}")
        print(f"Cost: $0.02 per 1M tokens")
    
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
        
        print(f"Generating {len(texts)} {chunk_type} embeddings with OpenAI...")
        
        # Generate embeddings in batches
        batch_size = 100  # OpenAI allows up to 2048
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch_texts
                )
                
                # Extract embeddings
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Track cost
                tokens_used = response.usage.total_tokens
                cost = (tokens_used / 1_000_000) * 0.02
                
                self.total_tokens += tokens_used
                self.total_cost += cost
                
                print(f"  Batch {i//batch_size + 1}: {len(batch_texts)} embeddings, "
                      f"{tokens_used} tokens, ${cost:.4f}")
                
            except Exception as e:
                print(f"  Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Add None for failed embeddings
                all_embeddings.extend([None] * len(batch_texts))
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            if i < len(all_embeddings) and all_embeddings[i] is not None:
                chunk["embedding"] = all_embeddings[i]
                chunk["embedding_model"] = self.model
                chunk["embedding_dimension"] = self.dimension
            else:
                chunk["embedding"] = None
        
        return chunks
    
    def generate_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=[text]
            )
            
            # Track cost
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1_000_000) * 0.02
            self.total_tokens += tokens_used
            self.total_cost += cost
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"Error generating single embedding: {e}")
            return None
    
    def get_cost_summary(self) -> str:
        """Get cost summary."""
        return f"""
OpenAI Embedding Cost:
  Total Tokens: {self.total_tokens:,}
  Total Cost: ${self.total_cost:.4f}
  Model: {self.model}
"""
