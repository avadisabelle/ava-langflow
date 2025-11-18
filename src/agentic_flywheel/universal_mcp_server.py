#!/usr/bin/env python3
"""
Universal MCP Server for Agentic Flywheel
Integrates multiple backends (Flowise, Langflow) with intelligent routing,
tracing, and state persistence.
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp import server, types
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
import mcp.server.stdio

# Import our universal components
from agentic_flywheel.backends import BackendRegistry, BackendType
from agentic_flywheel.mcp_tools import UniversalQueryHandler
from agentic_flywheel.integrations import (
    RedisSessionManager,
    RedisExecutionCache,
    RedisConfig,
    LangfuseTracerManager,
    trace_mcp_tool
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UniversalMCPServer:
    """
    Universal MCP Server with multi-backend support

    Features:
    - Intelligent query routing across Flowise and Langflow
    - Session persistence via Redis
    - Observability via Langfuse tracing
    - Backend health monitoring
    - Flow discovery and management
    """

    def __init__(self):
        """Initialize universal MCP server"""
        self.backend_registry = None
        self.query_handler = None
        self.redis_session_mgr = None
        self.redis_execution_cache = None
        self.tracer = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize all components"""
        if self.is_initialized:
            return

        logger.info("🚀 Initializing Universal MCP Server...")

        # Initialize backend registry
        self.backend_registry = BackendRegistry()
        await self.backend_registry.discover_backends()

        # Connect to backends based on environment configuration
        backends_to_connect = {}

        # Flowise configuration
        if os.getenv('FLOWISE_ENABLED', 'true').lower() == 'true':
            flowise_config = {
                'base_url': os.getenv('FLOWISE_API_URL', 'http://localhost:3000'),
                'api_key': os.getenv('FLOWISE_API_KEY', '')
            }
            backends_to_connect[BackendType.FLOWISE] = flowise_config

        # Langflow configuration
        if os.getenv('LANGFLOW_ENABLED', 'true').lower() == 'true':
            langflow_config = {
                'base_url': os.getenv('LANGFLOW_API_URL', 'http://localhost:7860'),
                'api_key': os.getenv('LANGFLOW_API_KEY', '')
            }
            backends_to_connect[BackendType.LANGFLOW] = langflow_config

        # Connect to all configured backends
        connection_results = await self.backend_registry.connect_all_backends(backends_to_connect)

        connected_count = sum(connection_results.values())
        logger.info(f"🌐 Connected to {connected_count}/{len(connection_results)} backends")

        # Initialize query handler
        self.query_handler = UniversalQueryHandler(
            backend_registry=self.backend_registry,
            enable_fallback=True,
            default_timeout=30.0
        )
        logger.info("🎯 Universal query handler initialized")

        # Initialize Redis session manager (optional)
        redis_config = RedisConfig.from_env()
        if redis_config['enabled']:
            self.redis_session_mgr = RedisSessionManager(
                enabled=True,
                ttl_seconds=redis_config['session_ttl'],
                key_prefix=redis_config['key_prefix']
            )
            self.redis_execution_cache = RedisExecutionCache(
                enabled=True,
                ttl_seconds=redis_config['execution_ttl'],
                key_prefix=redis_config['key_prefix']
            )
            logger.info("💾 Redis state persistence enabled")
        else:
            logger.info("⚠️  Redis state persistence disabled")

        # Initialize Langfuse tracer (optional)
        langfuse_enabled = os.getenv('LANGFUSE_ENABLED', 'false').lower() == 'true'
        if langfuse_enabled:
            self.tracer = LangfuseTracerManager(enabled=True)
            logger.info("📊 Langfuse tracing enabled")
        else:
            logger.info("⚠️  Langfuse tracing disabled")

        self.is_initialized = True
        logger.info("✅ Universal MCP Server initialized successfully")

    async def shutdown(self):
        """Cleanup and shutdown"""
        logger.info("🛑 Shutting down Universal MCP Server...")

        if self.backend_registry:
            await self.backend_registry.disconnect_all_backends()

        logger.info("✅ Shutdown complete")


# Create server instance
app = server.Server("universal-agentic-flywheel")
universal_server = UniversalMCPServer()


@app.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available MCP tools"""

    # Ensure server is initialized
    if not universal_server.is_initialized:
        await universal_server.initialize()

    return [
        # Main query tool
        types.Tool(
            name="universal_query",
            description="""Query AI workflows across all backends with intelligent routing.

Automatically selects optimal backend (Flowise, Langflow) based on:
- Question intent and complexity
- Backend health and availability
- Historical performance metrics
- Flow capabilities

Supports session continuity and automatic fallback on failures.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question or prompt to send to AI workflow"
                    },
                    "intent": {
                        "type": "string",
                        "description": "Optional explicit intent override",
                        "enum": [
                            "auto",
                            "creative-orientation",
                            "technical-analysis",
                            "structural-thinking",
                            "conversation",
                            "rag-retrieval",
                            "data-processing"
                        ],
                        "default": "auto"
                    },
                    "backend": {
                        "type": "string",
                        "description": "Optional backend selection (auto = intelligent routing)",
                        "enum": ["auto", "flowise", "langflow"],
                        "default": "auto"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for conversation continuity"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Flow-specific parameters",
                        "properties": {
                            "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                            "max_tokens": {"type": "integer", "minimum": 1}
                        }
                    }
                },
                "required": ["question"]
            }
        ),

        # Backend discovery tools
        types.Tool(
            name="backend_status",
            description="Get status of all registered backends including health and connection state",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        types.Tool(
            name="list_flows",
            description="List all available flows across all backends with their capabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "backend": {
                        "type": "string",
                        "description": "Filter by specific backend",
                        "enum": ["all", "flowise", "langflow"],
                        "default": "all"
                    }
                }
            }
        ),

        types.Tool(
            name="health_check",
            description="Perform health check on all backends",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        # Session management tools (if Redis enabled)
        types.Tool(
            name="list_sessions",
            description="List active sessions (requires Redis persistence)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Session ID pattern (supports wildcards)",
                        "default": "*"
                    }
                }
            }
        ),

        types.Tool(
            name="get_session",
            description="Retrieve session details (requires Redis persistence)",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Session ID to retrieve"
                    }
                },
                "required": ["session_id"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle MCP tool calls"""

    # Ensure server is initialized
    if not universal_server.is_initialized:
        await universal_server.initialize()

    try:
        if name == "universal_query":
            return await handle_universal_query(arguments)

        elif name == "backend_status":
            return await handle_backend_status(arguments)

        elif name == "list_flows":
            return await handle_list_flows(arguments)

        elif name == "health_check":
            return await handle_health_check(arguments)

        elif name == "list_sessions":
            return await handle_list_sessions(arguments)

        elif name == "get_session":
            return await handle_get_session(arguments)

        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_universal_query(arguments: dict) -> List[types.TextContent]:
    """Handle universal query with intelligent routing"""

    question = arguments["question"]
    intent = arguments.get("intent", "auto")
    backend = arguments.get("backend", "auto")
    session_id = arguments.get("session_id")
    parameters = arguments.get("parameters", {})

    # Load existing session if provided
    session = None
    if session_id and universal_server.redis_session_mgr:
        session = await universal_server.redis_session_mgr.load_session(session_id)
        if session:
            logger.info(f"📝 Resumed session: {session_id}")

    # Execute query with intelligent routing
    result = await universal_server.query_handler.execute_query(
        question=question,
        intent_override=intent if intent != "auto" else None,
        backend_override=backend if backend != "auto" else None,
        session_id=session_id,
        parameters=parameters
    )

    # Save session if persistence enabled
    if session_id and universal_server.redis_session_mgr and session:
        # Update session with new interaction
        if 'history' not in session.context:
            session.context['history'] = []
        session.context['history'].append({
            'question': question,
            'result': result.get('result', ''),
            'timestamp': asyncio.get_event_loop().time()
        })
        await universal_server.redis_session_mgr.save_session(session)

    # Format response
    metadata = result.get('_mcp_metadata', {})
    response_text = f"""**Result**: {result.get('result', result.get('error', 'No result'))}

**Routing Info**:
- Backend: {metadata.get('backend_used', 'unknown')}
- Flow: {metadata.get('flow_name', 'unknown')}
- Intent: {metadata.get('intent_classified', 'unknown')} (confidence: {metadata.get('intent_confidence', 0):.2f})
- Routing Score: {metadata.get('routing_score', 0):.2f}
- Execution Time: {metadata.get('execution_time_ms', 0)}ms
- Fallback Used: {metadata.get('fallback_used', False)}
"""

    if metadata.get('routing_breakdown'):
        breakdown = metadata['routing_breakdown']
        response_text += f"""
**Score Breakdown**:
- Flow Match: {breakdown.get('flow_match', 0):.2f}
- Health: {breakdown.get('health', 0):.2f}
- Performance: {breakdown.get('performance', 0):.2f}
- Capability: {breakdown.get('capability', 0):.2f}
"""

    return [types.TextContent(type="text", text=response_text)]


async def handle_backend_status(arguments: dict) -> List[types.TextContent]:
    """Get backend registry status"""

    status = universal_server.backend_registry.get_status()

    response_text = f"""**Backend Registry Status**

- Registered Backends: {status['registered_backends']}
- Connected: {status['connected_backends']}
- Cached Flows: {status['cached_flows']}

**Available Backends**:
"""

    for backend_type, is_healthy in status['health_status'].items():
        health_icon = "✅" if is_healthy else "❌"
        response_text += f"- {health_icon} {backend_type}\n"

    return [types.TextContent(type="text", text=response_text)]


async def handle_list_flows(arguments: dict) -> List[types.TextContent]:
    """List available flows"""

    backend_filter = arguments.get("backend", "all")

    flows_by_backend = await universal_server.backend_registry.discover_all_flows()

    response_text = "**Available Flows**\n\n"

    for backend_type, flows in flows_by_backend.items():
        if backend_filter != "all" and backend_type.value != backend_filter:
            continue

        response_text += f"**{backend_type.value.upper()}** ({len(flows)} flows):\n"

        for flow in flows:
            response_text += f"- {flow.name} ({flow.id})\n"
            response_text += f"  Description: {flow.description}\n"
            response_text += f"  Intents: {', '.join(flow.intent_keywords)}\n\n"

    return [types.TextContent(type="text", text=response_text)]


async def handle_health_check(arguments: dict) -> List[types.TextContent]:
    """Perform health check on all backends"""

    health_results = await universal_server.backend_registry.health_check_all()

    response_text = "**Health Check Results**\n\n"

    for backend_type, is_healthy in health_results.items():
        status = "✅ HEALTHY" if is_healthy else "❌ UNHEALTHY"
        response_text += f"- {backend_type.value}: {status}\n"

    healthy_count = sum(health_results.values())
    total_count = len(health_results)

    response_text += f"\n**Summary**: {healthy_count}/{total_count} backends healthy"

    return [types.TextContent(type="text", text=response_text)]


async def handle_list_sessions(arguments: dict) -> List[types.TextContent]:
    """List active sessions"""

    if not universal_server.redis_session_mgr:
        return [types.TextContent(
            type="text",
            text="Redis persistence not enabled. Cannot list sessions."
        )]

    pattern = arguments.get("pattern", "*")
    session_ids = await universal_server.redis_session_mgr.list_sessions(pattern)

    response_text = f"**Active Sessions** (pattern: {pattern})\n\n"

    if session_ids:
        for session_id in session_ids:
            response_text += f"- {session_id}\n"
        response_text += f"\n**Total**: {len(session_ids)} sessions"
    else:
        response_text += "No sessions found."

    return [types.TextContent(type="text", text=response_text)]


async def handle_get_session(arguments: dict) -> List[types.TextContent]:
    """Get session details"""

    if not universal_server.redis_session_mgr:
        return [types.TextContent(
            type="text",
            text="Redis persistence not enabled. Cannot retrieve session."
        )]

    session_id = arguments["session_id"]
    session = await universal_server.redis_session_mgr.load_session(session_id)

    if not session:
        return [types.TextContent(
            type="text",
            text=f"Session not found: {session_id}"
        )]

    response_text = f"""**Session Details**: {session_id}

- Backend: {session.backend.value}
- Status: {session.status.value if session.status else 'unknown'}
- Current Flow: {session.current_flow_id or 'none'}
- Context: {len(session.context)} items
- History: {len(session.history)} messages
"""

    return [types.TextContent(type="text", text=response_text)]


async def main():
    """Run the Universal MCP Server"""

    logger.info("🌟 Starting Universal Agentic Flywheel MCP Server")

    # Initialize server on startup
    await universal_server.initialize()

    # Run MCP server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="universal-agentic-flywheel",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

    # Cleanup on shutdown
    await universal_server.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
