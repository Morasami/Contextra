# Contextra - MCP Memory Server


[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

**Persistent memory that learns and recalls across conversations.**

Contextra is an MCP (Model Context Protocol) Memory Server that provides persistent memory capabilities for AI agents. It implements an agent-driven architecture where agents handle cognitive tasks while the server provides structured storage and retrieval.

The system features a two-stage retrieval workflow that allows agents to first preview memory summaries, then selectively retrieve full content only for relevant items. This approach helps optimize token usage while maintaining access to comprehensive information.

**Core Features:**
- Five canonical MCP tools for memory operations (write, search, retrieve, list, inspect)
- Lightweight-first design using SQLite and ChromaDB with no external dependencies
- MCP-native guidance through built-in prompts that help agents use the system effectively
- Agent-driven architecture that keeps cognitive processing with the agent
- Local-first storage with full data control and privacy

## ✅ Currently Tested and Supported

- **VS Code with GitHub Copilot** (tested and fully supported)
- Other MCP-compatible agents: _Not yet tested_

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/Morasami/Contextra.git
cd Contextra
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
python -m mcp_memory_server.server
# ✅ MCP server ready! Connect your AI agent to start building memories.
```

### Connect to VS Code/Claude

Add to your VS Code settings.json:
```json
{
  "mcp": {
    "servers": {
      "contextra": {
        "type": "stdio",
        "command": "python",
        "args": ["-m", "mcp_memory_server.server"],
        "cwd": "/path/to/Contextra/src",
        "env": {
          "PYTHONPATH": "/path/to/Contextra/src",
          "LIGHTWEIGHT_MODE": "true",
          "MCP_DEBUG": "false",
          "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": "python"
        }
      }
    }
  }
}
```

## 🧠 How It Works: Two-Stage Memory Retrieval

What Contextra does:

```
1. 🔍 SEARCH: Agent queries → Returns lightweight previews (titles + summaries)
2. 🎯 SELECT: Agent reviews previews → Chooses relevant memories  
3. 📖 RETRIEVE: Agent requests full content → Gets complete details only for selected items

Result: More efficient token usage while maintaining accuracy
```

### Example Workflow
```python
# Agent searches for relevant information
previews = await agent.call_tool("search_memory_preview", {
    "query": "Python async debugging techniques",
    "limit": 5
})
# Returns: [{"id": "mem_123", "title": "Fix async deadlocks", "summary": "..."}, ...]

# Agent selects relevant memories
full_content = await agent.call_tool("get_full_memory_by_ids", {
    "ids": ["mem_123", "mem_456"]  # Only the useful ones
})
# Returns: Complete content for efficient context building
```

## �️ Memory Tools (5 Core Functions)

### 💾 `write_memory` - Store Knowledge
Save agent-processed information with smart guidance on what's worth remembering.
```json
{
  "title": "React useEffect Infinite Loop Fix",
  "summary": "Resolved infinite re-render by adding dependency array",
  "full_content": "Problem: Component re-rendering infinitely...\nSolution: Added [userId] to dependency array..."
}
```

### 🔍 `search_memory_preview` - Find Relevant Info
Search and get lightweight previews to find what you need without token waste.
```json
{
  "query": "React debugging performance issues",
  "limit": 5
}
```

### 📖 `get_full_memory_by_ids` - Retrieve Details
Get complete content only for memories you've identified as relevant.
```json
{
  "ids": ["mem_abc123", "mem_def456"]
}
```

### 📋 `list_recent_memories` - Browse History
See what's been saved recently for context and debugging.

### 🔎 `get_memory_details` - Inspect Memory
Deep-dive into specific memory details including metadata.

## 🎯 Built-in Agent Guidance

Contextra includes 4 MCP prompts that teach your agents optimal memory practices:

- **`memory_saving_criteria`** - What information deserves to be saved
- **`summarization_guidelines`** - How to create effective, searchable summaries  
- **`retrieval_strategy`** - Best practices for two-stage retrieval
- **`token_efficiency`** - Strategies for minimizing context window usage

## ⚙️ Configuration

### 🪶 Lightweight Mode (Default)
Perfect for personal use and development:
- **Database**: SQLite (file-based, zero setup)
- **Vector Search**: ChromaDB (local, no external services)
- **Dependencies**: Just Python packages - no Docker, no cloud services
- **Capacity**: 1-1000 memories, great for individual agents

### Environment Setup
```bash
# Required for ChromaDB compatibility
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Optional customization
export SQLITE_PATH=./data/contextra.db
export CHROMADB_PATH=./data/chromadb
```


## � Project Structure

```
Contextra/
├── 📄 README.md                    # This file
├── 📄 LICENSE                      # MIT license
├── 📄 requirements.txt             # Core dependencies
├── 📄 pyproject.toml               # Package configuration
├── 📄 .env.example                 # Configuration template
├──  src/mcp_memory_server/       # Core implementation
│   ├── 🖥️ server.py                # MCP server + prompts
│   ├── ⚙️ config.py                # Configuration
│   ├── 📂 tools/                   # 5 MCP tools
│   ├── 📂 services/                # Business logic
│   └── 📂 models/                  # Data schemas
└── 📄 COMPREHENSIVE_DOCUMENTATION.md  # Full technical reference
```

## 📖 Documentation & Support

- **📋 Quick Setup Guide** - You're reading it!
- **📚 Technical Documentation** - Deep dive into architecture (not ready yet)
- **🐳 Production Deployment** - Docker & scaling guide (not ready yet)

## 🤝 Issues & Feedback

Found a bug or have a feature request? Please open an issue on GitHub! While I'm not actively seeking contributions at this time, I welcome feedback and bug reports to improve the project.

- **🐛 [Report Issues](https://github.com/Morasami/Contextra/issues)** - Bug reports and feature requests
- **💡 [Discussions](https://github.com/Morasami/Contextra/discussions)** - Questions and general feedback

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
