"""
SearchMemoryPreviewTool: Implementation of search_memory_preview MCP tool

This tool performs semantic search and returns token-efficient previews
of relevant memories (Stage 1 of Two-Stage Retrieval).

Agent Guidance:
- Use this tool to discover relevant memories without consuming many tokens
- Formulate queries as specific questions or problem statements
- Use previews to decide which memories warrant full retrieval
- Part of the two-stage retrieval cognitive workflow
"""

import json
import logging
from typing import Any, Dict
from mcp.types import Tool, TextContent

from ..models.memory import SearchMemoryRequest, SearchMemoryResponse
from ..services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class SearchMemoryPreviewTool:
    """MCP tool for searching memory previews (Stage 1 of Two-Stage Retrieval)"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
    
    def get_tool_definition(self) -> Tool:
        """Get the MCP tool definition with comprehensive search guidance"""
        return Tool(
            name="search_memory_preview",
            description="""Searches the memory bank using semantic search and returns token-efficient previews of relevant memories. This is Stage 1 of the Two-Stage Retrieval process.

            SEARCH STRATEGY GUIDANCE:
            - Formulate queries as specific questions: "How to debug React hooks?" vs "React"
            - Include key concepts and context: "Python async error handling patterns"
            - Start broad, then refine: First "API authentication", then "OAuth JWT implementation"
            - Use natural language: "steps to set up PostgreSQL locally"
            
            TWO-STAGE RETRIEVAL WORKFLOW:
            1. Call this tool to get lightweight previews (titles + summaries)
            2. Review previews to identify the most relevant memories  
            3. Use get_full_memory_by_ids to retrieve complete content of selected memories
            4. Integrate full content into your current context and reasoning
            
            TOKEN EFFICIENCY:
            - Previews show only title + summary to conserve tokens
            - Only retrieve full content for memories you actually need
            - Use previews to filter and prioritize before full retrieval""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query formulated as a specific question or problem statement. Examples: 'How to handle API rate limiting?', 'Python unit testing best practices', 'debugging React state issues'. Be specific about what information you're looking for."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The maximum number of memory previews to return. Start with 5-10 for focused searches, increase if you need more options to choose from.",
                        "minimum": 1,
                        "maximum": 20,
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    
    async def call_tool(self, arguments: Dict[str, Any]) -> TextContent:
        """
        Execute the search_memory_preview tool
        
        Args:
            arguments: Tool arguments containing search parameters
            
        Returns:
            TextContent with the search results
        """
        try:
            # Validate and parse arguments
            request = SearchMemoryRequest(**arguments)
            
            # Call memory service
            response = await self.memory_service.search_memory_preview(request)
            
            # Convert to JSON-serializable format (canonical schema)
            result = {
                "memories": [
                    {
                        "memory_id": mem.memory_id,
                        "title": mem.title,
                        "summary": mem.summary,
                        "created_at": mem.created_at.isoformat()
                    }
                    for mem in response.memories
                ],
                "total_found": response.total_found,
                "query": response.query
            }
            
            return TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
            
        except ValueError as e:
            logger.error(f"Validation error in search_memory_preview: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "memories": [],
                    "total_found": 0,
                    "query": arguments.get("query", ""),
                    "error": f"Validation error: {str(e)}"
                }, indent=2)
            )
        except Exception as e:
            logger.error(f"Unexpected error in search_memory_preview: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "memories": [],
                    "total_found": 0,
                    "query": arguments.get("query", ""),
                    "error": f"Internal error: {str(e)}"
                }, indent=2)
            )
