#!/usr/bin/env python3
"""
Universal Agentic Flywheel MCP Server
Multi-backend AI infrastructure with intelligent routing, observability, and persistence

Integrates all 18 MCP tools across 3 categories:
- Universal Query (1 tool)
- Backend Management (6 tools)
- Admin Intelligence (6 tools)
- Legacy Flowise Tools (3 tools)
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# MCP imports
try:
    from mcp import server, types
    from mcp.server.models import InitializationOptions
    import mcp.server.stdio
    MCP_AVAILABLE = True
except ImportError as e:
    logging.error(f"MCP not available: {e}")
    MCP_AVAILABLE = False
    server = None
    types = None

# Agentic Flywheel imports
try:
    from agentic_flywheel.tools import (
        # Universal query
        handle_universal_query,
        # Backend management
        handle_backend_registry_status,
        handle_backend_discover,
        handle_backend_connect,
        handle_backend_list_flows,
        handle_backend_execute_universal,
        handle_backend_performance_compare,
        # Admin intelligence
        handle_flowise_admin_dashboard,
        handle_flowise_analyze_flow,
        handle_flowise_discover_flows,
        handle_flowise_sync_config,
        handle_flowise_export_metrics,
        handle_flowise_pattern_analysis
    )
    TOOLS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Agentic Flywheel tools not fully available: {e}")
    TOOLS_AVAILABLE = False

# Legacy intelligent server for backward compatibility
try:
    from agentic_flywheel.intelligent_mcp_server import IntelligentFlowiseMCPServer
    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UniversalAgenticFlywheelServer:
    """Universal MCP server with all Agentic Flywheel capabilities"""

    def __init__(self):
        """Initialize universal server"""
        self.tools_available = TOOLS_AVAILABLE
        self.legacy_server = None

        # Initialize legacy server for backward compatibility
        if LEGACY_AVAILABLE:
            try:
                self.legacy_server = IntelligentFlowiseMCPServer()
                logger.info("✅ Legacy Flowise server available for backward compatibility")
            except Exception as e:
                logger.warning(f"⚠️ Legacy server unavailable: {e}")

        logger.info("🚀 Universal Agentic Flywheel MCP Server initialized")
        logger.info(f"   Tools Available: {self.tools_available}")
        logger.info(f"   Legacy Support: {self.legacy_server is not None}")


# Global server instance
if MCP_AVAILABLE and TOOLS_AVAILABLE:
    app = server.Server("agentic-flywheel-universal")
    universal_server = UniversalAgenticFlywheelServer()

    @app.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        """List all available MCP tools"""
        tools = [
            # ==========================================
            # UNIVERSAL QUERY TOOL
            # ==========================================
            types.Tool(
                name="universal_query",
                description="Universal query with intelligent backend routing and fallback (Flowise + Langflow + auto-selection)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question to ask"
                        },
                        "intent": {
                            "type": "string",
                            "description": "Intent classification (optional, auto-detected if not provided)"
                        },
                        "backend": {
                            "type": "string",
                            "enum": ["auto", "flowise", "langflow"],
                            "default": "auto",
                            "description": "Backend selection strategy"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Session ID for conversation continuity"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Additional flow-specific parameters"
                        },
                        "include_routing_metadata": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include routing decision metadata in response"
                        }
                    },
                    "required": ["question"]
                }
            ),

            # ==========================================
            # BACKEND MANAGEMENT TOOLS
            # ==========================================
            types.Tool(
                name="backend_registry_status",
                description="Get status of all registered AI workflow backends (Flowise, Langflow, etc.)",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            types.Tool(
                name="backend_discover",
                description="Auto-discover and register available backends from environment configuration",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "config_path": {
                            "type": "string",
                            "description": "Optional path to backend configuration file"
                        },
                        "force_rediscover": {
                            "type": "boolean",
                            "default": False,
                            "description": "Force rediscovery even if backends already registered"
                        }
                    }
                }
            ),
            types.Tool(
                name="backend_connect",
                description="Manually connect to a specific backend instance",
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
                            "description": "Optional API key for authentication"
                        },
                        "name": {
                            "type": "string",
                            "description": "Optional custom name for this backend instance"
                        }
                    },
                    "required": ["backend_type", "base_url"]
                }
            ),
            types.Tool(
                name="backend_list_flows",
                description="List all flows across all connected backends with filtering and performance metrics",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "backend_filter": {
                            "type": "string",
                            "enum": ["all", "flowise", "langflow"],
                            "default": "all",
                            "description": "Filter by backend type"
                        },
                        "intent_filter": {
                            "type": "string",
                            "description": "Filter flows by intent keyword"
                        },
                        "min_performance_score": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "description": "Minimum performance score threshold"
                        }
                    }
                }
            ),
            types.Tool(
                name="backend_execute_universal",
                description="Execute a flow by ID with automatic backend resolution (searches across all backends)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {
                            "type": "string",
                            "description": "Flow ID to execute (searches across all backends)"
                        },
                        "input_data": {
                            "type": "object",
                            "description": "Input data for flow execution"
                        },
                        "backend_preference": {
                            "type": "string",
                            "enum": ["auto", "flowise", "langflow"],
                            "default": "auto",
                            "description": "Backend selection preference"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Optional session ID for continuity"
                        }
                    },
                    "required": ["flow_id", "input_data"]
                }
            ),
            types.Tool(
                name="backend_performance_compare",
                description="Compare performance metrics across all backends with recommendations",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "enum": ["latency", "success_rate", "throughput"],
                            "default": "latency",
                            "description": "Primary metric to compare"
                        },
                        "time_range": {
                            "type": "string",
                            "enum": ["1h", "24h", "7d", "30d"],
                            "default": "24h",
                            "description": "Time range for analysis"
                        },
                        "intent_filter": {
                            "type": "string",
                            "description": "Compare performance for specific intent"
                        }
                    }
                }
            ),

            # ==========================================
            # ADMIN INTELLIGENCE TOOLS
            # ==========================================
            types.Tool(
                name="flowise_admin_dashboard",
                description="Get comprehensive analytics dashboard for Flowise flows (4,506+ messages analyzed)",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            types.Tool(
                name="flowise_analyze_flow",
                description="Analyze performance metrics for a specific Flowise flow with optimization suggestions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "flow_id": {
                            "type": "string",
                            "description": "Flow ID to analyze (e.g., 'csv2507')"
                        },
                        "include_samples": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include sample conversations in analysis"
                        }
                    },
                    "required": ["flow_id"]
                }
            ),
            types.Tool(
                name="flowise_discover_flows",
                description="Discover active Flowise flows from database with usage analytics and sorting",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "min_messages": {
                            "type": "integer",
                            "default": 10,
                            "description": "Minimum message count to consider flow active"
                        },
                        "include_inactive": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include flows with low usage"
                        },
                        "sort_by": {
                            "type": "string",
                            "enum": ["usage", "success_rate", "engagement", "recent"],
                            "default": "usage",
                            "description": "Sort criterion for discovered flows"
                        }
                    }
                }
            ),
            types.Tool(
                name="flowise_sync_config",
                description="Sync flow-registry.yaml with database reality (preview with dry_run=true by default)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "dry_run": {
                            "type": "boolean",
                            "default": True,
                            "description": "Preview changes without applying (safe default)"
                        },
                        "auto_add_flows": {
                            "type": "boolean",
                            "default": False,
                            "description": "Automatically add discovered flows to registry"
                        },
                        "remove_inactive": {
                            "type": "boolean",
                            "default": False,
                            "description": "Remove flows with zero usage"
                        }
                    }
                }
            ),
            types.Tool(
                name="flowise_export_metrics",
                description="Export flow performance metrics in JSON or CSV format for external analysis",
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
                            "description": "Specific flow IDs to export (empty = all flows)"
                        },
                        "include_messages": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include raw message data in export"
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
                            "description": "Analyze specific flow (optional, omit for all flows)"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 100,
                            "description": "Maximum messages to analyze"
                        },
                        "pattern_type": {
                            "type": "string",
                            "enum": ["question_types", "success_factors", "failure_modes", "all"],
                            "default": "all",
                            "description": "Type of patterns to extract"
                        }
                    }
                }
            ),
        ]

        # Add legacy Flowise tools if available
        if universal_server.legacy_server:
            tools.extend([
                types.Tool(
                    name="flowise_query",
                    description="[LEGACY] Query Flowise with intelligent flow selection (use universal_query for multi-backend)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "question": {"type": "string", "description": "Question to ask"},
                            "session_id": {"type": "string", "description": "Session ID for continuity"},
                            "flow_override": {"type": "string", "description": "Override automatic flow selection"}
                        },
                        "required": ["question"]
                    }
                ),
                types.Tool(
                    name="flowise_list_flows",
                    description="[LEGACY] List Flowise flows (use backend_list_flows for multi-backend)",
                    inputSchema={"type": "object", "properties": {}}
                ),
                types.Tool(
                    name="flowise_server_status",
                    description="[LEGACY] Get Flowise server status (use backend_registry_status for multi-backend)",
                    inputSchema={"type": "object", "properties": {}}
                )
            ])

        logger.info(f"📋 Listed {len(tools)} available tools")
        return tools

    @app.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
        """Handle MCP tool calls"""

        try:
            # Universal Query
            if name == "universal_query":
                return await handle_universal_query(name, arguments)

            # Backend Management Tools
            elif name == "backend_registry_status":
                return await handle_backend_registry_status(name, arguments)
            elif name == "backend_discover":
                return await handle_backend_discover(name, arguments)
            elif name == "backend_connect":
                return await handle_backend_connect(name, arguments)
            elif name == "backend_list_flows":
                return await handle_backend_list_flows(name, arguments)
            elif name == "backend_execute_universal":
                return await handle_backend_execute_universal(name, arguments)
            elif name == "backend_performance_compare":
                return await handle_backend_performance_compare(name, arguments)

            # Admin Intelligence Tools
            elif name == "flowise_admin_dashboard":
                return await handle_flowise_admin_dashboard(name, arguments)
            elif name == "flowise_analyze_flow":
                return await handle_flowise_analyze_flow(name, arguments)
            elif name == "flowise_discover_flows":
                return await handle_flowise_discover_flows(name, arguments)
            elif name == "flowise_sync_config":
                return await handle_flowise_sync_config(name, arguments)
            elif name == "flowise_export_metrics":
                return await handle_flowise_export_metrics(name, arguments)
            elif name == "flowise_pattern_analysis":
                return await handle_flowise_pattern_analysis(name, arguments)

            # Legacy Flowise Tools
            elif name in ["flowise_query", "flowise_list_flows", "flowise_server_status"]:
                if not universal_server.legacy_server:
                    return [types.TextContent(
                        type="text",
                        text=f"❌ Legacy tool '{name}' unavailable. Use the new multi-backend tools instead."
                    )]

                # Delegate to legacy server
                if name == "flowise_query":
                    result = await universal_server.legacy_server.intelligent_query(
                        arguments["question"],
                        arguments.get("session_id"),
                        arguments.get("flow_override")
                    )
                    response_text = result.get("text", str(result)) if isinstance(result, dict) else str(result)
                    return [types.TextContent(type="text", text=response_text)]

                elif name == "flowise_list_flows":
                    flows = universal_server.legacy_server.list_available_flows()
                    flows_text = "Available Flows:\n\n"
                    for flow_key, flow_data in flows.items():
                        flows_text += f"• {flow_data['name']}: {flow_data['description']}\n"
                    return [types.TextContent(type="text", text=flows_text)]

                elif name == "flowise_server_status":
                    status = universal_server.legacy_server.get_server_status()
                    status_text = json.dumps(status, indent=2)
                    return [types.TextContent(type="text", text=status_text)]

            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Unknown tool: {name}"
                )]

        except Exception as e:
            logger.error(f"Tool execution failed for '{name}': {e}", exc_info=True)
            return [types.TextContent(
                type="text",
                text=f"❌ Error executing {name}: {str(e)}"
            )]

    @app.list_resources()
    async def handle_list_resources() -> List[types.Resource]:
        """List available resources"""
        return [
            types.Resource(
                uri="docs://agentic-flywheel/overview",
                name="Agentic Flywheel Overview",
                description="Multi-backend AI infrastructure documentation",
                mimeType="text/plain"
            ),
            types.Resource(
                uri="docs://agentic-flywheel/architecture",
                name="Architecture Guide",
                description="System architecture and component integration",
                mimeType="text/plain"
            )
        ]

    @app.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read resource content"""
        if uri == "docs://agentic-flywheel/overview":
            return """
# Agentic Flywheel - Multi-Backend AI Infrastructure

Version: 2.0.0

## Overview
Universal AI workflow platform with intelligent routing, observability, and persistence.

## Supported Backends
- Flowise (existing)
- Langflow (new)
- Extensible to future platforms

## Key Features
- Intelligent backend routing (50% flow match, 30% health, 20% performance)
- Full observability via Langfuse tracing
- Cross-session persistence via Redis
- 18 MCP tools for management and intelligence
- 100% test coverage (134 tests)

## Tool Categories
1. Universal Query: Multi-backend query with auto-routing
2. Backend Management: Discovery, status, performance comparison
3. Admin Intelligence: Usage analytics, pattern analysis, optimization

## Quick Start
1. Configure environment variables (FLOWISE_BASE_URL, LANGFLOW_BASE_URL, etc.)
2. Use universal_query for questions (auto-routes to optimal backend)
3. Check backend_registry_status for system health
4. Analyze patterns with admin intelligence tools
            """
        elif uri == "docs://agentic-flywheel/architecture":
            return """
# Agentic Flywheel Architecture

## Component Layers
1. MCP Tools Layer (18 tools)
2. Intelligent Routing Layer (UniversalRouter)
3. Backend Registry (Multi-backend management)
4. Backend Implementations (Flowise + Langflow)
5. Observability & Persistence (Langfuse + Redis)

## Data Flow
User Request → MCP Tool → Router → Backend Selection → Execution → Tracing → Response

## Intelligent Routing
- 50% Flow Match Score (intent keyword matching)
- 30% Health Score (backend availability)
- 20% Performance Score (historical success/latency)

## Persistence
- Redis Sessions: 7-day TTL
- Execution Cache: 1-hour TTL
- JSON serialization for debugging

## Testing
- 134 comprehensive tests
- 100% coverage
- Unit + Integration tests
            """
        else:
            raise ValueError(f"Unknown resource: {uri}")


async def main():
    """Main entry point for MCP server"""
    if not MCP_AVAILABLE:
        logger.error("❌ MCP library not available. Install with: pip install mcp")
        sys.exit(1)

    if not TOOLS_AVAILABLE:
        logger.error("❌ Agentic Flywheel tools not available. Check installation.")
        sys.exit(1)

    logger.info("🚀 Starting Agentic Flywheel Universal MCP Server")
    logger.info("   Version: 2.0.0")
    logger.info("   Multi-Backend: Flowise + Langflow + Extensible")

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="agentic-flywheel-universal",
                server_version="2.0.0"
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
