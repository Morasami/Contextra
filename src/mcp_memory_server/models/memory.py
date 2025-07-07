"""
Memory models and schemas

This module contains all memory-related data models including:
- Memory entity models (SQLAlchemy)
- Request/Response schemas (Pydantic)
- Validation schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.sqlite import DATETIME
import uuid

Base = declarative_base()

# SQLAlchemy Models for Database Storage

class MemoryEntity(Base):
    """SQLAlchemy model for memory storage (Simplified Canonical Schema)"""
    __tablename__ = "memories"
    
    id = Column(String, primary_key=True, default=lambda: f"mem_{uuid.uuid4().hex[:12]}")
    title = Column(String(200), nullable=False, index=True)
    summary = Column(Text, nullable=False)
    full_content = Column(Text, nullable=False)
    created_at = Column(DATETIME, default=datetime.utcnow, index=True)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic Models for Request/Response Validation (Canonical Schema)

class WriteMemoryRequest(BaseModel):
    """Request schema for write_memory tool (Canonical - Simplified)"""
    title: str = Field(..., description="A concise, keyword-rich title summarizing the memory content. Should capture the essential topic in 10 words or less for effective search and identification.")
    summary: str = Field(..., description="A brief, factual summary of the memory content. Should be comprehensive yet concise, capturing key details in 1-2 sentences. This will be used for search previews and quick recall.")
    full_content: str = Field(..., description="The complete, original content of the memory to be stored. This should contain all relevant information for full context when retrieved by the agent.")

class MemoryPreview(BaseModel):
    """Lightweight memory representation for search previews (Two-Stage Retrieval - Stage 1)"""
    memory_id: str
    title: str
    summary: str
    created_at: datetime

class MemoryDetails(BaseModel):
    """Complete memory representation with full content (Two-Stage Retrieval - Stage 2)"""
    memory_id: str
    title: str
    summary: str
    full_content: str
    created_at: datetime
    updated_at: datetime

class SearchMemoryRequest(BaseModel):
    """Request schema for search_memory_preview tool"""
    query: str = Field(..., description="The natural language query to search for relevant memories. Formulate this as a precise question or statement describing the information you need. Focus on keywords and concepts.")
    limit: int = Field(5, description="The maximum number of memory previews to return", ge=1, le=20)

class GetFullMemoryRequest(BaseModel):
    """Request schema for get_full_memory_by_ids tool"""
    ids: List[str] = Field(..., description="A list of memory IDs to retrieve the full content for", min_items=1)

class ListRecentMemoriesRequest(BaseModel):
    """Request schema for list_recent_memories tool"""
    limit: int = Field(10, description="The maximum number of recent memories to return", ge=1, le=100)

class GetMemoryDetailsRequest(BaseModel):
    """Request schema for get_memory_details tool"""
    memory_id: str = Field(..., description="The ID of the memory to retrieve details for")

class UpdateMemoryRequest(BaseModel):
    """Request schema for update_memory tool"""
    memory_id: str = Field(..., description="The ID of the memory to update")
    title: Optional[str] = Field(None, description="Updated title (optional)")
    summary: Optional[str] = Field(None, description="Updated summary (optional)")
    full_content: Optional[str] = Field(None, description="Updated full content (optional)")
    category: Optional[str] = Field(None, description="Updated category (optional)",
                                   pattern="^(technical|decision|user_preference|code_snippet|conversation|research|project_management|other)$")
    tags: Optional[List[str]] = Field(None, description="Updated tags (optional)")
    project_id: Optional[str] = Field(None, description="Updated project ID (optional)")
    importance_score: Optional[float] = Field(None, description="Updated importance score (optional)", ge=0.0, le=1.0)
    merge_strategy: str = Field("replace", description="How to merge the updates",
                               pattern="^(replace|append|intelligent_merge)$")
    change_reason: Optional[str] = Field(None, description="Reason for the update (optional)")

# Response Models

# Response Models

class WriteMemoryResponse(BaseModel):
    """Response schema for write_memory tool"""
    success: bool
    memory_id: str
    message: str

class SearchMemoryResponse(BaseModel):
    """Response schema for search_memory_preview tool"""
    memories: List[MemoryPreview]
    total_found: int
    query: str

class GetFullMemoryRequest(BaseModel):
    """Request schema for get_full_memory_by_ids tool"""
    ids: List[str] = Field(..., description="A list of memory IDs to retrieve. These IDs should be obtained from search_memory_preview results.")

class GetFullMemoryResponse(BaseModel):
    """Response schema for get_full_memory_by_ids tool"""
    memories: List[MemoryDetails]

class ListRecentMemoriesRequest(BaseModel):
    """Request schema for list_recent_memories tool"""
    limit: int = Field(10, description="The maximum number of recent memories to retrieve", ge=1, le=50)

class ListRecentMemoriesResponse(BaseModel):
    """Response schema for list_recent_memories tool"""
    memories: List[MemoryPreview]
    total_count: int

class GetMemoryDetailsRequest(BaseModel):
    """Request schema for get_memory_details tool"""
    memory_id: str = Field(..., description="The unique ID of the memory to retrieve")

class GetMemoryDetailsResponse(BaseModel):
    """Response schema for get_memory_details tool"""
    memory: MemoryDetails
