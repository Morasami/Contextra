"""
GetFullMemoryByIdsTool: Implementation of get_full_memory_by_ids MCP tool

This tool retrieves the full content of specific memories by their IDs
(Stage 2 of Two-Stage Retrieval).

Agent Guidance:
- Use this ONLY after search_memory_preview has identified relevant memories
- Selective retrieval: only request IDs for memories you actually need
- Integrates full content into current context for reasoning and responses
- Token-intensive operation - use judiciously
"""

import json
import logging
from typing import Any, Dict, List
from mcp.types import Tool, TextContent

from ..models.memory import GetFullMemoryRequest, GetFullMemoryResponse
from ..services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class GetFullMemoryByIdsTool:
    """MCP tool for retrieving full memory content by IDs (Stage 2 of Two-Stage Retrieval)"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
    
    def get_tool_definition(self) -> Tool:
        """Get the MCP tool definition with stage 2 retrieval guidance"""
        return Tool(
            name="get_full_memory_by_ids",
            description="""Retrieves the full content of specific memories by their IDs. This is Stage 2 of the Two-Stage Retrieval process - use after search_memory_preview.

            SELECTIVE RETRIEVAL GUIDANCE:
            - Only request IDs for memories you determined are relevant from previews
            - Be selective: each memory adds significant tokens to your context
            - Prioritize the most relevant memories if you have many options
            - Use full content to inform your current reasoning and responses
            
            TWO-STAGE WORKFLOW:
            1. ✅ Already completed: search_memory_preview returned previews
            2. ➡️ Current step: Select specific memory IDs based on preview relevance  
            3. 🎯 This tool: Retrieve complete content for selected memories
            4. 🧠 Next: Integrate full content into your reasoning and response
            
            TOKEN MANAGEMENT:
            - Full content can be extensive - only retrieve what you need
            - Review previews carefully before deciding which IDs to request
            - Consider starting with 1-3 most relevant memories""",
            inputSchema={
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of memory IDs to retrieve full content for. These IDs should come from search_memory_preview results. Be selective - only include IDs for memories you determined are relevant based on their titles and summaries.",
                        "minItems": 1,
                        "maxItems": 10
                    }
                },
                "required": ["ids"]
            }
        )
    
    async def call_tool(self, arguments: Dict[str, Any]) -> TextContent:
        """
        Execute the get_full_memory_by_ids tool
        
        Args:
            arguments: Tool arguments containing memory IDs
            
        Returns:
            TextContent with the full memory details
        """
        try:
            # Validate and parse arguments
            request = GetFullMemoryRequest(**arguments)
            
            # Call memory service
            response = await self.memory_service.get_full_memory_by_ids(request)
            
            # Convert to JSON-serializable format (canonical schema)
            result = {
                "memories": [
                    {
                        "memory_id": mem.memory_id,
                        "title": mem.title,
                        "summary": mem.summary,
                        "full_content": mem.full_content,
                        "created_at": mem.created_at.isoformat(),
                        "updated_at": mem.updated_at.isoformat()
                    }
                    for mem in response.memories
                ]
            }
            
            return TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )
            
        except ValueError as e:
            logger.error(f"Validation error in get_full_memory_by_ids: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "memories": [],
                    "error": f"Validation error: {str(e)}"
                }, indent=2)
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_full_memory_by_ids: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "memories": [],
                    "error": f"Internal error: {str(e)}"
                }, indent=2)
            )
