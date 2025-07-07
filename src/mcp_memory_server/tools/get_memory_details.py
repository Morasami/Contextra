"""
GetMemoryDetailsTool: Implementation of get_memory_details MCP tool

This tool retrieves full details of a specific memory including metadata
and processing information for deep inspection.
"""

import json
import logging
from typing import Any, Dict
from mcp.types import Tool, TextContent

from ..models.memory import GetMemoryDetailsRequest, GetMemoryDetailsResponse
from ..services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class GetMemoryDetailsTool:
    """MCP tool for retrieving detailed information about a specific memory"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
    
    def get_tool_definition(self) -> Tool:
        """Get the MCP tool definition"""
        return Tool(
            name="get_memory_details",
            description="Retrieves full details of a specific memory including all metadata and processing information for deep inspection and debugging.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "string",
                        "description": "The ID of the memory to retrieve details for."
                    }
                },
                "required": ["memory_id"]
            }
        )
    
    async def call_tool(self, arguments: Dict[str, Any]) -> TextContent:
        """
        Execute the get_memory_details tool
        
        Args:
            arguments: Tool arguments containing memory ID
            
        Returns:
            TextContent with the memory details
        """
        try:
            # Validate and parse arguments
            request = GetMemoryDetailsRequest(**arguments)
            
            # Call memory service
            response = await self.memory_service.get_memory_details(request)
            
            # Convert to JSON-serializable format (canonical schema)
            result = {
                "memory": {
                    "memory_id": response.memory.memory_id,
                    "title": response.memory.title,
                    "summary": response.memory.summary,
                    "full_content": response.memory.full_content,
                    "created_at": response.memory.created_at.isoformat(),
                    "updated_at": response.memory.updated_at.isoformat()
                }
            }
            
            return TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
            
        except ValueError as e:
            logger.error(f"Validation error in get_memory_details: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "memory": None,
                    "error": f"Validation error: {str(e)}"
                }, indent=2)
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_memory_details: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "memory": None,
                    "error": f"Internal error: {str(e)}"
                }, indent=2)
            )
