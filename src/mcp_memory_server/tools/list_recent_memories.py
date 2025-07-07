"""
ListRecentMemoriesTool: Implementation of list_recent_memories MCP tool

This tool lists the most recently added memories for introspection
and debugging purposes.

Agent Guidance:
- Use for debugging and understanding memory bank state
- Helpful for reviewing recent additions and memory creation patterns
- Provides chronological view of memory bank contents
- Introspection tool - not part of core two-stage retrieval workflow
"""

import json
import logging
from typing import Any, Dict
from mcp.types import Tool, TextContent

from ..models.memory import ListRecentMemoriesRequest, ListRecentMemoriesResponse
from ..services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class ListRecentMemoriesTool:
    """MCP tool for listing recently added memories"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
    
    def get_tool_definition(self) -> Tool:
        """Get the MCP tool definition"""
        return Tool(
            name="list_recent_memories",
            description="Lists the most recently added memories for introspection and debugging purposes. Returns memory previews ordered by creation date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "The maximum number of recent memories to return (1-100).",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10
                    }
                },
                "required": []
            }
        )
    
    async def call_tool(self, arguments: Dict[str, Any]) -> TextContent:
        """
        Execute the list_recent_memories tool
        
        Args:
            arguments: Tool arguments containing limit parameter
            
        Returns:
            TextContent with the recent memories
        """
        try:
            # Validate and parse arguments
            request = ListRecentMemoriesRequest(**arguments)
            
            # Call memory service
            response = await self.memory_service.list_recent_memories(request)
            
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
                "total_count": response.total_count
            }
            
            return TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
            
        except ValueError as e:
            logger.error(f"Validation error in list_recent_memories: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "memories": [],
                    "total_count": 0,
                    "error": f"Validation error: {str(e)}"
                }, indent=2)
            )
        except Exception as e:
            logger.error(f"Unexpected error in list_recent_memories: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "memories": [],
                    "total_count": 0,
                    "error": f"Internal error: {str(e)}"
                }, indent=2)
            )
