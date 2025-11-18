#!/usr/bin/env python3
"""
Langflow Backend Adapter
Implements the universal flow backend interface for Langflow platforms.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import httpx

from ..base import (
    FlowBackend,
    BackendType,
    UniversalFlow,
    UniversalSession,
    UniversalPerformanceMetrics,
    FlowStatus,
)


class LangflowBackend(FlowBackend):
    """
    Langflow platform adapter implementing the universal flow interface.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None, **config):
        super().__init__(BackendType.LANGFLOW, config)
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    # Connection Management
    async def connect(self) -> bool:
        """
        Establishes an asynchronous HTTP client session for the backend.
        """
        if self._client and not self._client.is_closed:
            return True
        
        headers = {"x-api-key": self.api_key} if self.api_key else {}
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=self.config.get("timeout", 30.0)
        )
        self._is_connected = await self.health_check()
        return self.is_connected

    async def disconnect(self) -> None:
        """
        Closes the asynchronous HTTP client session.
        """
        if self._client and not self._client.is_closed:
            await self._client.aclose()
        self._client = None
        self._is_connected = False

    async def health_check(self) -> bool:
        """
        Verifies the backend is healthy and responsive by checking a lightweight endpoint.
        """
        if not self._client:
            return False
        try:
            # According to the spec, /api/v1/flows is a potential lightweight endpoint
            response = await self._client.get("/api/v1/flows")
            response.raise_for_status()
            return True
        except httpx.RequestError as e:
            # In a real implementation, we'd log this error
            print(f"Health check failed: {e}")
            return False
        except httpx.HTTPStatusError as e:
            # Handle non-2xx responses
            print(f"Health check received non-2xx status: {e.response.status_code}")
            return False

    # Flow Discovery and Management
    async def discover_flows(self) -> List[UniversalFlow]:
        """
        Discovers and catalogs all available flows from the Langflow backend.
        """
        if not self.is_connected:
            return []
        try:
            response = await self._client.get("/api/v1/flows")
            response.raise_for_status()
            flows_data = response.json()
            # The structure of flows_data is an assumption based on the RISE spec.
            # It should be verified with a real Langflow API response.
            # Assuming flows_data is a list of flow dictionaries.
            return [self.to_universal_flow(flow_data) for flow_data in flows_data]
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"Failed to discover flows: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred during flow discovery: {e}")
            return []

    async def get_flow(self, flow_id: str) -> Optional[UniversalFlow]:
        """
        Retrieves a specific flow by its backend-specific ID.
        """
        if not self.is_connected:
            return None
        try:
            response = await self._client.get(f"/api/v1/flows/{flow_id}")
            response.raise_for_status()
            flow_data = response.json()
            return self.to_universal_flow(flow_data)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"Failed to get flow {flow_id}: {e}")
            return None

    async def create_flow(self, flow_definition: Dict[str, Any]) -> UniversalFlow:
        pass

    async def update_flow(self, flow_id: str, updates: Dict[str, Any]) -> UniversalFlow:
        pass

    async def delete_flow(self, flow_id: str) -> bool:
        pass

    # Flow Execution
    async def execute_flow(
        self,
        flow_id: str,
        input_data: Any,
        parameters: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a flow with given input and parameters.
        """
        if not self.is_connected:
            return {"error": "Backend is not connected."}
        
        # The structure of the request body is an assumption.
        # It needs to be verified with the actual Langflow API.
        request_body = {
            "input_value": input_data,
            "tweaks": parameters or {}
        }
        
        try:
            response = await self._client.post(f"/api/v1/run/{flow_id}", json=request_body)
            response.raise_for_status()
            result_data = response.json()
            
            # The structure of the result_data is an assumption.
            # This helper will parse the actual result from the response.
            return self._transform_execution_result(result_data)
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"Failed to execute flow {flow_id}: {e}")
            return {"error": str(e)}

    async def stream_flow(
        self,
        flow_id: str,
        input_data: Any,
        parameters: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ):
        """
        Executes a flow with a streaming response.
        NOTE: This is a basic, non-streaming implementation for now.
        It will be updated once the actual streaming API is investigated.
        """
        result = await self.execute_flow(flow_id, input_data, parameters, session_id)
        yield result
        
    def _transform_execution_result(self, result_data: Any) -> Dict[str, Any]:
        """
        Transforms the backend-specific execution result into a universal format.
        This is a placeholder based on assumptions.
        """
        # Assuming the main result is in a nested structure. This needs verification.
        # For example: result_data.get('results', {}).get('chat_output', {}).get('outputs', {}).get('output')
        main_result = "Placeholder result from Langflow"
        
        return {
            "result": main_result,
            "raw": result_data,
        }

    # Session Management (assuming stateless interaction for now)
    async def create_session(
        self, flow_id: str, config: Optional[Dict[str, Any]] = None
    ) -> UniversalSession:
        """
        Creates a mock session, as Langflow execution is treated as stateless.
        """
        session_id = f"langflow_session_{int(datetime.now().timestamp())}"
        return UniversalSession(
            id=session_id,
            backend=self.backend_type,
            backend_session_id=session_id, # Mocked
            status=FlowStatus.RUNNING,
            current_flow_id=flow_id,
        )

    async def get_session(self, session_id: str) -> Optional[UniversalSession]:
        """Returns None, assuming stateless interaction."""
        return None

    async def update_session(
        self, session_id: str, updates: Dict[str, Any]
    ) -> UniversalSession:
        """Returns a mock session, as there's no state to update."""
        return await self.create_session(updates.get("current_flow_id", ""))

    async def delete_session(self, session_id: str) -> bool:
        """Returns True, as there's no session to delete."""
        return True

    async def list_sessions(
        self, flow_id: Optional[str] = None
    ) -> List[UniversalSession]:
        """Returns an empty list, assuming stateless interaction."""
        return []

    # Performance and Analytics (placeholders)
    async def get_performance_metrics(
        self, flow_id: str
    ) -> UniversalPerformanceMetrics:
        """Returns empty performance metrics."""
        return UniversalPerformanceMetrics(backend=self.backend_type, flow_id=flow_id)

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Returns empty system metrics."""
        return {}

    async def analyze_usage_patterns(
        self, flow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Returns empty usage patterns."""
        return {}

    # Configuration and Parameters (placeholders)
    async def validate_parameters(
        self, flow_id: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pass-through validation, returns parameters as is."""
        return {"validated": True, "parameters": parameters}

    async def get_parameter_schema(self, flow_id: str) -> Dict[str, Any]:
        """Returns an empty schema."""
        return {}

    # Utility Methods
    def to_universal_flow(self, backend_flow: Any) -> UniversalFlow:
        """
        Converts a backend-specific flow representation (dict from Langflow API)
        into the UniversalFlow format with intelligent capability inference.
        """
        flow_id = backend_flow.get("id", "")
        name = backend_flow.get("name", "Unnamed Langflow Flow")
        description = backend_flow.get("description", "")

        # Extract intent keywords and capabilities from flow graph structure
        intent_keywords = self._extract_intent_keywords(backend_flow)
        capabilities = self._infer_capabilities_from_flow(backend_flow)
        input_types, output_types = self._detect_io_types(backend_flow)

        return UniversalFlow(
            id=f"langflow_{flow_id}",
            name=name,
            description=description,
            backend=self.backend_type,
            backend_specific_id=flow_id,
            intent_keywords=intent_keywords,
            capabilities=capabilities,
            input_types=input_types,
            output_types=output_types,
        )

    def _extract_intent_keywords(self, backend_flow: Dict[str, Any]) -> List[str]:
        """
        Extract intent keywords from flow name, description, and graph structure.
        """
        keywords = set()

        # Extract from name and description
        text = f"{backend_flow.get('name', '')} {backend_flow.get('description', '')}".lower()

        # Common intent keyword patterns
        intent_patterns = {
            'chat': ['chat', 'conversation', 'dialog', 'talk'],
            'rag': ['rag', 'retrieval', 'search', 'document', 'knowledge'],
            'code': ['code', 'programming', 'development', 'script'],
            'analysis': ['analyze', 'analysis', 'evaluate', 'assess'],
            'generation': ['generate', 'create', 'produce', 'build'],
            'translation': ['translate', 'translation', 'convert'],
            'summarize': ['summarize', 'summary', 'condense'],
            'question': ['question', 'qa', 'answer', 'ask'],
        }

        for intent, patterns in intent_patterns.items():
            if any(pattern in text for pattern in patterns):
                keywords.add(intent)

        # Analyze graph nodes if available
        data = backend_flow.get('data', {})
        nodes = data.get('nodes', []) if isinstance(data, dict) else []

        for node in nodes:
            if isinstance(node, dict):
                node_type = node.get('type', '').lower()
                node_name = node.get('data', {}).get('node', {}).get('display_name', '').lower()

                # Infer from node types
                if 'llm' in node_type or 'chat' in node_type:
                    keywords.add('chat')
                if 'vector' in node_type or 'retriever' in node_type:
                    keywords.add('rag')
                    keywords.add('search')
                if 'agent' in node_type:
                    keywords.add('agent')
                    keywords.add('autonomous')
                if 'tool' in node_type:
                    keywords.add('tools')
                if 'prompt' in node_type:
                    keywords.add('prompt')

        return list(keywords)

    def _infer_capabilities_from_flow(self, backend_flow: Dict[str, Any]) -> List[str]:
        """
        Infer flow capabilities from graph structure and components.
        """
        capabilities = set(['chat'])  # All Langflow flows support chat

        # Analyze graph nodes
        data = backend_flow.get('data', {})
        nodes = data.get('nodes', []) if isinstance(data, dict) else []

        for node in nodes:
            if isinstance(node, dict):
                node_type = node.get('type', '').lower()

                # Capability inference rules
                if any(kw in node_type for kw in ['vector', 'retriever', 'embedding']):
                    capabilities.add('rag')
                    capabilities.add('retrieval')

                if 'agent' in node_type:
                    capabilities.add('agent')
                    capabilities.add('autonomous')

                if any(kw in node_type for kw in ['tool', 'function', 'api']):
                    capabilities.add('tool-use')

                if any(kw in node_type for kw in ['code', 'python', 'javascript']):
                    capabilities.add('code-execution')

                if 'memory' in node_type or 'buffer' in node_type:
                    capabilities.add('memory')

                if 'output' in node_type or 'response' in node_type:
                    capabilities.add('structured-output')

        # Infer from flow metadata
        description = backend_flow.get('description', '').lower()
        if 'streaming' in description:
            capabilities.add('streaming')
        if 'multi' in description or 'multiple' in description:
            capabilities.add('multi-step')

        return list(capabilities)

    def _detect_io_types(self, backend_flow: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """
        Detect input and output types supported by the flow.
        """
        input_types = set(['text'])  # Default: all flows accept text
        output_types = set(['text'])  # Default: all flows produce text

        # Analyze graph nodes for special I/O types
        data = backend_flow.get('data', {})
        nodes = data.get('nodes', []) if isinstance(data, dict) else []

        for node in nodes:
            if isinstance(node, dict):
                node_type = node.get('type', '').lower()

                # Input type detection
                if 'file' in node_type or 'document' in node_type:
                    input_types.add('file')
                if 'image' in node_type:
                    input_types.add('image')
                if 'json' in node_type or 'structured' in node_type:
                    input_types.add('json')
                if 'csv' in node_type:
                    input_types.add('csv')

                # Output type detection
                if 'structured' in node_type or 'json' in node_type:
                    output_types.add('structured')
                if 'stream' in node_type:
                    output_types.add('stream')

        return list(input_types), list(output_types)

    def from_universal_flow(self, universal_flow: UniversalFlow) -> Any:
        # To be implemented
        pass

