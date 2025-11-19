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
        ),

        # Task 5: Backend Management Tools
        types.Tool(
            name="backend_discover",
            description="Discover and register available AI workflow backends from environment",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "Optional path to backend configuration file"
                    }
                }
            }
        ),

        types.Tool(
            name="backend_connect",
            description="Connect to a specific backend",
            inputSchema={
                "type": "object",
                "properties": {
                    "backend_type": {
                        "type": "string",
                        "enum": ["flowise", "langflow"],
                        "description": "Backend type to connect"
                    },
                    "base_url": {
                        "type": "string",
                        "description": "Backend base URL"
                    },
                    "api_key": {
                        "type": "string",
                        "description": "Optional API key"
                    }
                },
                "required": ["backend_type", "base_url"]
            }
        ),

        types.Tool(
            name="backend_performance_compare",
            description="Compare performance metrics across all backends",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["latency", "success_rate", "throughput"],
                        "default": "latency",
                        "description": "Metric to compare"
                    },
                    "time_range": {
                        "type": "string",
                        "enum": ["1h", "24h", "7d"],
                        "default": "24h",
                        "description": "Time range for comparison"
                    }
                }
            }
        ),

        # Task 6: Admin Intelligence Tools
        types.Tool(
            name="flowise_admin_dashboard",
            description="Get analytics dashboard with flow usage and performance metrics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),

        types.Tool(
            name="flowise_analyze_flow",
            description="Analyze performance metrics for a specific flow",
            inputSchema={
                "type": "object",
                "properties": {
                    "flow_id": {
                        "type": "string",
                        "description": "Flow ID to analyze"
                    }
                },
                "required": ["flow_id"]
            }
        ),

        types.Tool(
            name="flowise_discover_flows",
            description="Discover flows from database with usage analytics",
            inputSchema={
                "type": "object",
                "properties": {
                    "min_messages": {
                        "type": "integer",
                        "default": 10,
                        "description": "Minimum message count"
                    },
                    "include_inactive": {
                        "type": "boolean",
                        "default": False,
                        "description": "Include inactive flows"
                    }
                }
            }
        ),

        types.Tool(
            name="flowise_sync_config",
            description="Sync flow registry with database-discovered flows",
            inputSchema={
                "type": "object",
                "properties": {
                    "dry_run": {
                        "type": "boolean",
                        "default": True,
                        "description": "Preview without applying"
                    }
                }
            }
        ),

        types.Tool(
            name="flowise_export_metrics",
            description="Export flow performance metrics in structured format",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "default": "json",
                        "description": "Export format"
                    },
                    "flows": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Flow IDs to export (empty = all)"
                    }
                }
            }
        ),

        types.Tool(
            name="flowise_pattern_analysis",
            description="Analyze conversation patterns to identify optimization opportunities",
            inputSchema={
                "type": "object",
                "properties": {
                    "flow_id": {
                        "type": "string",
                        "description": "Analyze specific flow (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum patterns to analyze"
                    }
                }
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

        # Task 5: Backend Management Tools
        elif name == "backend_discover":
            return await handle_backend_discover(arguments)

        elif name == "backend_connect":
            return await handle_backend_connect(arguments)

        elif name == "backend_performance_compare":
            return await handle_backend_performance_compare(arguments)

        # Task 6: Admin Intelligence Tools
        elif name == "flowise_admin_dashboard":
            return await handle_flowise_admin_dashboard(arguments)

        elif name == "flowise_analyze_flow":
            return await handle_flowise_analyze_flow(arguments)

        elif name == "flowise_discover_flows":
            return await handle_flowise_discover_flows(arguments)

        elif name == "flowise_sync_config":
            return await handle_flowise_sync_config(arguments)

        elif name == "flowise_export_metrics":
            return await handle_flowise_export_metrics(arguments)

        elif name == "flowise_pattern_analysis":
            return await handle_flowise_pattern_analysis(arguments)

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


# Task 5: Backend Management Tool Handlers

async def handle_backend_discover(arguments: dict) -> List[types.TextContent]:
    """Discover and register available backends"""

    # Re-discover backends from environment
    await universal_server.backend_registry.discover_backends()

    # Try to connect to all discovered backends
    backends_to_connect = {}

    if os.getenv('FLOWISE_ENABLED', 'true').lower() == 'true':
        flowise_config = {
            'base_url': os.getenv('FLOWISE_API_URL', 'http://localhost:3000'),
            'api_key': os.getenv('FLOWISE_API_KEY', '')
        }
        backends_to_connect[BackendType.FLOWISE] = flowise_config

    if os.getenv('LANGFLOW_ENABLED', 'true').lower() == 'true':
        langflow_config = {
            'base_url': os.getenv('LANGFLOW_API_URL', 'http://localhost:7860'),
            'api_key': os.getenv('LANGFLOW_API_KEY', '')
        }
        backends_to_connect[BackendType.LANGFLOW] = langflow_config

    connection_results = await universal_server.backend_registry.connect_all_backends(backends_to_connect)

    response_text = "**Backend Discovery Results**\n\n"

    for backend_type, connected in connection_results.items():
        status = "✅ Connected" if connected else "❌ Failed"
        response_text += f"- {backend_type.value}: {status}\n"

    connected_count = sum(connection_results.values())
    total_count = len(connection_results)

    response_text += f"\n**Summary**: {connected_count}/{total_count} backends connected"

    return [types.TextContent(type="text", text=response_text)]


async def handle_backend_connect(arguments: dict) -> List[types.TextContent]:
    """Connect to a specific backend"""

    backend_type_str = arguments["backend_type"]
    base_url = arguments["base_url"]
    api_key = arguments.get("api_key", "")

    # Map string to BackendType enum
    backend_type = BackendType.FLOWISE if backend_type_str == "flowise" else BackendType.LANGFLOW

    # Connect to the backend
    config = {"base_url": base_url, "api_key": api_key}
    connection_results = await universal_server.backend_registry.connect_all_backends({backend_type: config})

    connected = connection_results.get(backend_type, False)

    if connected:
        response_text = f"✅ Successfully connected to {backend_type_str} at {base_url}"

        # Try to discover flows
        try:
            backend = universal_server.backend_registry.backends[backend_type]
            flows = await backend.discover_flows()
            response_text += f"\n\n**Discovered**: {len(flows)} flows"
        except Exception as e:
            response_text += f"\n\n⚠️ Connected but flow discovery failed: {str(e)}"
    else:
        response_text = f"❌ Failed to connect to {backend_type_str} at {base_url}"

    return [types.TextContent(type="text", text=response_text)]


async def handle_backend_performance_compare(arguments: dict) -> List[types.TextContent]:
    """Compare performance metrics across backends"""

    metric = arguments.get("metric", "latency")
    time_range = arguments.get("time_range", "24h")

    response_text = f"**Backend Performance Comparison**\n\n"
    response_text += f"Metric: {metric}\n"
    response_text += f"Time Range: {time_range}\n\n"

    # Get all connected backends
    backends = universal_server.backend_registry.backends

    if not backends:
        return [types.TextContent(
            type="text",
            text="No backends connected. Cannot compare performance."
        )]

    comparison_data = []

    for backend_type, backend in backends.items():
        if backend.is_connected:
            # Get performance metrics
            perf_metrics = backend.get_performance_metrics()

            comparison_data.append({
                "backend": backend_type.value,
                "avg_latency_ms": perf_metrics.get("avg_latency_ms", 0),
                "success_rate": perf_metrics.get("success_rate", 0),
                "total_requests": perf_metrics.get("total_requests", 0)
            })

    if not comparison_data:
        return [types.TextContent(
            type="text",
            text="No performance data available for connected backends."
        )]

    # Display comparison
    for data in comparison_data:
        response_text += f"**{data['backend'].upper()}**:\n"
        response_text += f"- Average Latency: {data['avg_latency_ms']}ms\n"
        response_text += f"- Success Rate: {data['success_rate']:.1%}\n"
        response_text += f"- Total Requests: {data['total_requests']}\n\n"

    # Add recommendation
    if len(comparison_data) > 1:
        best_latency = min(comparison_data, key=lambda x: x['avg_latency_ms'] if x['avg_latency_ms'] > 0 else float('inf'))
        if best_latency['avg_latency_ms'] > 0:
            response_text += f"**Recommendation**: {best_latency['backend']} shows best latency performance\n"

    return [types.TextContent(type="text", text=response_text)]


# Task 6: Admin Intelligence Tool Handlers

async def handle_flowise_admin_dashboard(arguments: dict) -> List[types.TextContent]:
    """Get Flowise admin dashboard data"""

    try:
        # Check if Flowise backend is available and connected
        flowise_backend = universal_server.backend_registry.backends.get(BackendType.FLOWISE)

        if not flowise_backend or not flowise_backend.is_connected:
            return [types.TextContent(
                type="text",
                text="❌ Flowise backend not connected. Cannot access admin dashboard."
            )]

        # Get dashboard data from Flowise backend
        dashboard_data = flowise_backend.get_admin_dashboard_data()

        if "error" in dashboard_data:
            return [types.TextContent(
                type="text",
                text=f"❌ Error retrieving dashboard: {dashboard_data['error']}"
            )]

        # Format response
        response_text = "**Flowise Admin Dashboard**\n\n"

        stats = dashboard_data.get("statistics", {})
        response_text += f"**Statistics**:\n"
        response_text += f"- Total Messages: {stats.get('total_messages', 0):,}\n"
        response_text += f"- Total Flows: {stats.get('total_flows', 0)}\n"
        response_text += f"- Active Flows: {stats.get('active_flows', 0)}\n"
        response_text += f"- Date Range: {stats.get('earliest_date', 'N/A')} to {stats.get('latest_date', 'N/A')}\n\n"

        # Top flows
        top_flows = dashboard_data.get("top_flows", [])
        if top_flows:
            response_text += "**Top Flows by Usage**:\n"
            for i, flow in enumerate(top_flows[:5], 1):
                response_text += f"{i}. {flow.get('name', 'Unknown')}: {flow.get('message_count', 0)} messages\n"
            response_text += "\n"

        # Performance summary
        perf = dashboard_data.get("performance_summary", {})
        if perf:
            response_text += "**Performance**:\n"
            response_text += f"- Average Success Rate: {perf.get('avg_success_rate', 0):.1%}\n"
            response_text += f"- Average Engagement: {perf.get('avg_engagement', 0):.1%}\n"

        return [types.TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def handle_flowise_analyze_flow(arguments: dict) -> List[types.TextContent]:
    """Analyze a specific Flowise flow"""

    flow_id = arguments["flow_id"]

    try:
        flowise_backend = universal_server.backend_registry.backends.get(BackendType.FLOWISE)

        if not flowise_backend or not flowise_backend.is_connected:
            return [types.TextContent(
                type="text",
                text="❌ Flowise backend not connected."
            )]

        # Get flow analysis
        analysis = flowise_backend.analyze_flow_performance(flow_id)

        if "error" in analysis:
            return [types.TextContent(
                type="text",
                text=f"❌ Error analyzing flow: {analysis['error']}"
            )]

        response_text = f"**Flow Analysis: {flow_id}**\n\n"

        response_text += f"**Name**: {analysis.get('name', 'Unknown')}\n"
        response_text += f"**Total Messages**: {analysis.get('message_count', 0)}\n"
        response_text += f"**Success Score**: {analysis.get('success_score', 0):.2f}\n"
        response_text += f"**Engagement Score**: {analysis.get('engagement_score', 0):.2f}\n"
        response_text += f"**Status**: {analysis.get('status', 'Unknown')}\n\n"

        # Recommendations
        recommendations = analysis.get('recommendations', [])
        if recommendations:
            response_text += "**Recommendations**:\n"
            for rec in recommendations:
                response_text += f"- {rec}\n"

        return [types.TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Flow analysis error: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def handle_flowise_discover_flows(arguments: dict) -> List[types.TextContent]:
    """Discover Flowise flows from database"""

    min_messages = arguments.get("min_messages", 10)
    include_inactive = arguments.get("include_inactive", False)

    try:
        flowise_backend = universal_server.backend_registry.backends.get(BackendType.FLOWISE)

        if not flowise_backend or not flowise_backend.is_connected:
            return [types.TextContent(
                type="text",
                text="❌ Flowise backend not connected."
            )]

        # Discover flows from database
        flows = flowise_backend.discover_flows_from_database(
            min_messages=min_messages,
            include_inactive=include_inactive
        )

        response_text = f"**Discovered Flows** (min messages: {min_messages})\n\n"

        if flows:
            for flow in flows:
                status_icon = "✅" if flow.get('active') else "⚠️"
                response_text += f"{status_icon} **{flow.get('name', 'Unknown')}**\n"
                response_text += f"   ID: {flow.get('id', 'unknown')}\n"
                response_text += f"   Messages: {flow.get('message_count', 0)}\n"
                response_text += f"   Success Score: {flow.get('success_score', 0):.2f}\n\n"

            response_text += f"**Total**: {len(flows)} flows discovered"
        else:
            response_text += "No flows found matching criteria."

        return [types.TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Flow discovery error: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def handle_flowise_sync_config(arguments: dict) -> List[types.TextContent]:
    """Sync Flowise flow registry with database"""

    dry_run = arguments.get("dry_run", True)

    try:
        flowise_backend = universal_server.backend_registry.backends.get(BackendType.FLOWISE)

        if not flowise_backend or not flowise_backend.is_connected:
            return [types.TextContent(
                type="text",
                text="❌ Flowise backend not connected."
            )]

        # Perform sync
        sync_result = flowise_backend.sync_flow_configurations(dry_run=dry_run)

        if "error" in sync_result:
            return [types.TextContent(
                type="text",
                text=f"❌ Sync error: {sync_result['error']}"
            )]

        mode = "Preview" if dry_run else "Applied"
        response_text = f"**Flow Configuration Sync - {mode}**\n\n"

        response_text += f"**Changes**:\n"
        response_text += f"- Flows to Add: {sync_result.get('flows_to_add', 0)}\n"
        response_text += f"- Flows to Update: {sync_result.get('flows_to_update', 0)}\n"
        response_text += f"- Flows to Remove: {sync_result.get('flows_to_remove', 0)}\n\n"

        if dry_run:
            response_text += "ℹ️ This was a preview. Set dry_run=false to apply changes."

        return [types.TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Sync error: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def handle_flowise_export_metrics(arguments: dict) -> List[types.TextContent]:
    """Export Flowise flow metrics"""

    format_type = arguments.get("format", "json")
    flow_ids = arguments.get("flows", [])

    try:
        flowise_backend = universal_server.backend_registry.backends.get(BackendType.FLOWISE)

        if not flowise_backend or not flowise_backend.is_connected:
            return [types.TextContent(
                type="text",
                text="❌ Flowise backend not connected."
            )]

        # Export metrics
        metrics = flowise_backend.export_flow_metrics(
            flow_ids=flow_ids if flow_ids else None,
            format=format_type
        )

        if "error" in metrics:
            return [types.TextContent(
                type="text",
                text=f"❌ Export error: {metrics['error']}"
            )]

        response_text = f"**Flow Metrics Export** ({format_type})\n\n"

        if format_type == "json":
            import json
            response_text += "```json\n"
            response_text += json.dumps(metrics, indent=2)
            response_text += "\n```"
        else:
            response_text += metrics.get("csv_data", "No data")

        return [types.TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Export error: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


async def handle_flowise_pattern_analysis(arguments: dict) -> List[types.TextContent]:
    """Analyze conversation patterns"""

    flow_id = arguments.get("flow_id")
    limit = arguments.get("limit", 100)

    try:
        flowise_backend = universal_server.backend_registry.backends.get(BackendType.FLOWISE)

        if not flowise_backend or not flowise_backend.is_connected:
            return [types.TextContent(
                type="text",
                text="❌ Flowise backend not connected."
            )]

        # Analyze patterns
        patterns = flowise_backend.analyze_conversation_patterns(
            flow_id=flow_id,
            limit=limit
        )

        if "error" in patterns:
            return [types.TextContent(
                type="text",
                text=f"❌ Analysis error: {patterns['error']}"
            )]

        scope = f"Flow: {flow_id}" if flow_id else "All Flows"
        response_text = f"**Conversation Pattern Analysis**\n{scope}\n\n"

        # Common intents
        intents = patterns.get("common_intents", [])
        if intents:
            response_text += "**Common Intents**:\n"
            for intent in intents[:5]:
                response_text += f"- {intent.get('intent', 'unknown')}: {intent.get('count', 0)} occurrences\n"
            response_text += "\n"

        # Recommendations
        recommendations = patterns.get("optimization_recommendations", [])
        if recommendations:
            response_text += "**Optimization Opportunities**:\n"
            for rec in recommendations:
                response_text += f"- {rec}\n"

        return [types.TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Error: {str(e)}"
        )]


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
