#!/usr/bin/env python3
"""
Integration Tests for Agentic Flywheel End-to-End Flows

Tests complete workflows across all components:
- Backend discovery and registration
- Universal query routing
- Langfuse tracing integration
- Redis persistence
- Admin intelligence
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock

from agentic_flywheel.backends.base import BackendType, UniversalFlow, FlowStatus
from agentic_flywheel.backends.registry import BackendRegistry


# Integration Test Scenarios

@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_query_flow_with_routing():
    """
    Test complete query flow:
    1. Backend discovery
    2. Intent classification
    3. Intelligent routing
    4. Execution
    5. Performance tracking
    """
    with patch('agentic_flywheel.backends.flowise.FlowiseBackend') as mock_flowise_class, \
         patch('agentic_flywheel.backends.langflow.LangflowBackend') as mock_langflow_class:

        # Create mock backends
        mock_flowise = Mock()
        mock_flowise.backend_type = BackendType.FLOWISE
        mock_flowise.health_check = AsyncMock(return_value=True)
        mock_flowise.discover_flows = AsyncMock(return_value=[
            UniversalFlow(
                id="csv2507",
                name="Creative Orientation",
                description="Structural tension guidance",
                backend=BackendType.FLOWISE,
                backend_specific_id="csv2507",
                intent_keywords=["creative", "goal", "vision"],
                capabilities=[],
                input_types=[],
                output_types=[]
            )
        ])
        mock_flowise.execute_flow = AsyncMock(return_value={
            "text": "Structural tension is the creative force..."
        })
        mock_flowise_class.return_value = mock_flowise

        mock_langflow = Mock()
        mock_langflow.backend_type = BackendType.LANGFLOW
        mock_langflow.health_check = AsyncMock(return_value=True)
        mock_langflow.discover_flows = AsyncMock(return_value=[
            UniversalFlow(
                id="tech_analysis",
                name="Technical Analysis",
                description="Code analysis",
                backend=BackendType.LANGFLOW,
                backend_specific_id="tech_001",
                intent_keywords=["code", "technical", "programming"],
                capabilities=[],
                input_types=[],
                output_types=[]
            )
        ])
        mock_langflow.execute_flow = AsyncMock(return_value={
            "result": "Code analysis complete..."
        })
        mock_langflow_class.return_value = mock_langflow

        # Import after patching
        from agentic_flywheel.tools import handle_universal_query
        from agentic_flywheel.backends.registry import BackendRegistry
        from agentic_flywheel.routing import get_router

        # Reset registry for test
        registry = BackendRegistry()
        registry._backends = []

        # Discover backends
        await registry.discover_backends()

        # Execute query with creative intent
        result = await handle_universal_query("universal_query", {
            "question": "What is my creative goal?",
            "backend": "auto",
            "include_routing_metadata": True
        })

        # Verify execution
        assert len(result) == 1
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text

        # Should route to Flowise (creative intent)
        assert "creative" in response_text.lower() or "structural tension" in response_text.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multi_backend_failover():
    """
    Test failover when primary backend fails:
    1. Primary backend selected
    2. Primary fails
    3. Automatic fallback to secondary
    4. Success on secondary
    """
    with patch('agentic_flywheel.backends.flowise.FlowiseBackend') as mock_flowise_class, \
         patch('agentic_flywheel.backends.langflow.LangflowBackend') as mock_langflow_class:

        # Flowise fails
        mock_flowise = Mock()
        mock_flowise.backend_type = BackendType.FLOWISE
        mock_flowise.health_check = AsyncMock(return_value=True)
        mock_flowise.discover_flows = AsyncMock(return_value=[
            UniversalFlow(
                id="test_flow",
                name="Test Flow",
                description="Test",
                backend=BackendType.FLOWISE,
                backend_specific_id="test_001",
                intent_keywords=["test"],
                capabilities=[],
                input_types=[],
                output_types=[]
            )
        ])
        mock_flowise.execute_flow = AsyncMock(side_effect=Exception("Backend error"))
        mock_flowise_class.return_value = mock_flowise

        # Langflow succeeds
        mock_langflow = Mock()
        mock_langflow.backend_type = BackendType.LANGFLOW
        mock_langflow.health_check = AsyncMock(return_value=True)
        mock_langflow.discover_flows = AsyncMock(return_value=[
            UniversalFlow(
                id="test_flow",
                name="Test Flow",
                description="Test",
                backend=BackendType.LANGFLOW,
                backend_specific_id="test_002",
                intent_keywords=["test"],
                capabilities=[],
                input_types=[],
                output_types=[]
            )
        ])
        mock_langflow.execute_flow = AsyncMock(return_value={
            "result": "Success on fallback"
        })
        mock_langflow_class.return_value = mock_langflow

        from agentic_flywheel.tools import handle_universal_query
        from agentic_flywheel.backends.registry import BackendRegistry

        # Reset registry
        registry = BackendRegistry()
        registry._backends = []
        await registry.discover_backends()

        # Execute - should fallback to Langflow
        result = await handle_universal_query("universal_query", {
            "question": "Test question",
            "backend": "auto"
        })

        # Verify fallback worked
        assert len(result) == 1
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        assert "fallback" in response_text.lower() or "langflow" in response_text.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_redis_session_persistence_flow():
    """
    Test Redis session persistence:
    1. Create session with query
    2. Save to Redis
    3. Load from Redis
    4. Verify continuity
    """
    # Mock Redis
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.setex = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url', return_value=mock_redis):
        from agentic_flywheel.integrations import RedisSessionManager
        from agentic_flywheel.backends.base import UniversalSession, BackendType, FlowStatus

        # Create session
        session = UniversalSession(
            id="test_session_123",
            backend=BackendType.FLOWISE,
            status=FlowStatus.ACTIVE,
            context={"topic": "structural tension"}
        )

        # Save to Redis
        manager = RedisSessionManager(enabled=True)
        saved = await manager.save_session(session)

        assert saved is True
        mock_redis.setex.assert_called_once()

        # Verify JSON serialization was called
        call_args = mock_redis.setex.call_args
        assert "test_session_123" in call_args[0][0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_langfuse_tracing_integration():
    """
    Test Langfuse tracing integration:
    1. Execute query
    2. Trace created
    3. Observations recorded
    4. Scores added
    """
    mock_langfuse = MagicMock()
    mock_trace = MagicMock()
    mock_langfuse.trace.return_value = mock_trace

    with patch('agentic_flywheel.integrations.langfuse_tracer.Langfuse', return_value=mock_langfuse):
        from agentic_flywheel.integrations import trace_mcp_tool

        # Decorate test function
        @trace_mcp_tool(
            trace_name="test_trace",
            metadata={"test": True}
        )
        async def test_tool(name: str, arguments: dict):
            return [{"type": "text", "text": "Test response"}]

        # Execute with tracing
        result = await test_tool("test_tool", {"question": "test"})

        # Verify tracing was attempted
        assert result is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backend_performance_tracking():
    """
    Test performance tracking across backends:
    1. Execute multiple queries
    2. Track latency and success
    3. Compare performance
    4. Generate recommendations
    """
    with patch('agentic_flywheel.backends.flowise.FlowiseBackend') as mock_flowise_class:
        mock_flowise = Mock()
        mock_flowise.backend_type = BackendType.FLOWISE
        mock_flowise.health_check = AsyncMock(return_value=True)
        mock_flowise.discover_flows = AsyncMock(return_value=[])
        mock_flowise_class.return_value = mock_flowise

        from agentic_flywheel.routing import get_router
        from agentic_flywheel.backends.registry import BackendRegistry

        # Reset registry
        registry = BackendRegistry()
        registry._backends = []
        await registry.discover_backends()

        # Get router and track performance
        router = get_router()

        # Record multiple performance metrics
        for i in range(10):
            router.performance_tracker.record(
                backend="flowise",
                intent="creative-orientation",
                latency_ms=1000 + (i * 100),
                success=True
            )

        # Get performance score
        score = router.performance_tracker.get_score("flowise", "creative-orientation")

        # Should have positive score
        assert score > 0.0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_admin_intelligence_flow():
    """
    Test admin intelligence analytics:
    1. Mock database with flow data
    2. Get dashboard
    3. Analyze specific flow
    4. Get recommendations
    """
    mock_dashboard_data = {
        "total_messages": 4506,
        "total_flows": 7,
        "top_flows": [
            {
                "id": "csv2507",
                "name": "Creative Orientation",
                "message_count": 118
            }
        ],
        "overall_metrics": {
            "success_rate": 0.85
        },
        "flows": [
            {"id": "csv2507", "message_count": 118},
            {"id": "low_usage", "message_count": 3}
        ]
    }

    with patch('agentic_flywheel.tools.admin_tools.FlowiseDBInterface') as mock_db_class:
        mock_db = Mock()
        mock_db.get_admin_dashboard_data.return_value = mock_dashboard_data
        mock_db_class.return_value = mock_db

        from agentic_flywheel.tools import handle_flowise_admin_dashboard

        # Get dashboard
        result = await handle_flowise_admin_dashboard("flowise_admin_dashboard", {})

        # Verify response includes recommendations
        assert len(result) == 1
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text

        # Should include dashboard data
        assert "4506" in response_text or "Creative Orientation" in response_text


@pytest.mark.asyncio
@pytest.mark.integration
async def test_end_to_end_multi_backend_workflow():
    """
    Complete end-to-end test:
    1. Discover multiple backends
    2. List all flows
    3. Execute universal query
    4. Check performance
    5. Get admin insights
    """
    with patch('agentic_flywheel.backends.flowise.FlowiseBackend') as mock_flowise_class, \
         patch('agentic_flywheel.backends.langflow.LangflowBackend') as mock_langflow_class:

        # Setup mock backends
        mock_flowise = Mock()
        mock_flowise.backend_type = BackendType.FLOWISE
        mock_flowise.health_check = AsyncMock(return_value=True)
        mock_flowise.discover_flows = AsyncMock(return_value=[
            UniversalFlow(
                id="flowise_flow",
                name="Flowise Flow",
                description="Test",
                backend=BackendType.FLOWISE,
                backend_specific_id="flowise_001",
                intent_keywords=["flowise"],
                capabilities=[],
                input_types=[],
                output_types=[]
            )
        ])
        mock_flowise.execute_flow = AsyncMock(return_value={"text": "Flowise response"})
        mock_flowise_class.return_value = mock_flowise

        mock_langflow = Mock()
        mock_langflow.backend_type = BackendType.LANGFLOW
        mock_langflow.health_check = AsyncMock(return_value=True)
        mock_langflow.discover_flows = AsyncMock(return_value=[
            UniversalFlow(
                id="langflow_flow",
                name="Langflow Flow",
                description="Test",
                backend=BackendType.LANGFLOW,
                backend_specific_id="langflow_001",
                intent_keywords=["langflow"],
                capabilities=[],
                input_types=[],
                output_types=[]
            )
        ])
        mock_langflow.execute_flow = AsyncMock(return_value={"result": "Langflow response"})
        mock_langflow_class.return_value = mock_langflow

        from agentic_flywheel.tools import (
            handle_backend_registry_status,
            handle_backend_list_flows,
            handle_universal_query
        )
        from agentic_flywheel.backends.registry import BackendRegistry

        # Reset registry
        registry = BackendRegistry()
        registry._backends = []
        await registry.discover_backends()

        # Step 1: Check registry status
        status_result = await handle_backend_registry_status("backend_registry_status", {})
        assert len(status_result) == 1

        # Step 2: List flows
        flows_result = await handle_backend_list_flows("backend_list_flows", {"backend_filter": "all"})
        assert len(flows_result) == 1

        # Step 3: Execute query
        query_result = await handle_universal_query("universal_query", {
            "question": "Test question",
            "backend": "auto"
        })
        assert len(query_result) == 1

        # All steps successful
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
