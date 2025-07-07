"""
Contextra MCP Memory Server

Main server implementation that implements the MCP protocol and coordinates
all memory operations through the defined tools.

Implements MCP-native guidance through:
- Rich tool descriptions with agent guidance
- MCP Prompts specification for dynamic guidance  
- Self-documenting memory management system
"""

import os
# Fix protobuf version conflict with ChromaDB
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import asyncio
import logging
from typing import Any, Sequence
import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .config import config
from .services.memory_service import MemoryService
from .tools.write_memory import WriteMemoryTool
from .tools.search_memory_preview import SearchMemoryPreviewTool
from .tools.get_full_memory_by_ids import GetFullMemoryByIdsTool
from .tools.list_recent_memories import ListRecentMemoriesTool
from .tools.get_memory_details import GetMemoryDetailsTool

logger = logging.getLogger(__name__)

class ContextraMCPServer:
    """Main MCP server class for Contextra Memory System (Canonical 5-Tool Implementation)"""
    
    def __init__(self):
        self.server = Server("contextra-mcp-memory-server")
        self.memory_service = MemoryService()
        
        # Initialize the 5 canonical tools only
        self.write_memory_tool = WriteMemoryTool(self.memory_service)
        self.search_memory_preview_tool = SearchMemoryPreviewTool(self.memory_service)
        self.get_full_memory_by_ids_tool = GetFullMemoryByIdsTool(self.memory_service)
        self.list_recent_memories_tool = ListRecentMemoriesTool(self.memory_service)
        self.get_memory_details_tool = GetMemoryDetailsTool(self.memory_service)
        
        # Register handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools (5 canonical tools)"""
            return [
                self.write_memory_tool.get_tool_definition(),
                self.search_memory_preview_tool.get_tool_definition(),
                self.get_full_memory_by_ids_tool.get_tool_definition(),
                self.list_recent_memories_tool.get_tool_definition(),
                self.get_memory_details_tool.get_tool_definition()
            ]
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> list[types.Prompt]:
            """List available MCP prompts for agent guidance"""
            return [
                types.Prompt(
                    name="memory_saving_criteria",
                    description="Guidelines for deciding what information should be saved as memories",
                    arguments=[]
                ),
                types.Prompt(
                    name="summarization_guidelines", 
                    description="Instructions for creating effective memory titles and summaries",
                    arguments=[]
                ),
                types.Prompt(
                    name="retrieval_strategy",
                    description="Best practices for the two-stage retrieval workflow",
                    arguments=[]
                ),
                types.Prompt(
                    name="token_efficiency",
                    description="Guidance for minimizing context window usage while maintaining effectiveness",
                    arguments=[]
                )
            ]
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict[str, str]) -> types.GetPromptResult:
            """Get specific prompt content for agent guidance"""
            
            if name == "memory_saving_criteria":
                return types.GetPromptResult(
                    description="Guidelines for what information should be saved as memories",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text="""When deciding what information to save as memories, consider these criteria:

SAVE when information is:
• Solutions to specific problems you solved
• Insights gained from debugging or troubleshooting  
• Architectural decisions and their reasoning
• Code patterns that work well for specific use cases
• Configuration steps that were hard to figure out
• User preferences and specific requirements
• Lessons learned from mistakes or failures
• Reusable processes or workflows

DO NOT SAVE:
• General conversational exchanges without specific insights
• Information easily found in documentation
• Temporary or context-specific details
• Personal opinions without actionable content

QUALITY OVER QUANTITY: Save fewer, higher-quality memories that will genuinely help you in future similar situations."""
                            )
                        )
                    ]
                )
            
            elif name == "summarization_guidelines":
                return types.GetPromptResult(
                    description="Instructions for creating effective memory titles and summaries",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text="""When creating memory titles and summaries:

TITLE GUIDELINES:
• Be specific and keyword-rich: "Fix React useEffect infinite loop" not "React issue"
• Include key technologies: "PostgreSQL connection pooling with Node.js"
• Focus on the main action or outcome: "Debug Python import circular dependency"
• Keep under 10 words but be descriptive

SUMMARY GUIDELINES:
• Start with the core problem or topic in the first sentence
• Include key technical details: versions, specific error messages, technologies
• Mention the solution approach or outcome briefly
• Use searchable keywords that you would naturally think of later
• Keep to 1-2 sentences but pack them with useful information

Example:
Title: "Debug Next.js hydration mismatch error"
Summary: "Resolved hydration mismatch between server and client rendering caused by dynamic content loading before useEffect. Fixed by moving dynamic content to useEffect and adding loading states."""
                            )
                        )
                    ]
                )
            
            elif name == "retrieval_strategy":
                return types.GetPromptResult(
                    description="Best practices for the two-stage retrieval workflow",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text="""Follow this two-stage retrieval workflow for efficient memory access:

STAGE 1 - DISCOVERY (search_memory_preview):
• Formulate specific queries: "how to handle authentication in Express.js"
• Start with broader terms, then narrow down if needed
• Include problem context: "debugging", "setup", "implementation"
• Review all returned previews before deciding what to retrieve
• Look for relevant keywords in titles and summaries

STAGE 2 - RETRIEVAL (get_full_memory_by_ids):
• Be selective - only retrieve memories you determined are relevant
• Start with 1-3 most promising memories to conserve tokens
• Read full content to inform your current reasoning
• Can retrieve additional memories if first batch doesn't have what you need

SEARCH STRATEGY:
• Use natural language: "steps to deploy React app to Vercel"
• Include specific technologies and contexts
• If initial search is too broad, add more specific terms
• If too narrow, try broader or alternative terms"""
                            )
                        )
                    ]
                )
            
            elif name == "token_efficiency":
                return types.GetPromptResult(
                    description="Guidance for minimizing context window usage",
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text="""Optimize token usage with these strategies:

MEMORY CREATION:
• Write concise but complete summaries - they're used for search previews
• Include essential details in summaries to enable good preview-based decisions
• Store complete context in full_content for when you actually need it

RETRIEVAL OPTIMIZATION:
• Use search_memory_preview first - previews are lightweight
• Be highly selective about which memories to retrieve fully
• Only call get_full_memory_by_ids for memories you're confident are relevant
• Consider retrieving 1-2 most relevant memories first, then more if needed

WORKFLOW EFFICIENCY:
• Trust your preview-based decisions - avoid retrieving "just in case"
• Quality titles and summaries in previews enable better filtering
• Use the full content when retrieved - don't waste the token investment
• Remember that every full memory retrieval adds significantly to your context"""
                            )
                        )
                    ]
                )
            
            else:
                raise ValueError(f"Unknown prompt: {name}")
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict[str, Any]) -> Sequence[types.TextContent]:
            """Handle tool calls (5 canonical tools only)"""
            try:
                logger.info(f"Calling tool: {name}")
                
                if name == "write_memory":
                    result = await self.write_memory_tool.call_tool(arguments)
                elif name == "search_memory_preview":
                    result = await self.search_memory_preview_tool.call_tool(arguments)
                elif name == "get_full_memory_by_ids":
                    result = await self.get_full_memory_by_ids_tool.call_tool(arguments)
                elif name == "list_recent_memories":
                    result = await self.list_recent_memories_tool.call_tool(arguments)
                elif name == "get_memory_details":
                    result = await self.get_memory_details_tool.call_tool(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}. Available tools: write_memory, search_memory_preview, get_full_memory_by_ids, list_recent_memories, get_memory_details")
                
                return [result]
                
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                # Provide helpful error guidance to agent
                error_message = f"Error in {name}: {str(e)}"
                if "validation" in str(e).lower():
                    error_message += "\n\nHint: Check that required parameters are provided and match the expected format. Review the tool definition for parameter requirements."
                elif name == "search_memory_preview" and "query" in str(e).lower():
                    error_message += "\n\nHint: Ensure your query is a descriptive string. Try formulating it as a specific question or problem statement."
                elif name == "get_full_memory_by_ids" and "ids" in str(e).lower():
                    error_message += "\n\nHint: Provide memory IDs as a list of strings. IDs should come from search_memory_preview results."
                
                return [types.TextContent(
                    type="text",
                    text=error_message
                )]
    
    async def initialize(self):
        """Initialize the MCP server and all services"""
        try:
            logger.info("Initializing Contextra MCP Memory Server")
            
            # Initialize memory service
            await self.memory_service.initialize()
            
            logger.info("Contextra MCP Memory Server initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            raise
    
    async def cleanup(self):
        """Clean up server resources"""
        try:
            await self.memory_service.cleanup()
            logger.info("Server cleanup completed")
        except Exception as e:
            logger.error(f"Error during server cleanup: {e}")
    
    async def run(self):
        """Run the MCP server"""
        try:
            await self.initialize()
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="contextra-mcp-memory-server",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.cleanup()

async def main():
    """Main entry point for the MCP Memory Server"""
    # Setup simple logging
    log_level = "INFO"
    if config.mcp_server.mcp_debug:
        log_level = "DEBUG"
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Contextra MCP Memory Server starting...")
    logger.info(f"Running in {'Lightweight' if config.is_lightweight_mode else 'Production'} Mode")
    
    # Create and run server
    server = ContextraMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
