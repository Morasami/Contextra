"""
Embedding Service: Local embedding generation using Sentence-Transformers

This service handles vector embedding generation for semantic search,
using local models to ensure 100% free operation.
"""

from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from ..config import config

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using local Sentence-Transformers models"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config.mcp_server.default_embedding_model
        self._model: Optional[SentenceTransformer] = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise
    
    @property
    def model(self) -> SentenceTransformer:
        """Get the embedding model, initializing if necessary"""
        if self._model is None:
            self._initialize_model()
        return self._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            # Encode the text
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            # Convert to list of floats
            if isinstance(embedding, np.ndarray):
                return embedding.tolist()
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Use batch processing for efficiency
            batch_size = config.ai.embedding_batch_size
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.model.encode(batch, convert_to_tensor=False)
                
                # Convert to list format
                if isinstance(batch_embeddings, np.ndarray):
                    embeddings.extend(batch_embeddings.tolist())
                else:
                    embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def generate_memory_embedding(self, title: str, summary: str, full_content: str) -> List[float]:
        """
        Generate embedding for a memory by combining title, summary, and content
        
        Args:
            title: Memory title
            summary: Memory summary
            full_content: Full memory content
            
        Returns:
            Combined embedding vector
        """
        # Combine text with appropriate weighting
        # Title and summary are more important for search
        combined_text = f"{title} {summary} {full_content[:1000]}"  # Limit content to first 1000 chars
        
        return self.generate_embedding(combined_text)
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Failed to calculate similarity: {e}")
            return 0.0
    
    def get_model_info(self) -> dict:
        """Get information about the current embedding model"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.model.get_sentence_embedding_dimension() if self._model else None,
            "max_sequence_length": getattr(self.model, "max_seq_length", None) if self._model else None
        }
