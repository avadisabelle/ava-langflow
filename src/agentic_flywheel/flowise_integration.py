#!/usr/bin/env python3
"""
Flowise Integration Helper
Provides easy integration with the user's Flowise server at beagle-emerging-gnu.ngrok-free.app
"""

import asyncio
import json
import requests
from typing import Dict, Any, Optional

# Optional import of MCP server - only if httpx is available
try:
    from .flowise_mcp.mcp_server import FlowiseMCPServer
    MCP_AVAILABLE = True
except ImportError:
    FlowiseMCPServer = None
    MCP_AVAILABLE = False


class FlowiseIntegrationHelper:
    """Helper class for integrating with the user's Flowise server."""
    
    def __init__(self, base_url: str = "https://beagle-emerging-gnu.ngrok-free.app"):
        self.base_url = base_url
        self.mcp_server = FlowiseMCPServer(flowise_base_url=base_url) if MCP_AVAILABLE else None
        
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the Flowise server."""
        try:
            # Test with example flow from comment
            response = requests.get(f"{self.base_url}/api/v1/chatflows", timeout=10)
            if response.status_code == 200:
                flows = response.json() if response.text else []
                return {
                    "status": "connected",
                    "server": self.base_url,
                    "flows_available": len(flows) if flows else 0
                }
            else:
                return {
                    "status": "error", 
                    "message": f"HTTP {response.status_code}",
                    "server": self.base_url
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "server": self.base_url
            }
    
    async def query_example_flow(self, question: str, max_messages: int = 10) -> Dict[str, Any]:
        """Query the example flow mentioned in the comment (896f7eed-342e-4596-9429-6fb9b5fbd91b)."""
        example_flow_id = "896f7eed-342e-4596-9429-6fb9b5fbd91b"
        
        try:
            payload = {
                "question": question,
                "overrideConfig": {
                    "sessionId": f"cesaret-example-{hash(question) % 10000}",
                    "maxMessages": max_messages
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/prediction/{example_flow_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "flow_id": example_flow_id,
                    "response": result,
                    "question": question,
                    "server": self.base_url
                }
            else:
                return {
                    "status": "error",
                    "message": f"HTTP {response.status_code}: {response.text}",
                    "flow_id": example_flow_id,
                    "server": self.base_url
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e),
                "flow_id": example_flow_id,
                "server": self.base_url
            }
    
    async def integrate_with_flywheel(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Integrate the Flowise server with the Agentic Flywheel system."""
        if not MCP_AVAILABLE or not self.mcp_server:
            return {
                "status": "error",
                "message": "MCP server not available (httpx dependency missing)"
            }
        return await self.mcp_server._intelligent_query(
            query, 
            session_id=session_id
        )


async def test_user_server():
    """Test function for the user's Flowise server integration."""
    helper = FlowiseIntegrationHelper()
    
    print("🔗 Testing connection to beagle-emerging-gnu.ngrok-free.app...")
    connection_test = await helper.test_connection()
    print(f"Connection status: {connection_test}")
    
    if connection_test.get("status") == "connected":
        print("\n🚀 Testing example flow with a sample question...")
        query_result = await helper.query_example_flow(
            "How can AI enhance creativity in research?", 
            max_messages=5
        )
        print(f"Query result status: {query_result.get('status')}")
        if query_result.get("status") == "success":
            response_text = query_result["response"].get("text", "No text response")
            print(f"Response preview: {response_text[:200]}...")
        else:
            print(f"Query error: {query_result.get('message')}")


if __name__ == "__main__":
    asyncio.run(test_user_server())