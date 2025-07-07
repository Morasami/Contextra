"""
Configuration management for Contextra MCP Memory Server

This module handles all configuration settings, environment variables,
and provides configuration classes for different deployment modes.

Default Mode: Lightweight (SQLite + ChromaDB + Native Python)
Advanced Mode: Production (PostgreSQL + Weaviate + Docker)
"""

import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class AppConfig(BaseSettings):
    """Main application configuration"""
    
    # Deployment Mode - DEFAULT TO LIGHTWEIGHT
    app_mode: str = Field(default="development", env="APP_MODE")  # development or production
    
    # Lightweight Mode (enabled by default)
    lightweight_mode: bool = Field(default=True, env="LIGHTWEIGHT_MODE")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.app_mode.lower() == "production"
    
    @property
    def is_lightweight(self) -> bool:
        """Check if running in lightweight mode"""
        return self.lightweight_mode or not self.is_production


class DatabaseConfig(BaseSettings):
    """Database configuration settings"""
    
    # SQLite Configuration (DEFAULT - Lightweight Mode)
    sqlite_path: str = Field(default="./data/contextra.db", env="SQLITE_PATH")
    
    # PostgreSQL Configuration (Production Mode Only)
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="contextra", env="POSTGRES_DB")
    postgres_user: str = Field(default="contextra_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="contextra_pass", env="POSTGRES_PASSWORD")
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @property
    def async_postgres_url(self) -> str:
        """Get async PostgreSQL connection URL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class VectorDatabaseConfig(BaseSettings):
    """Vector database configuration settings"""
    
    # ChromaDB Configuration (DEFAULT - Lightweight Mode)
    chromadb_path: str = Field(default="./data/chromadb", env="CHROMADB_PATH")
    
    # Weaviate Configuration (Production Mode Only)
    weaviate_url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")


class MCPServerConfig(BaseSettings):
    """MCP Server configuration settings"""
    
    # Server Settings (MCP stdio server - no port needed)
    mcp_debug: bool = Field(default=False, env="MCP_DEBUG")
    
    # Memory Processing Settings (Simplified)
    default_embedding_model: str = Field(default="all-MiniLM-L6-v2", env="DEFAULT_EMBEDDING_MODEL")
    max_search_results: int = Field(default=10, env="MAX_SEARCH_RESULTS")
    embedding_batch_size: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")


class Config:
    """Main configuration class that combines all configuration sections"""
    
    def __init__(self):
        # Load environment variables from .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize configuration sections
        self.app = AppConfig()
        self.database = DatabaseConfig()
        self.vector_db = VectorDatabaseConfig()
        self.mcp_server = MCPServerConfig()
        
        # Ensure data directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        directories = [
            Path(self.database.sqlite_path).parent,
            Path(self.vector_db.chromadb_path),
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_lightweight_mode(self) -> bool:
        """Check if running in lightweight mode"""
        return self.app.is_lightweight
    
    @property
    def is_production_mode(self) -> bool:
        """Check if running in production mode"""
        return self.app.is_production
    
    @property
    def database_url(self) -> str:
        """Get the appropriate database URL based on mode"""
        if self.is_lightweight_mode:
            return f"sqlite:///{self.database.sqlite_path}"
        else:
            return self.database.postgres_url
    
    @property
    def async_database_url(self) -> str:
        """Get the appropriate async database URL based on mode"""
        if self.is_lightweight_mode:
            return f"sqlite+aiosqlite:///{self.database.sqlite_path}"
        else:
            return self.database.async_postgres_url


# Global configuration instance
config = Config()
