"""
MemoryService: Core memory operations and business logic

This service handles all memory-related operations including storage,
retrieval, and management of memories in the simplified canonical schema.

Canonical Schema: id, title, summary, full_content, created_at, updated_at
Supports: 5 core MCP tools with agent-guided two-stage retrieval workflow
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy import create_engine, desc, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import json

from ..models.memory import (
    MemoryEntity, Base, WriteMemoryRequest, MemoryPreview, MemoryDetails,
    SearchMemoryRequest, GetFullMemoryRequest, ListRecentMemoriesRequest,
    GetMemoryDetailsRequest, WriteMemoryResponse, SearchMemoryResponse,
    GetFullMemoryResponse, ListRecentMemoriesResponse, GetMemoryDetailsResponse
)
from ..config import config
from .vector_service import VectorService
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class MemoryService:
    """Core service for memory operations (Canonical 5-Tool Implementation)"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService(self.embedding_service)
        
    async def initialize(self):
        """Initialize the memory service"""
        try:
            # Initialize database
            database_url = config.database_url
            logger.info(f"Initializing database: {database_url}")
            
            # Create engine
            if database_url.startswith("sqlite"):
                self.engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    echo=config.mcp_server.mcp_debug
                )
            else:
                self.engine = create_engine(database_url, echo=config.mcp_server.mcp_debug)
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Initialize vector service
            await self.vector_service.initialize()
            
            logger.info("Memory service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory service: {e}")
            raise
    
    def get_db_session(self) -> Session:
        """Get a database session"""
        if not self.SessionLocal:
            raise RuntimeError("Memory service not initialized")
        return self.SessionLocal()
    
    async def write_memory(self, request: WriteMemoryRequest) -> WriteMemoryResponse:
        """
        Store a new memory in the database and vector store (Canonical Schema)
        
        Args:
            request: WriteMemoryRequest with title, summary, full_content
            
        Returns:
            WriteMemoryResponse with success status and memory ID
        """
        db = self.get_db_session()
        try:
            # Create memory entity (Canonical Schema - Simplified)
            memory = MemoryEntity(
                title=request.title,
                summary=request.summary,
                full_content=request.full_content
            )
            
            # Save to database
            db.add(memory)
            db.commit()
            db.refresh(memory)
            
            # Store embedding in vector database (summary-based for search)
            metadata = {
                "title": memory.title,
                "created_at": memory.created_at.isoformat()
            }
            
            success = await self.vector_service.store_memory_embedding(
                memory.id,
                memory.title,
                memory.summary,
                memory.full_content,
                metadata
            )
            
            if not success:
                logger.warning(f"Failed to store embedding for memory {memory.id}")
            
            logger.info(f"Memory stored successfully with ID: {memory.id}")
            return WriteMemoryResponse(
                success=True,
                memory_id=memory.id,
                message="Memory stored successfully"
            )
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error while storing memory: {e}")
            return WriteMemoryResponse(
                success=False,
                memory_id="",
                message=f"Failed to store memory: {str(e)}"
            )
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error while storing memory: {e}")
            return WriteMemoryResponse(
                success=False,
                memory_id="",
                message=f"Unexpected error: {str(e)}"
            )
        finally:
            db.close()
    
    async def search_memory_preview(self, request: SearchMemoryRequest) -> SearchMemoryResponse:
        """
        Search for memories and return previews (Stage 1 of Two-Stage Retrieval)
        
        Args:
            request: SearchMemoryRequest with query and limit
            
        Returns:
            SearchMemoryResponse with lightweight memory previews
        """
        try:
            # Search in vector database (summary-based semantic search)
            vector_results = await self.vector_service.search_memories(
                request.query,
                limit=request.limit
            )
            
            # Get memory IDs from vector results
            memory_ids = [result['memory_id'] for result in vector_results]
            
            if not memory_ids:
                return SearchMemoryResponse(
                    memories=[],
                    total_found=0,
                    query=request.query
                )
            
            # Fetch memory details from database
            db = self.get_db_session()
            try:
                memories = db.query(MemoryEntity).filter(MemoryEntity.id.in_(memory_ids)).all()
                
                # Convert to preview format and maintain vector search order
                memory_dict = {m.id: m for m in memories}
                previews = []
                
                for result in vector_results:
                    memory_id = result['memory_id']
                    if memory_id in memory_dict:
                        memory = memory_dict[memory_id]
                        preview = MemoryPreview(
                            memory_id=memory.id,
                            title=memory.title,
                            summary=memory.summary,
                            created_at=memory.created_at
                        )
                        previews.append(preview)
                
                logger.info(f"Found {len(previews)} memories for query: {request.query}")
                
                return SearchMemoryResponse(
                    memories=previews,
                    total_found=len(previews),
                    query=request.query
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return SearchMemoryResponse(
                memories=[],
                total_found=0,
                query=request.query
            )
    
    async def get_full_memory_by_ids(self, request: GetFullMemoryRequest) -> GetFullMemoryResponse:
        """
        Retrieve full memory content by IDs (Stage 2 of Two-Stage Retrieval)
        
        Args:
            request: GetFullMemoryRequest with memory IDs
            
        Returns:
            GetFullMemoryResponse with complete memory details
        """
        db = self.get_db_session()
        try:
            memories = db.query(MemoryEntity).filter(MemoryEntity.id.in_(request.ids)).all()
            
            details = []
            for memory in memories:
                detail = MemoryDetails(
                    memory_id=memory.id,
                    title=memory.title,
                    summary=memory.summary,
                    full_content=memory.full_content,
                    created_at=memory.created_at,
                    updated_at=memory.updated_at
                )
                details.append(detail)
            
            logger.info(f"Retrieved {len(details)} complete memories")
            
            return GetFullMemoryResponse(memories=details)
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}")
            return GetFullMemoryResponse(memories=[])
        finally:
            db.close()
    
    async def list_recent_memories(self, request: ListRecentMemoriesRequest) -> ListRecentMemoriesResponse:
        """
        List recently created memories (Introspection Tool)
        
        Args:
            request: ListRecentMemoriesRequest with limit
            
        Returns:
            ListRecentMemoriesResponse with recent memory previews
        """
        db = self.get_db_session()
        try:
            memories = (
                db.query(MemoryEntity)
                .order_by(desc(MemoryEntity.created_at))
                .limit(request.limit)
                .all()
            )
            
            previews = []
            for memory in memories:
                preview = MemoryPreview(
                    memory_id=memory.id,
                    title=memory.title,
                    summary=memory.summary,
                    created_at=memory.created_at
                )
                previews.append(preview)
            
            total_count = db.query(MemoryEntity).count()
            
            logger.info(f"Retrieved {len(previews)} recent memories")
            
            return ListRecentMemoriesResponse(
                memories=previews,
                total_count=total_count
            )
            
        except Exception as e:
            logger.error(f"Error listing recent memories: {e}")
            return ListRecentMemoriesResponse(memories=[], total_count=0)
        finally:
            db.close()
    
    async def get_memory_details(self, request: GetMemoryDetailsRequest) -> GetMemoryDetailsResponse:
        """
        Get detailed information about a specific memory (Introspection Tool)
        
        Args:
            request: GetMemoryDetailsRequest with memory ID
            
        Returns:
            GetMemoryDetailsResponse with complete memory details
        """
        db = self.get_db_session()
        try:
            memory = db.query(MemoryEntity).filter(MemoryEntity.id == request.memory_id).first()
            
            if not memory:
                raise ValueError(f"Memory not found: {request.memory_id}")
            
            detail = MemoryDetails(
                memory_id=memory.id,
                title=memory.title,
                summary=memory.summary,
                full_content=memory.full_content,
                created_at=memory.created_at,
                updated_at=memory.updated_at
            )
            
            logger.info(f"Retrieved details for memory {request.memory_id}")
            
            return GetMemoryDetailsResponse(memory=detail)
            
        except Exception as e:
            logger.error(f"Error retrieving memory details: {e}")
            raise
        finally:
            db.close()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory database statistics (simplified for canonical schema)"""
        db = self.get_db_session()
        try:
            total_memories = db.query(MemoryEntity).count()
            
            # Get vector database info
            vector_info = await self.vector_service.get_collection_info()
            
            # Get recent activity
            recent_memories = (
                db.query(MemoryEntity)
                .order_by(desc(MemoryEntity.created_at))
                .limit(5)
                .all()
            )
            
            recent_titles = [m.title for m in recent_memories]
            
            return {
                "total_memories": total_memories,
                "vector_database": vector_info,
                "embedding_model": self.embedding_service.model_name,
                "recent_memory_titles": recent_titles,
                "server_mode": "lightweight" if config.is_lightweight_mode else "production"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.vector_service:
                await self.vector_service.cleanup()
            
            if self.engine:
                self.engine.dispose()
            
            logger.info("Memory service cleaned up")
            
        except Exception as e:
            logger.error(f"Error during memory service cleanup: {e}")
