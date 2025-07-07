"""
Project models and schemas

This module contains project-related data models for organizing
memories by project context.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.sqlite import DATETIME
import uuid

Base = declarative_base()

class ProjectEntity(Base):
    """SQLAlchemy model for project storage"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: f"proj_{uuid.uuid4().hex[:12]}")
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DATETIME, default=datetime.utcnow, index=True)
    updated_at = Column(DATETIME, default=datetime.utcnow, onupdate=datetime.utcnow)
    memory_count = Column(Integer, default=0)

class ProjectModel(BaseModel):
    """Pydantic model for project representation"""
    project_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    memory_count: int = 0

class CreateProjectRequest(BaseModel):
    """Request schema for creating a new project"""
    name: str = Field(..., description="Project name", max_length=200)
    description: Optional[str] = Field(None, description="Optional project description")

class ProjectSummary(BaseModel):
    """Lightweight project representation"""
    project_id: str
    name: str
    memory_count: int
    created_at: datetime
