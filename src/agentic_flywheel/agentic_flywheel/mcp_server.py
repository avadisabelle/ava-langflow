#!/usr/bin/env python3
"""
JGT Flowise MCP Server
Exposes flowise capabilities as MCP services with dynamic flow registry
"""

import os
import asyncio
import json
import logging
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
import click
import webbrowser # Added for flowise_browse tool
from mcp import server, types
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
import mcp.server.stdio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowiseMCPServer:
    """MCP Server for Flowise integration"""
    
    def __init__(self, flowise_base_url: str = "https://beagle-emerging-gnu.ngrok-free.app", config_path: Optional[str] = None):
        self.flowise_base_url = flowise_base_url
        self.active_sessions = {}

        if config_path:
            try:
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                self.flows = {
                    key: {
                        "id": flow["id"],
                        "name": flow["name"],
                        "description": flow["description"],
                        "default_config": {
                            "temperature": 0.7, # Default if not specified in exported config
                            "maxOutputTokens": 2000, # Default if not specified
                            "rephrasePrompt": f"Transform this into a {flow['name'].lower()} inquiry: {{question}}",
                            "responsePrompt": f"Provide helpful guidance for {flow['name'].lower()}: {{context}}"
                        },
                        "intent_keywords": flow["intent_keywords"]
                    }
                    for key, flow in config_data["mcp_compatible_flows"].items()
                }
                logger.info(f"✅ Loaded {len(self.flows)} flows from {config_path}")
            except Exception as e:
                logger.error(f"❌ Failed to load flows from {config_path}: {e}. Loading from YAML registry.")
                self._load_from_yaml_registry()
        else:
            self._load_from_yaml_registry()

    def _load_from_yaml_registry(self):
        """Load flows from YAML registry, filtering by active flag"""
        registry_paths = [
            Path(__file__).parent / "config" / "flow-registry.yaml",  # Package location
            Path(__file__).parent.parent / "flow-registry.yaml"       # Development location
        ]
        
        for registry_path in registry_paths:
            if registry_path.exists():
                try:
                    with open(registry_path, 'r') as f:
                        registry = yaml.safe_load(f)
                    
                    self.flows = {}
                    # Load operational flows that are active
                    for flow_key, flow_config in registry.get('operational_flows', {}).items():
                        if flow_config.get('active', 0) == 1:
                            self.flows[flow_key] = {
                                "id": flow_config['id'],
                                "name": flow_config['name'],
                                "description": flow_config['description'],
                                "default_config": flow_config.get('config', {
                                    "temperature": 0.7,
                                    "maxOutputTokens": 2000
                                }),
                                "intent_keywords": flow_config['intent_keywords']
                            }
                    
                    # Load routing flows that are active
                    for flow_key, flow_config in registry.get('routing_flows', {}).items():
                        if flow_config.get('active', 0) == 1:
                            self.flows[flow_key] = {
                                "id": flow_config['id'],
                                "name": flow_config['name'],
                                "description": flow_config['description'],
                                "default_config": flow_config.get('config', {
                                    "temperature": 0.7,
                                    "maxOutputTokens": 2000
                                }),
                                "intent_keywords": flow_config['intent_keywords']
                            }
                    
                    logger.info(f"✅ Loaded {len(self.flows)} active flows from YAML registry: {registry_path}")
                    return
                except Exception as e:
                    logger.error(f"❌ Failed to load flows from {registry_path}: {e}")
                    continue
        
        logger.warning("❌ Flow registry not found. Using default flows.")
        self._load_default_flows()

    def _load_default_flows(self):
        self.flows = {
            "creative-orientation": {
                "id": "7d405a51-968d-4467-9ae6-d49bf182cdf9",
                "name": "Creative Orientation",
                "description": "Structural tension dynamics for creating desired outcomes",
                "default_config": {
                    "temperature": 0.8,
                    "rephrasePrompt": "Transform this into a creative orientation inquiry focused on desired outcomes: {question}",
                    "responsePrompt": "Guide using structural tension dynamics - what desired outcome wants to emerge? Apply creative orientation principles focusing on natural advancement through structural relationships: {context}"
                },
                "intent_keywords": ["creative", "vision", "goal", "plan", "dream", "aspire"]
            },
            "technical-analysis": {
                "id": "896f7eed-342e-4596-9429-6fb9b5fbd91b",
                "name": "Technical Analysis",
                "description": "Technical guidance for creating robust software solutions",
                "default_config": {
                    "temperature": 0.3,
                    "returnSourceDocuments": True,
                    "maxOutputTokens": 2000,
                    "rephrasePrompt": "Clarify what technical outcome you want to create: {question}",
                    "responsePrompt": "Guide toward creating effective technical solutions with structural clarity: {context}"
                },
                "intent_keywords": ["code", "technical", "analyze", "debug", "programming"]
            },
            "document-qa": {
                "id": "8ce0ad25-da40-490e-a8ba-f00ea7836677",
                "name": "Document Q&A",
                "description": "Knowledge access for creating informed understanding",
                "default_config": {
                    "temperature": 0.5,
                    "returnSourceDocuments": True,
                    "rephrasePrompt": "Clarify what understanding you want to create from available knowledge: {question}",
                    "responsePrompt": "Guide toward creating comprehensive understanding from relevant sources: {context}"
                },
                "intent_keywords": ["document", "search", "find", "information", "lookup"]
            }
        }
    
    async def _intelligent_query(self, 
                                question: str,
                                intent: Optional[str] = None,
                                session_id: Optional[str] = None,
                                flow_override: Optional[str] = None) -> Dict[str, Any]:
        """Execute intelligent flowise query with flow selection"""
        
        # Determine flow to use
        if flow_override and flow_override in self.flows:
            flow_key = flow_override
        elif intent and intent in self.flows:
            flow_key = intent
        else:
            # Auto-classify intent based on keywords
            flow_key = self._classify_intent(question)
        
        flow_config = self.flows[flow_key]
        flow_id = flow_config["id"]
        
        # Generate session ID if not provided
        if not session_id:
            import time, uuid
            session_id = f"mcp-session-{int(time.time())}-{str(uuid.uuid4())[:8]}"
        
        # Build configuration
        config = flow_config["default_config"].copy()
        config["sessionId"] = session_id
        
        # Track active session
        self.active_sessions[session_id] = {
            "flow_key": flow_key,
            "flow_name": flow_config["name"],
            "created_at": asyncio.get_event_loop().time()
        }
        
        # Build payload
        payload = {
            "question": question,
            "overrideConfig": config
        }
        
        logger.info(f"Querying flow: {flow_config['name']} ({flow_id})")
        logger.info(f"Session: {session_id}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.flowise_base_url}/api/v1/prediction/{flow_id}",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Add metadata
                result["_mcp_metadata"] = {
                    "flow_used": flow_config["name"],
                    "flow_key": flow_key,
                    "flow_id": flow_id,
                    "session_id": session_id,
                    "intent_detected": flow_key,
                    "config_used": config
                }
                
                return result
                
            except httpx.RequestError as e:
                logger.error(f"Request failed: {e}")
                return {
                    "error": f"Request failed: {str(e)}",
                    "flow_attempted": flow_config["name"],
                    "session_id": session_id
                }
    
    async def _configure_flow(self,
                             flow_id: str,
                             config: Dict[str, Any],
                             session_id: Optional[str] = None) -> Dict[str, Any]:
        """Configure specific flow with custom parameters"""
        
        # Find flow by ID
        flow_key = None
        flow_config = None
        for key, flow in self.flows.items():
            if flow["id"] == flow_id:
                flow_key = key
                flow_config = flow
                break
        
        if not flow_config:
            return {"error": f"Flow with ID {flow_id} not found"}
        
        # Generate session ID if not provided
        if not session_id:
            import time, uuid
            session_id = f"mcp-config-{int(time.time())}-{str(uuid.uuid4())[:8]}"
        
        # Merge configuration
        final_config = flow_config["default_config"].copy()
        final_config.update(config)
        final_config["sessionId"] = session_id
        
        return {
            "flow_id": flow_id,
            "flow_name": flow_config["name"],
            "session_id": session_id,
            "configuration_applied": final_config,
            "status": "configured"
        }
    
    def _classify_intent(self, question: str) -> str:
        """Classify user intent based on question content"""
        question_lower = question.lower()
        
        # Score each flow based on keyword matches
        scores = {}
        for flow_key, flow_config in self.flows.items():
            score = sum(1 for keyword in flow_config["intent_keywords"] 
                       if keyword in question_lower)
            scores[flow_key] = score
        
        # Return the flow with highest score, default to creative-orientation
        best_flow = max(scores.items(), key=lambda x: x[1])
        return best_flow[0] if best_flow[1] > 0 else "creative-orientation"
    
    async def _get_active_sessions(self) -> Dict[str, Any]:
        """Get currently tracked sessions"""
        return self.active_sessions.copy()

# Create server instance
app = server.Server("flowise-mcp-server")
flowise_server = FlowiseMCPServer()

@app.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available MCP tools for flowise operations"""
    return [
        types.Tool(
            name="flowise_query",
            description="Query flowise with intelligent flow selection and configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to ask flowise"
                    },
                    "intent": {
                        "type": "string",
                        "enum": ["creative-orientation", "technical-analysis", "document-qa"],
                        "description": "Specify intent for flow selection"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for conversation continuity"
                    },
                    "flow_override": {
                        "type": "string",
                        "description": "Override automatic flow selection with specific flow key"
                    }
                },
                "required": ["question"]
            }
        ),
        types.Tool(
            name="flowise_configure",
            description="Configure flowise flow parameters dynamically",
            inputSchema={
                "type": "object",
                "properties": {
                    "flow_id": {
                        "type": "string",
                        "description": "Flow ID to configure"
                    },
                    "config": {
                        "type": "object",
                        "description": "Configuration parameters to apply",
                        "properties": {
                            "temperature": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                            "maxOutputTokens": {"type": "integer", "minimum": 1, "maximum": 8192},
                            "rephrasePrompt": {"type": "string"},
                            "responsePrompt": {"type": "string"},
                            "returnSourceDocuments": {"type": "boolean"}
                        }
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for the configuration"
                    }
                },
                "required": ["flow_id", "config"]
            }
        ),
        types.Tool(
            name="flowise_list_flows",
            description="List available flowise flows with their capabilities",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="flowise_session_info",
            description="Get information about active flowise sessions",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "Specific session ID to query (optional)"
                    }
                },
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="flowise_domain_query",
            description="Query flowise with domain specialization and automatic context injection",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to ask with domain context"
                    },
                    "domain_name": {
                        "type": "string",
                        "description": "Domain name for specialization (e.g. 'Language Learning Platform')"
                    },
                    "domain_description": {
                        "type": "string",
                        "description": "Domain description for context"
                    },
                    "context_type": {
                        "type": "string",
                        "enum": ["technical", "cultural", "strategic", "general"],
                        "description": "Type of context to inject",
                        "default": "general"
                    },
                    "stack_info": {
                        "type": "object",
                        "description": "Technical stack information (for technical context)",
                        "additionalProperties": True
                    },
                    "cultural_info": {
                        "type": "object", 
                        "description": "Cultural context information (for cultural context)",
                        "additionalProperties": True
                    },
                    "specialized_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Domain-specific keywords for enhanced intent classification"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Session ID for conversation continuity"
                    }
                },
                "required": ["question", "domain_name", "domain_description"]
            }
        ),
        types.Tool(
            name="flowise_add_flow",
            description="Add new flow to the registry dynamically",
            inputSchema={
                "type": "object",
                "properties": {
                    "flow_id": {
                        "type": "string",
                        "description": "Unique flow ID from Flowise"
                    },
                    "flow_name": {
                        "type": "string",
                        "description": "Human-readable flow name"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the flow does"
                    },
                    "purpose": {
                        "type": "string",
                        "description": "Purpose and intended use of the flow"
                    },
                    "intent_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords for automatic intent classification"
                    },
                    "temperature": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "default": 0.7,
                        "description": "Default temperature for the flow"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "minimum": 100,
                        "maximum": 8192,
                        "default": 2000,
                        "description": "Default max output tokens"
                    }
                },
                "required": ["flow_id", "flow_name", "description", "intent_keywords"]
            }
        ),
        types.Tool(
            name="flowise_browse",
            description="Opens a Flowise flow in the default web browser on the machine where the MCP server is running. Note: If the MCP server is running remotely or in a headless environment, this action may not be visible or functional on the client's machine. Check the tool's return message for success or failure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "flow_name": {
                        "type": "string",
                        "description": "The name of the flow to open (e.g., 'Creative Orientation')."
                    },
                    "canvas": {
                        "type": "boolean",
                        "description": "If true, open in edit mode (canvas) instead of chat mode. Defaults to false.",
                        "default": false
                    }
                },
                "required": ["flow_name"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle MCP tool calls"""
    
    try:
        if name == "flowise_query":
            result = await flowise_server._intelligent_query(
                arguments["question"],
                arguments.get("intent"),
                arguments.get("session_id"),
                arguments.get("flow_override")
            )
            
            # Extract response text
            response_text = result.get("text") or result.get("answer") or str(result)
            
            # Include metadata if available
            if "_mcp_metadata" in result:
                metadata_text = f"\n\n[MCP Metadata: Flow={result['_mcp_metadata']['flow_used']}, Session={result['_mcp_metadata']['session_id']}]"
                response_text += metadata_text
            
            return [types.TextContent(type="text", text=response_text)]
        
        elif name == "flowise_configure":
            result = await flowise_server._configure_flow(
                arguments["flow_id"],
                arguments["config"],
                arguments.get("session_id")
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
        
        elif name == "flowise_list_flows":
            flows_info = {
                key: {
                    "id": flow["id"],
                    "name": flow["name"],
                    "description": flow["description"],
                    "intent_keywords": flow["intent_keywords"]
                }
                for key, flow in flowise_server.flows.items()
            }
            return [types.TextContent(type="text", text=json.dumps(flows_info, indent=2))]
        
        elif name == "flowise_session_info":
            session_id = arguments.get("session_id")
            if session_id:
                session_info = flowise_server.active_sessions.get(session_id, {"error": "Session not found"})
            else:
                session_info = await flowise_server._get_active_sessions()
            
            return [types.TextContent(type="text", text=json.dumps(session_info, indent=2))]
        
        elif name == "flowise_domain_query":
            # This would require importing domain specialization modules
            # For now, return a message indicating the capability
            domain_info = {
                "domain_name": arguments["domain_name"],
                "domain_description": arguments["domain_description"],
                "context_type": arguments.get("context_type", "general"),
                "question": arguments["question"],
                "note": "Domain specialization requires flowise_manager module integration",
                "fallback": "Using standard intelligent query with domain context in question"
            }
            
            # Fallback to regular query with domain context injected
            contextualized_question = f"""
Domain: {arguments['domain_name']}
Description: {arguments['domain_description']}
Context Type: {arguments.get('context_type', 'general')}

Query: {arguments['question']}
"""
            
            result = await flowise_server._intelligent_query(
                contextualized_question,
                None,  # Let it auto-detect intent
                arguments.get("session_id"),
                None
            )
            
            # Extract response and add domain metadata
            response_text = result.get("text") or result.get("answer") or str(result)
            
            if "_mcp_metadata" in result:
                result["_mcp_metadata"]["domain_context"] = domain_info
                metadata_text = f"\n\n[Domain Context: {arguments['domain_name']} | Context: {arguments.get('context_type', 'general')} | Flow: {result['_mcp_metadata']['flow_used']}]"
                response_text += metadata_text
            
            return [types.TextContent(type="text", text=response_text)]
        
        elif name == "flowise_add_flow":
            # Add new flow to registry
            # Try package-bundled config first, then fallback to development location  
            registry_paths = [
                Path(__file__).parent / "config" / "flow-registry.yaml",  # Package location
                Path(__file__).parent.parent / "flow-registry.yaml"       # Development location  
            ]
            
            registry_path = None
            for path in registry_paths:
                if path.exists():
                    registry_path = path
                    break
            
            if not registry_path:
                error_result = {
                    "status": "error", 
                    "message": f"Flow registry not found. Searched: {[str(p) for p in registry_paths]}"
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
            
            try:
                # Load existing registry
                with open(registry_path, 'r') as f:
                    registry = yaml.safe_load(f)
                
                # Create flow key from name
                flow_key = arguments["flow_name"].lower().replace(' ', '-').replace('_', '-')
                
                # Build new flow config
                new_flow = {
                    'id': arguments["flow_id"],
                    'name': arguments["flow_name"],
                    'description': arguments["description"],
                    'purpose': arguments.get("purpose", f"Purpose for {arguments['flow_name']}"),
                    'session_format': f"chat:{flow_key}:{{uuid}}",
                    'config': {
                        'temperature': arguments.get("temperature", 0.7),
                        'maxOutputTokens': arguments.get("max_tokens", 2000),
                        'rephrasePrompt': f"Transform this into a {arguments['flow_name'].lower()} inquiry: {{question}}",
                        'responsePrompt': f"Provide guidance for {arguments['flow_name'].lower()}: {{context}}"
                    },
                    'intent_keywords': arguments["intent_keywords"],
                    'status': 'active'
                }
                
                # Add to operational flows
                if 'operational_flows' not in registry:
                    registry['operational_flows'] = {}
                registry['operational_flows'][flow_key] = new_flow
                
                # Save back to file
                with open(registry_path, 'w') as f:
                    yaml.dump(registry, f, default_flow_style=False, sort_keys=False)
                
                # Update flowise_server flows dynamically
                flowise_server.flows[flow_key] = {
                    "id": new_flow["id"],
                    "name": new_flow["name"],
                    "description": new_flow["description"],
                    "default_config": new_flow["config"],
                    "intent_keywords": new_flow["intent_keywords"]
                }
                
                result = {
                    "status": "success",
                    "message": f"Added flow '{flow_key}' to registry",
                    "flow_key": flow_key,
                    "flow_id": arguments["flow_id"],
                    "keywords": arguments["intent_keywords"]
                }
                
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
                
            except Exception as e:
                logger.error(f"Failed to add flow: {e}")
                error_result = {
                    "status": "error",
                    "message": f"Failed to add flow: {str(e)}"
                }
                return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]
        
        elif name == "flowise_browse":
            flow_name = arguments["flow_name"]
            canvas_mode = arguments.get("canvas", False)
            
            flow_config = None
            for key, flow in flowise_server.flows.items():
                if flow["name"] == flow_name:
                    flow_config = flow
                    break
            
            if not flow_config:
                return [types.TextContent(type="text", text=f"❌ Flow '{flow_name}' not found in registry.")]
            
            flow_id = flow_config["id"]
            url_pattern = "canvas" if canvas_mode else "chatbot"
            browse_url = f"{flowise_server.flowise_base_url}/{url_pattern}/{flow_id}"
            
            try:
                webbrowser.open(browse_url)
                return [types.TextContent(type="text", text=f"✅ Opened '{flow_name}' in browser: {browse_url}")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"❌ Failed to open browser for '{flow_name}': {str(e)}")]
        
        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return [types.TextContent(type="text", text=f"Error executing tool {name}: {str(e)}")]

@app.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available MCP resources"""
    return [
        types.Resource(
            uri="flowise://flows",
            name="Available Flowise Flows",
            description="List of configured flowise flows with their capabilities and configuration options",
            mimeType="application/json"
        ),
        types.Resource(
            uri="flowise://sessions",
            name="Active Sessions",
            description="Currently active flowise sessions with metadata",
            mimeType="application/json"
        ),
        types.Resource(
            uri="flowise://config-schema",
            name="Configuration Schema",
            description="Schema for flowise configuration parameters",
            mimeType="application/json"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read MCP resources"""
    
    if uri == "flowise://flows":
        return json.dumps(flowise_server.flows, indent=2)
    
    elif uri == "flowise://sessions":
        sessions = await flowise_server._get_active_sessions()
        return json.dumps(sessions, indent=2)
    
    elif uri == "flowise://config-schema":
        schema = {
            "ChatGoogleGenerativeAI": {
                "temperature": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "maxOutputTokens": {"type": "integer", "minimum": 1, "maximum": 8192},
                "modelName": {"type": "string", "enum": ["gemini-pro", "gemini-1.5-pro"]},
                "customModelName": {"type": "string"},
                "topK": {"type": "number"},
                "baseUrl": {"type": "string"}
            },
            "ConversationalRetrievalQAChain": {
                "rephrasePrompt": {"type": "string", "minLength": 10},
                "responsePrompt": {"type": "string", "minLength": 10},
                "returnSourceDocuments": {"type": "boolean"}
            },
            "RedisBackedChatMemory": {
                "sessionId": {"type": "string"},
                "sessionTTL": {"type": "number"},
                "windowSize": {"type": "number"}
            }
        }
        return json.dumps(schema, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

@click.command()
@click.option('--config', 'config_file_path', type=click.Path(exists=True), help='Path to the Flowise MCP configuration JSON file.')
def cli(config_file_path: Optional[str] = None):
    """JGT Flowise MCP Server"""
    try:
        asyncio.run(main(config_file_path=config_file_path))
    except KeyboardInterrupt:
        print("\nServer stopped by user.")

async def main(config_file_path: Optional[str] = None):
    """Run the MCP server"""
    global flowise_server # Declare global to modify it

    # Determine config path
    if config_file_path:
        actual_config_path = config_file_path
    else:
        actual_config_path = os.getenv("FLOWISE_MCP_CONFIG_PATH")

    flowise_server = FlowiseMCPServer(config_path=actual_config_path) # Pass config_path to constructor

    # Server can be configured with initialization options
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="flowise-mcp-server",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(resources_changed=False),
                    experimental_capabilities=None,
                )
            ),
        )

if __name__ == "__main__":
    cli()
