"""
Vector Service: ChromaDB operations for semantic search

This service handles all vector database operations including embedding
storage and semantic search using ChromaDB for lightweight deployment.
"""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import logging
from pathlib import Path
import chromadb
from chromadb.config import Settings
from ..config import config
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class VectorService:
    """Service for vector operations using ChromaDB"""
    
    def __init__(self, embedding_service: Optional[EmbeddingService] = None):
        self.embedding_service = embedding_service or EmbeddingService()
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[chromadb.Collection] = None
        self.collection_name = "contextra_memories"
        
    def _get_client(self) -> chromadb.Client:
        """Get or create ChromaDB client"""
        if self._client is None:
            # Ensure the ChromaDB directory exists
            db_path = Path(config.vector_db.chromadb_path)
            db_path.mkdir(parents=True, exist_ok=True)
            
            # Create persistent client
            self._client = chromadb.PersistentClient(
                path=str(db_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info(f"ChromaDB client initialized at {db_path}")
        
        return self._client
    
    def _get_collection(self) -> chromadb.Collection:
        """Get or create the memories collection"""
        if self._collection is None:
            client = self._get_client()
            
            try:
                # Try to get existing collection
                self._collection = client.get_collection(name=self.collection_name)
                logger.info(f"Using existing ChromaDB collection: {self.collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Contextra memory embeddings"}
                )
                logger.info(f"Created new ChromaDB collection: {self.collection_name}")
        
        return self._collection
    
    async def initialize(self):
        """Initialize the vector service"""
        try:
            # Initialize the collection
            self._get_collection()
            logger.info("Vector service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            raise
    
    async def store_memory_embedding(
        self, 
        memory_id: str, 
        title: str, 
        summary: str, 
        full_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store a memory's embedding in the vector database
        
        Args:
            memory_id: Unique memory identifier
            title: Memory title
            summary: Memory summary
            full_content: Full memory content
            metadata: Additional metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Generate embedding
            embedding = self.embedding_service.generate_memory_embedding(title, summary, full_content)
            
            # Prepare metadata
            doc_metadata = {
                "title": title,
                "summary": summary,
                "memory_id": memory_id,
            }
            
            # Add other metadata with ChromaDB-compatible types
            if metadata:
                for key, value in metadata.items():
                    if key == "tags" and isinstance(value, list):
                        # Convert tags list to comma-separated string
                        doc_metadata[key] = ",".join(value) if value else ""
                    elif value is not None:
                        # Only add non-None values and ensure they're primitive types
                        if isinstance(value, (str, int, float, bool)):
                            doc_metadata[key] = value
                        else:
                            doc_metadata[key] = str(value)
            
            # Store in ChromaDB
            collection = self._get_collection()
            collection.add(
                embeddings=[embedding],
                documents=[f"{title} {summary}"],  # Store searchable text
                metadatas=[doc_metadata],
                ids=[memory_id]
            )
            
            logger.debug(f"Stored embedding for memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store embedding for memory {memory_id}: {e}")
            return False
    
    async def search_memories(
        self, 
        query: str, 
        limit: int = 5,
        where_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for memories using semantic similarity
        
        Args:
            query: Search query
            limit: Maximum number of results
            where_filters: ChromaDB where filters for metadata
            
        Returns:
            List of search results with memory_id, distance, and metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_embedding(query)
            
            # Search in ChromaDB
            collection = self._get_collection()
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filters
            )
            
            # Process results
            search_results = []
            if results['ids'] and results['ids'][0]:
                for i, memory_id in enumerate(results['ids'][0]):
                    result = {
                        'memory_id': memory_id,
                        'distance': results['distances'][0][i] if results['distances'] else 0.0,
                        'similarity': 1.0 - (results['distances'][0][i] if results['distances'] else 0.0),
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    }
                    search_results.append(result)
            
            logger.debug(f"Found {len(search_results)} memories for query: {query}")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    async def update_memory_embedding(
        self, 
        memory_id: str, 
        title: str, 
        summary: str, 
        full_content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Update an existing memory embedding
        
        Args:
            memory_id: ID of the memory
            title: Memory title
            summary: Memory summary
            full_content: Full memory content
            metadata: Additional metadata
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Generate new embedding
            combined_text = f"{title}\n{summary}\n{full_content}"
            embedding = await self.embedding_service.generate_embedding(combined_text)
            
            collection = self._get_collection()
            
            # Prepare metadata with ChromaDB-compatible types
            doc_metadata = {
                "title": title,
                "summary": summary,
                "memory_id": memory_id,
            }
            
            # Add other metadata with ChromaDB-compatible types
            if metadata:
                for key, value in metadata.items():
                    if key == "tags" and isinstance(value, list):
                        # Convert tags list to comma-separated string
                        doc_metadata[key] = ",".join(value) if value else ""
                    elif value is not None:
                        # Only add non-None values and ensure they're primitive types
                        if isinstance(value, (str, int, float, bool)):
                            doc_metadata[key] = value
                        else:
                            doc_metadata[key] = str(value)
            
            # Delete existing embedding first
            try:
                collection.delete(ids=[memory_id])
            except Exception:
                # If deletion fails, the ID might not exist, which is fine
                pass
            
            # Add updated embedding
            collection.add(
                embeddings=[embedding],
                documents=[combined_text],
                metadatas=[doc_metadata],
                ids=[memory_id]
            )
            
            logger.info(f"Successfully updated embedding for memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update embedding for memory {memory_id}: {e}")
            return False
    
    async def delete_memory_embedding(self, memory_id: str) -> bool:
        """
        Delete a memory's embedding from the vector database
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self._get_collection()
            collection.delete(ids=[memory_id])
            
            logger.debug(f"Deleted embedding for memory {memory_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embedding for memory {memory_id}: {e}")
            return False
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector collection"""
        try:
            collection = self._get_collection()
            count = collection.count()
            
            return {
                "collection_name": self.collection_name,
                "total_embeddings": count,
                "embedding_model": self.embedding_service.model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self._client:
                # ChromaDB doesn't require explicit cleanup
                self._client = None
                self._collection = None
                logger.info("Vector service cleaned up")
        except Exception as e:
            logger.error(f"Error during vector service cleanup: {e}")
