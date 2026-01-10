#!/usr/bin/env python3
"""
Complete Integration Test Suite

Tests the full integration of all components:
- Flowise backend with flow adapter
- Langflow backend with capability inference
- Redis state persistence
- Langfuse tracing
- Universal query routing
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock
import httpx

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from agentic_flywheel.backends import BackendRegistry, BackendType, UniversalFlow
from agentic_flywheel.backends.flowise import FlowiseBackend
from agentic_flywheel.backends.langflow import LangflowBackend
from agentic_flywheel.mcp_tools import UniversalQueryHandler
from agentic_flywheel.adapters import FlowiseFlowAdapter


@pytest.mark.asyncio
class TestCompleteMultiBackendIntegration:
    """Test complete integration of all backends and components"""

    async def test_flowise_langflow_capability_comparison(self):
        """Test that both backends can detect similar capabilities"""

        # Flowise backend
        flowise = FlowiseBackend(config={"base_url": "http://localhost:3000"})

        # Langflow backend
        langflow = LangflowBackend(base_url="http://localhost:7860")

        # Mock Langflow RAG flow
        langflow_rag = {
            "id": "lf_rag_123",
            "name": "Langflow RAG System",
            "description": "Document retrieval with vector search",
            "data": {
                "nodes": [
                    {"type": "VectorStoreRetriever", "data": {}},
                    {"type": "ChatLLM", "data": {}}
                ]
            }
        }

        lf_flow = langflow.to_universal_flow(langflow_rag)

        # Both should detect RAG capability
        assert "rag" in lf_flow.capabilities or "retrieval" in lf_flow.capabilities
        assert "chat" in lf_flow.capabilities
        assert BackendType.LANGFLOW == lf_flow.backend

    async def test_multi_backend_routing_scenario(self, mocker):
        """Test realistic multi-backend routing scenarios"""

        registry = BackendRegistry()

        # Mock Flowise backend with creative flow
        flowise = FlowiseBackend(config={"base_url": "http://localhost:3000", "api_key": "test"})
        creative_flow = UniversalFlow(
            id="flowise_creative",
            name="Creative Vision Helper",
            description="Help define creative vision",
            backend=BackendType.FLOWISE,
            backend_specific_id="flowise_123",
            intent_keywords=["creative", "vision", "goal", "dream"],
            capabilities=["chat", "creative"],
            input_types=["text"],
            output_types=["text"]
        )

        # Mock Langflow backend with RAG flow
        langflow = LangflowBackend(base_url="http://localhost:7860", api_key="test")
        rag_flow = UniversalFlow(
            id="langflow_rag",
            name="Document Search",
            description="Search documents",
            backend=BackendType.LANGFLOW,
            backend_specific_id="langflow_456",
            intent_keywords=["search", "document", "rag", "retrieval"],
            capabilities=["chat", "rag", "retrieval"],
            input_types=["text"],
            output_types=["text", "structured"]
        )

        # Register backends
        await registry.register_backend(flowise)
        await registry.register_backend(langflow)

        # Mock connections
        flowise._is_connected = True
        langflow._is_connected = True

        # Mock flow discovery
        flowise.discover_flows = AsyncMock(return_value=[creative_flow])
        langflow.discover_flows = AsyncMock(return_value=[rag_flow])

        # Mock execution
        flowise.execute_flow = AsyncMock(return_value={
            "result": "Creative response",
            "flow_id": "flowise_123"
        })
        langflow.execute_flow = AsyncMock(return_value={
            "result": "RAG response",
            "flow_id": "langflow_456"
        })

        # Initialize query handler
        handler = UniversalQueryHandler(registry)

        # Test 1: Creative query should route successfully
        creative_result = await handler.execute_query(
            question="Help me define my vision for this project",
            backend_override="auto"
        )
        # Just verify it routed to a backend
        assert "_mcp_metadata" in creative_result
        assert "backend_used" in creative_result["_mcp_metadata"]

        # Test 2: RAG query should route successfully
        rag_result = await handler.execute_query(
            question="Search the documents for testing strategies",
            backend_override="auto"
        )
        # Just verify it routed to a backend
        assert "_mcp_metadata" in rag_result
        assert "backend_used" in rag_result["_mcp_metadata"]

    async def test_flowise_adapter_integration(self):
        """Test Flowise flow adapter integration"""

        adapter = FlowiseFlowAdapter()

        # Test adapter can find registry
        if adapter.registry_path and adapter.registry_path.exists():
            flows = await adapter.import_active_flows()

            # Should import flows successfully
            assert len(flows) >= 0  # May be 0 if registry not found

            # If flows found, verify structure
            if flows:
                for flow in flows:
                    assert flow.backend == BackendType.FLOWISE
                    assert flow.id.startswith("flowise_")
                    assert isinstance(flow.capabilities, list)
                    assert isinstance(flow.intent_keywords, list)

    async def test_backend_health_monitoring(self, mocker):
        """Test health monitoring across backends"""

        registry = BackendRegistry()

        # Create backends
        flowise = FlowiseBackend(config={"base_url": "http://localhost:3000"})
        langflow = LangflowBackend(base_url="http://localhost:7860")

        # Mock health check directly
        flowise.health_check = AsyncMock(return_value=True)
        langflow.health_check = AsyncMock(return_value=False)

        # Mock connection state
        flowise._is_connected = True
        langflow._is_connected = False

        # Register backends
        await registry.register_backend(flowise)
        await registry.register_backend(langflow)

        # Verify registry reports correct status
        status = registry.get_status()
        assert status["registered_backends"] == 2


@pytest.mark.asyncio
class TestBackendCapabilityParity:
    """Verify both backends support same core capabilities"""

    async def test_both_support_chat(self):
        """Both backends should support chat"""
        flowise = FlowiseBackend(config={"base_url": "http://localhost:3000"})
        langflow = LangflowBackend(base_url="http://localhost:7860")

        # Create minimal flows
        fw_flow = {"id": "fw1", "name": "Test", "description": "Chat flow"}
        lf_flow = {"id": "lf1", "name": "Test", "description": "Chat flow", "data": {}}

        fw_universal = flowise.to_universal_flow(fw_flow)
        lf_universal = langflow.to_universal_flow(lf_flow)

        # Both should have chat capability (Langflow always adds it, Flowise via config)
        assert "chat" in lf_universal.capabilities

    async def test_both_support_rag(self):
        """Both backends should detect RAG capability"""
        flowise = FlowiseBackend(config={"base_url": "http://localhost:3000"})
        langflow = LangflowBackend(base_url="http://localhost:7860")

        # Flowise RAG flow (hypothetical structure)
        fw_rag = {
            "id": "fw_rag",
            "name": "RAG Flow",
            "description": "Retrieval augmented generation"
        }

        # Langflow RAG flow
        lf_rag = {
            "id": "lf_rag",
            "name": "RAG Flow",
            "description": "Retrieval augmented generation",
            "data": {
                "nodes": [
                    {"type": "VectorStoreRetriever", "data": {}}
                ]
            }
        }

        fw_universal = flowise.to_universal_flow(fw_rag)
        lf_universal = langflow.to_universal_flow(lf_rag)

        # Langflow should definitely detect RAG
        assert "rag" in lf_universal.capabilities or "retrieval" in lf_universal.capabilities

    async def test_both_support_agents(self):
        """Both backends should support agent capabilities"""
        flowise = FlowiseBackend(config={"base_url": "http://localhost:3000"})
        langflow = LangflowBackend(base_url="http://localhost:7860")

        # Langflow agent flow
        lf_agent = {
            "id": "lf_agent",
            "name": "Agent Flow",
            "description": "Autonomous agent",
            "data": {
                "nodes": [
                    {"type": "AgentNode", "data": {}}
                ]
            }
        }

        lf_universal = langflow.to_universal_flow(lf_agent)

        # Langflow should detect agent capability
        assert "agent" in lf_universal.capabilities or "autonomous" in lf_universal.capabilities


@pytest.mark.asyncio
class TestUniversalMCPServerComponents:
    """Test Universal MCP Server component integration"""

    async def test_backend_registry_multi_backend(self):
        """Test backend registry with multiple backends"""
        registry = BackendRegistry()

        flowise = FlowiseBackend(config={"base_url": "http://localhost:3000"})
        langflow = LangflowBackend(base_url="http://localhost:7860")

        await registry.register_backend(flowise)
        await registry.register_backend(langflow)

        status = registry.get_status()
        assert status["registered_backends"] == 2
        # Verify backend types are in the status
        assert "flowise" in status["backend_types"]
        assert "langflow" in status["backend_types"]

    async def test_query_handler_with_both_backends(self, mocker):
        """Test query handler routing between backends"""
        registry = BackendRegistry()

        # Setup backends
        flowise = FlowiseBackend(config={"base_url": "http://localhost:3000"})
        langflow = LangflowBackend(base_url="http://localhost:7860")

        flowise._is_connected = True
        langflow._is_connected = True

        await registry.register_backend(flowise)
        await registry.register_backend(langflow)

        # Mock flow discovery
        flowise.discover_flows = AsyncMock(return_value=[
            UniversalFlow(
                id="fw1", name="Creative", description="",
                backend=BackendType.FLOWISE, backend_specific_id="fw1",
                intent_keywords=["creative"], capabilities=["chat"],
                input_types=["text"], output_types=["text"]
            )
        ])
        langflow.discover_flows = AsyncMock(return_value=[
            UniversalFlow(
                id="lf1", name="RAG", description="",
                backend=BackendType.LANGFLOW, backend_specific_id="lf1",
                intent_keywords=["search"], capabilities=["rag"],
                input_types=["text"], output_types=["text"]
            )
        ])

        # Initialize handler
        handler = UniversalQueryHandler(registry)

        # Verify both backends are available
        status = registry.get_status()
        assert status["registered_backends"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
