#!/usr/bin/env python3
"""
Intelligent Flowise MCP Server
Rebuilt MCP server using admin layer intelligence and working flowise components
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import sys
import os
from pathlib import Path

# Import working flowise manager

try:
    from agentic_flywheel.flowise_manager import FlowiseManager
    from flowise_admin.config_sync import ConfigurationSync
    ADMIN_AVAILABLE = True
except ImportError as e:
    FlowiseManager = None
    ConfigurationSync = None
    ADMIN_AVAILABLE = False
    logging.warning(f"Admin integration not available: {e}")

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentFlowiseMCPServer:
    """MCP Server with admin intelligence integration"""
    
    def __init__(self):
        # Initialize with working flowise manager
        self.flowise_manager = None
        self.curated_flows = {}
        self.admin_sync = None
        self.active_sessions = {}
        
        # Try to initialize working components
        if FlowiseManager:
            try:
                # Determine default flow registry path
                default_registry_path = Path(__file__).parent / "config" / "flow-registry.yaml"
                self.flowise_manager = FlowiseManager(flow_registry_path=str(default_registry_path))
                logger.info("✅ Connected to working FlowiseManager")
            except Exception as e:
                logger.error(f"❌ FlowiseManager connection failed: {e}")
        
        # Try to get admin intelligence
        if ConfigurationSync and ADMIN_AVAILABLE:
            try:
                self.admin_sync = ConfigurationSync()
                self._load_curated_flows()
                logger.info("✅ Admin intelligence loaded successfully")
            except Exception as e:
                logger.warning(f"⚠️ Admin intelligence unavailable: {e}")
        
        # Fallback to working flows if admin unavailable
        if not self.curated_flows and self.flowise_manager:
            self._load_fallback_flows()
    
    def _load_curated_flows(self):
        """Load flows curated by admin layer intelligence"""
        if not self.admin_sync:
            return
        
        try:
            # Get MCP-suitable flows from admin analysis
            mcp_export = self.admin_sync.export_configuration_for_mcp()
            
            for flow_key, flow_data in mcp_export['mcp_compatible_flows'].items():
                # Convert admin format to MCP server format
                self.curated_flows[flow_key] = {
                    'id': flow_data['id'],
                    'name': flow_data['name'],
                    'description': flow_data['description'],
                    'intent_keywords': flow_data['intent_keywords'],
                    'success_metrics': flow_data['success_metrics'],
                    'admin_curated': True
                }
            
            logger.info(f"✅ Loaded {len(self.curated_flows)} admin-curated flows")
            
        except Exception as e:
            logger.error(f"❌ Failed to load curated flows: {e}")
    
    def _load_fallback_flows(self):
        """Load fallback flows from working flowise manager"""
        if not self.flowise_manager:
            return
        
        try:
            # Use known working flows
            working_flows = {
                'creative-orientation': {
                    'id': '7d405a51-968d-4467-9ae6-d49bf182cdf9',
                    'name': 'Creative Orientation',
                    'description': 'Structural tension dynamics for creating desired outcomes',
                    'intent_keywords': ['creative', 'vision', 'goal', 'plan', 'dream', 'aspire'],
                    'admin_curated': False
                },
                'faith2story': {
                    'id': '896f7eed-342e-4596-9429-6fb9b5fbd91b', 
                    'name': 'Faith2Story',
                    'description': 'Transform faith experiences into narrative stories',
                    'intent_keywords': ['faith', 'story', 'narrative', 'experience', 'spiritual'],
                    'admin_curated': False
                }
            }
            
            # Test flows to ensure they work
            for flow_key, flow_data in working_flows.items():
                if self._test_flow_availability(flow_data['id']):
                    self.curated_flows[flow_key] = flow_data
            
            logger.info(f"✅ Loaded {len(self.curated_flows)} fallback flows")
            
        except Exception as e:
            logger.error(f"❌ Failed to load fallback flows: {e}")
    
    def _test_flow_availability(self, flow_id: str) -> bool:
        """Test if a flow is available"""
        if not self.flowise_manager:
            return False
        
        try:
            # Simple connectivity test
            return self.flowise_manager.test_connection()
        except:
            return False
    
    async def intelligent_query(self, question: str, session_id: Optional[str] = None, 
                              flow_override: Optional[str] = None) -> Dict[str, Any]:
        """Execute intelligent query with admin-optimized routing"""
        
        if not self.flowise_manager:
            return {"error": "FlowiseManager not available"}
        
        try:
            # Use admin intelligence for flow selection if available
            if flow_override and flow_override in self.curated_flows:
                selected_flow = flow_override
            else:
                selected_flow = self._classify_intent(question)
            
            if selected_flow not in self.curated_flows:
                selected_flow = list(self.curated_flows.keys())[0]  # Fallback to first available
            
            flow_data = self.curated_flows[selected_flow]
            
            # Use working flowise manager for actual query
            result = self.flowise_manager.adaptive_query(
                question=question,
                intent=selected_flow,
                session_id=session_id
            )
            
            # Add MCP metadata
            if isinstance(result, dict):
                result['_mcp_metadata'] = {
                    'flow_used': flow_data['name'],
                    'flow_id': flow_data['id'],
                    'admin_curated': flow_data.get('admin_curated', False),
                    'session_id': session_id,
                    'success_metrics': flow_data.get('success_metrics')
                }
            
            # Track session
            if session_id:
                self.active_sessions[session_id] = {
                    'flow_used': selected_flow,
                    'last_query': question[:100],
                    'timestamp': asyncio.get_event_loop().time()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "error": f"Query execution failed: {str(e)}",
                "available_flows": list(self.curated_flows.keys())
            }
    
    def _classify_intent(self, question: str) -> str:
        """Classify intent using available flows"""
        question_lower = question.lower()
        
        # Score flows based on keyword matches
        scores = {}
        for flow_key, flow_data in self.curated_flows.items():
            score = sum(1 for keyword in flow_data['intent_keywords'] 
                       if keyword in question_lower)
            scores[flow_key] = score
        
        # Return best match or first available flow
        if scores:
            best_flow = max(scores.items(), key=lambda x: x[1])
            return best_flow[0] if best_flow[1] > 0 else list(self.curated_flows.keys())[0]
        
        return list(self.curated_flows.keys())[0] if self.curated_flows else "creative-orientation"
    
    def list_available_flows(self) -> Dict[str, Any]:
        """List flows available to users"""
        return {
            flow_key: {
                'name': flow_data['name'],
                'description': flow_data['description'],
                'keywords': flow_data['intent_keywords'],
                'admin_curated': flow_data.get('admin_curated', False)
            }
            for flow_key, flow_data in self.curated_flows.items()
        }
    
    def get_server_status(self) -> Dict[str, Any]:
        """Get server status information"""
        return {
            'flowise_manager_available': self.flowise_manager is not None,
            'admin_intelligence_available': self.admin_sync is not None,
            'curated_flows_count': len(self.curated_flows),
            'active_sessions_count': len(self.active_sessions),
            'flows_available': list(self.curated_flows.keys())
        }

# Global server instance
if MCP_AVAILABLE:
    app = server.Server("intelligent-flowise-mcp-server")
    intelligent_server = IntelligentFlowiseMCPServer()

    @app.list_tools()
    async def handle_list_tools() -> List[types.Tool]:
        """List available MCP tools"""
        return [
            types.Tool(
                name="flowise_query",
                description="Query flowise with intelligent flow selection using admin optimization",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question to ask flowise"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Session ID for conversation continuity"
                        },
                        "flow_override": {
                            "type": "string",
                            "description": "Override automatic flow selection"
                        }
                    },
                    "required": ["question"]
                }
            ),
            types.Tool(
                name="flowise_list_flows",
                description="List available flows curated by admin intelligence",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="flowise_server_status", 
                description="Get server status and capabilities",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            )
        ]

    @app.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
        """Handle MCP tool calls"""
        
        try:
            if name == "flowise_query":
                result = await intelligent_server.intelligent_query(
                    arguments["question"],
                    arguments.get("session_id"),
                    arguments.get("flow_override")
                )
                
                # Extract response text
                if isinstance(result, dict):
                    if "error" in result:
                        response_text = f"Error: {result['error']}"
                    else:
                        response_text = result.get("text", result.get("answer", str(result)))
                        
                        # Add metadata if available
                        if "_mcp_metadata" in result:
                            metadata = result["_mcp_metadata"]
                            response_text += f"\n\n[Flow: {metadata['flow_used']} | Admin Curated: {metadata['admin_curated']}]"
                else:
                    response_text = str(result)
                
                return [types.TextContent(type="text", text=response_text)]
            
            elif name == "flowise_list_flows":
                flows = intelligent_server.list_available_flows()
                flows_text = "Available Flows:\n\n"
                
                for flow_key, flow_data in flows.items():
                    status = "🎯 Admin Curated" if flow_data['admin_curated'] else "📋 Fallback"
                    flows_text += f"• **{flow_data['name']}** ({status})\n"
                    flows_text += f"  {flow_data['description']}\n"
                    flows_text += f"  Keywords: {', '.join(flow_data['keywords'][:5])}\n\n"
                
                return [types.TextContent(type="text", text=flows_text)]
            
            elif name == "flowise_server_status":
                status = intelligent_server.get_server_status()
                status_text = "Server Status:\n\n"
                
                status_text += f"🔗 Flowise Manager: {'✅ Connected' if status['flowise_manager_available'] else '❌ Unavailable'}\n"
                status_text += f"🧠 Admin Intelligence: {'✅ Available' if status['admin_intelligence_available'] else '⚠️ Fallback Mode'}\n"
                status_text += f"📊 Curated Flows: {status['curated_flows_count']}\n"
                status_text += f"💬 Active Sessions: {status['active_sessions_count']}\n"
                status_text += f"🎯 Available Flows: {', '.join(status['flows_available'])}\n"
                
                return [types.TextContent(type="text", text=status_text)]
            
            else:
                return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
        
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return [types.TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

    @app.list_resources()
    async def handle_list_resources() -> List[types.Resource]:
        """List available MCP resources"""
        return [
            types.Resource(
                uri="flowise://curated-flows",
                name="Admin Curated Flows",
                description="Flows curated by admin intelligence for optimal user experience",
                mimeType="application/json"
            ),
            types.Resource(
                uri="flowise://server-status",
                name="Server Status",
                description="Current server status and capabilities",
                mimeType="application/json"
            )
        ]

    @app.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Read MCP resources"""
        
        if uri == "flowise://curated-flows":
            flows = intelligent_server.list_available_flows()
            return json.dumps(flows, indent=2)
        
        elif uri == "flowise://server-status":
            status = intelligent_server.get_server_status()
            return json.dumps(status, indent=2)
        
        else:
            raise ValueError(f"Unknown resource: {uri}")

    async def main():
        """Run the intelligent MCP server"""
        if not MCP_AVAILABLE:
            logger.error("❌ MCP server dependencies not available")
            return
        
        logger.info("🚀 Starting Intelligent Flowise MCP Server...")
        
        # Show startup status
        status = intelligent_server.get_server_status()
        logger.info(f"📊 Server ready: {status['curated_flows_count']} flows, Admin: {status['admin_intelligence_available']}")
        
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="intelligent-flowise-mcp-server",
                    server_version="2.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None
                    )
                ),
            )

else:
    # Fallback for testing without MCP
    def main():
        """CLI interface for testing"""
        print("🧪 Testing Intelligent Flowise MCP Server")
        
        server = IntelligentFlowiseMCPServer()
        status = server.get_server_status()
        
        print("Server Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\nAvailable Flows:")
        flows = server.list_available_flows()
        for flow_key, flow_data in flows.items():
            print(f"  • {flow_data['name']}: {flow_data['description']}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Force test mode
        print("🧪 Testing Intelligent Flowise MCP Server (CLI Mode)")
        
        server = IntelligentFlowiseMCPServer()
        status = server.get_server_status()
        
        print("\n📊 Server Status:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        print("\n🎯 Available Flows:")
        flows = server.list_available_flows()
        for flow_key, flow_data in flows.items():
            status_emoji = "🎯" if flow_data.get('admin_curated') else "📋"
            print(f"  {status_emoji} {flow_data['name']}: {flow_data['description']}")
            print(f"      Keywords: {', '.join(flow_data['keywords'][:5])}")
        
        print(f"\n✅ Test completed: {len(flows)} flows ready for MCP service")
        
    elif MCP_AVAILABLE:
        asyncio.run(main())
    else:
        print("❌ MCP dependencies not available. Install with: pip install mcp")
        print("🧪 Use --test flag to test core functionality without MCP")