"""
WriteMemoryTool: Implementation of write_memory MCP tool

This tool stores new memories in the persistent memory bank using the canonical
simplified schema: title, summary, full_content only.

Agent Guidance:
- The agent should perform distillation and summarization BEFORE calling this tool
- This tool stores pre-processed information, not raw conversational data
- Focus on creating searchable, valuable memories for future retrieval
"""

import json
import logging
from typing import Any, Dict
from mcp.types import Tool, TextContent

from ..models.memory import WriteMemoryRequest, WriteMemoryResponse
from ..services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class WriteMemoryTool:
    """MCP tool for writing memories to the persistent store (Canonical Schema)"""
    
    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
    
    def get_tool_definition(self) -> Tool:
        """Get the MCP tool definition with comprehensive agent guidance"""
        return Tool(
            name="write_memory",
            description="""Stores a new piece of information into the persistent memory bank. The agent should distill and summarize information BEFORE calling this tool.

            MEMORY CREATION GUIDANCE:
            - Save information that is valuable for future reference: insights, solutions, decisions, patterns, learnings
            - Focus on actionable, specific content rather than general conversation
            - Ensure the memory is self-contained and understandable without external context
            - Create memories that your future self would find useful for similar situations
            
            TWO-STAGE RETRIEVAL OPTIMIZATION:
            - The 'summary' will be used for search previews (Stage 1) - make it informative and keyword-rich
            - The 'full_content' will be retrieved when needed (Stage 2) - include complete context
            - Balance brevity in summary with completeness in full_content""",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "A concise, keyword-rich title that captures the essence of the memory. Should be easily searchable and understandable at a glance. Think of this as the 'headline' that will help you find this memory later. Max 10 words recommended.",
                        "maxLength": 200
                    },
                    "summary": {
                        "type": "string", 
                        "description": "A brief, factual summary that captures the key points of the memory. This will be shown in search previews, so make it informative enough to judge relevance. Include key entities, actions, and outcomes. Focus on searchable keywords. 1-2 sentences recommended.",
                        "maxLength": 500
                    },
                    "full_content": {
                        "type": "string",
                        "description": "The complete, detailed content of the memory. This should contain all relevant information needed for full context when retrieved. Include code snippets, detailed explanations, step-by-step processes, or any other comprehensive information."
                    }
                },
                "required": ["title", "summary", "full_content"]
            }
        )
    
    async def call_tool(self, arguments: Dict[str, Any]) -> TextContent:
        """
        Execute the write_memory tool
        
        Args:
            arguments: Tool arguments containing memory data
            
        Returns:
            TextContent with the operation result
        """
        try:
            # Validate and parse arguments
            request = WriteMemoryRequest(**arguments)
            
            # Call memory service
            response = await self.memory_service.write_memory(request)
            
            # Return response as JSON
            return TextContent(
                type="text",
                text=json.dumps({
                    "success": response.success,
                    "memory_id": response.memory_id,
                    "message": response.message
                }, indent=2)
            )
            
        except ValueError as e:
            logger.error(f"Validation error in write_memory: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "memory_id": "",
                    "message": f"Validation error: {str(e)}"
                }, indent=2)
            )
        except Exception as e:
            logger.error(f"Unexpected error in write_memory: {e}")
            return TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "memory_id": "",
                    "message": f"Internal error: {str(e)}"
                }, indent=2)
            )
