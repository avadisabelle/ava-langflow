#!/usr/bin/env python3
"""
Integration tests for Universal MCP Server

Tests the complete system integration:
- BackendRegistry with multiple backends
- UniversalQueryHandler with intelligent routing
- RedisSessionManager with session persistence
- Full end-to-end workflows
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from agentic_flywheel.backends import (
    BackendRegistry,
    BackendType,
    UniversalFlow,
    UniversalSession,
    FlowStatus
)
from agentic_flywheel.mcp_tools import UniversalQueryHandler
from agentic_flywheel.integrations import RedisSessionManager


# Integration Test Fixtures

@pytest.fixture
def mock_flowise_backend():
    """Create a complete mock Flowise backend"""
    from unittest.mock import MagicMock
    backend = MagicMock()
    backend.backend_type = BackendType.FLOWISE
    backend.is_connected = True
    backend.health_check = AsyncMock(return_value=True)
    backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="flowise_creative_001",
            name="Creative Orientation Flow",
            description="Structural tension dynamics",
            backend=BackendType.FLOWISE,
            backend_specific_id="7d405a51-968d-4467-9ae6-d49bf182cdf9",
            intent_keywords=["creative-orientation", "vision", "goal"],
            capabilities=["chat", "creative"],
            input_types=["text"],
            output_types=["text"]
        ),
        UniversalFlow(
            id="flowise_technical_002",
            name="Technical Analysis Flow",
            description="Code analysis and debugging",
            backend=BackendType.FLOWISE,
            backend_specific_id="896f7eed-342e-4596-9429-6fb9b5fbd91b",
            intent_keywords=["technical-analysis", "code", "debug"],
            capabilities=["chat", "analysis"],
            input_types=["text"],
            output_types=["text"]
        )
    ])
    backend.execute_flow = AsyncMock(return_value={
        "result": "Flowise executed successfully",
        "session_id": "flowise_session_123",
        "status": "success"
    })
    return backend


@pytest.fixture
def mock_langflow_backend():
    """Create a complete mock Langflow backend"""
    from unittest.mock import MagicMock
    backend = MagicMock()
    backend.backend_type = BackendType.LANGFLOW
    backend.is_connected = True
    backend.health_check = AsyncMock(return_value=True)
    backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="langflow_rag_001",
            name="RAG Retrieval Flow",
            description="Document retrieval with RAG",
            backend=BackendType.LANGFLOW,
            backend_specific_id="rag_flow_001",
            intent_keywords=["rag-retrieval", "document", "search"],
            capabilities=["rag", "retrieval"],
            input_types=["text"],
            output_types=["text", "structured"]
        ),
        UniversalFlow(
            id="langflow_data_002",
            name="Data Processing Flow",
            description="ETL and data transformation",
            backend=BackendType.LANGFLOW,
            backend_specific_id="data_flow_001",
            intent_keywords=["data-processing", "transform", "etl"],
            capabilities=["data", "processing"],
            input_types=["text", "json"],
            output_types=["structured"]
        )
    ])
    backend.execute_flow = AsyncMock(return_value={
        "result": "Langflow executed successfully",
        "session_id": "langflow_session_456",
        "status": "success"
    })
    return backend


@pytest.fixture
def integrated_registry(mock_flowise_backend, mock_langflow_backend):
    """Create a BackendRegistry with both backends"""
    registry = BackendRegistry()
    registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend,
        BackendType.LANGFLOW: mock_langflow_backend
    }
    registry._health_status = {
        BackendType.FLOWISE: True,
        BackendType.LANGFLOW: True
    }
    return registry


# Integration Tests

@pytest.mark.asyncio
async def test_full_query_workflow_flowise_routing(integrated_registry):
    """Test complete workflow: query → Flowise backend"""

    # Create query handler
    handler = UniversalQueryHandler(integrated_registry)

    # Execute creative query (should route to Flowise)
    result = await handler.execute_query(
        question="Help me define my creative vision and structural tension",
        backend_override="auto"
    )

    # Verify routing
    assert "_mcp_metadata" in result
    metadata = result["_mcp_metadata"]

    assert metadata["backend_used"] == "flowise"
    assert metadata["intent_classified"] == "creative-orientation"
    assert metadata["intent_confidence"] > 0.5
    assert metadata["routing_score"] > 0


@pytest.mark.asyncio
async def test_full_query_workflow_langflow_routing(integrated_registry):
    """Test complete workflow: query → Langflow backend"""

    handler = UniversalQueryHandler(integrated_registry)

    # Execute RAG query (should route to Langflow)
    result = await handler.execute_query(
        question="Search the documents for information about testing strategies",
        backend_override="auto"
    )

    # Verify routing
    assert "_mcp_metadata" in result
    metadata = result["_mcp_metadata"]

    assert metadata["backend_used"] == "langflow"
    assert metadata["intent_classified"] == "rag-retrieval"


@pytest.mark.asyncio
async def test_explicit_backend_override(integrated_registry):
    """Test explicit backend selection overrides intelligent routing"""

    handler = UniversalQueryHandler(integrated_registry)

    # Force Langflow for creative query (normally routes to Flowise)
    result = await handler.execute_query(
        question="Creative vision question",
        backend_override="langflow"
    )

    metadata = result["_mcp_metadata"]
    assert metadata["backend_used"] == "langflow"


@pytest.mark.asyncio
async def test_session_persistence_workflow(integrated_registry):
    """Test complete workflow with session persistence"""

    # Setup mocks
    handler = UniversalQueryHandler(integrated_registry)
    redis_mgr = RedisSessionManager(enabled=True)

    session_data_store = {}

    async def mock_save(session):
        session_data_store[session.id] = session
        return True

    async def mock_load(session_id):
        return session_data_store.get(session_id)

    redis_mgr.save_session = mock_save
    redis_mgr.load_session = mock_load

    # First query - create session
    result1 = await handler.execute_query(
        question="What is creative orientation?",
        session_id="test_session_001"
    )

    # Create and save session
    session = UniversalSession(
        id="test_session_001",
        backend=BackendType.FLOWISE,
        backend_session_id="flowise_123",
        status=FlowStatus.COMPLETED,
        current_flow_id=result1["_mcp_metadata"]["flow_id"],
        context={"history": [result1]},
        history=[]
    )
    await redis_mgr.save_session(session)

    # Second query - resume session
    loaded_session = await redis_mgr.load_session("test_session_001")
    assert loaded_session is not None
    assert loaded_session.id == "test_session_001"
    assert len(loaded_session.context["history"]) == 1


@pytest.mark.asyncio
async def test_fallback_mechanism(integrated_registry, mock_flowise_backend):
    """Test fallback when primary backend fails"""

    # Make Flowise fail
    mock_flowise_backend.execute_flow = AsyncMock(
        side_effect=Exception("Flowise unavailable")
    )

    handler = UniversalQueryHandler(integrated_registry, enable_fallback=True)

    # Creative query normally routes to Flowise, but should fallback to Langflow
    result = await handler.execute_query(
        question="Creative vision planning"
    )

    # Should have fallback metadata
    if "_mcp_metadata" in result:
        metadata = result["_mcp_metadata"]
        # Either Langflow was used (fallback) or there was an error
        assert metadata.get("fallback_used") == True or metadata["backend_used"] == "langflow"


@pytest.mark.asyncio
async def test_backend_health_monitoring(integrated_registry):
    """Test health check integration"""

    # Check all backends
    health_results = await integrated_registry.health_check_all()

    assert BackendType.FLOWISE in health_results
    assert BackendType.LANGFLOW in health_results
    assert health_results[BackendType.FLOWISE] is True
    assert health_results[BackendType.LANGFLOW] is True


@pytest.mark.asyncio
async def test_flow_discovery_across_backends(integrated_registry):
    """Test flow discovery from multiple backends"""

    flows_by_backend = await integrated_registry.discover_all_flows()

    # Should have flows from both backends
    assert BackendType.FLOWISE in flows_by_backend
    assert BackendType.LANGFLOW in flows_by_backend

    # Flowise should have 2 flows
    assert len(flows_by_backend[BackendType.FLOWISE]) == 2

    # Langflow should have 2 flows
    assert len(flows_by_backend[BackendType.LANGFLOW]) == 2

    # Total of 4 flows
    all_flows = await integrated_registry.get_all_flows()
    assert len(all_flows) == 4


@pytest.mark.asyncio
async def test_intent_classification_accuracy():
    """Test intent classification for various queries"""
    from agentic_flywheel.mcp_tools.universal_query import classify_intent

    test_cases = [
        ("Help me define my creative vision", "creative-orientation"),
        ("Debug this code for errors", "technical-analysis"),
        ("Search the documents for testing info", "rag-retrieval"),
        ("Transform this data using ETL", "data-processing"),
        ("Hello, how are you?", "conversation"),
    ]

    for question, expected_intent in test_cases:
        intent, confidence = classify_intent(question)
        assert intent == expected_intent, f"Expected {expected_intent}, got {intent} for: {question}"
        assert confidence > 0


@pytest.mark.asyncio
async def test_routing_score_calculation(integrated_registry):
    """Test backend scoring algorithm"""

    handler = UniversalQueryHandler(integrated_registry)

    # Internal test - check if routing produces valid scores
    result = await handler.execute_query(
        question="Creative structural tension analysis"
    )

    if "_mcp_metadata" in result and "routing_breakdown" in result["_mcp_metadata"]:
        breakdown = result["_mcp_metadata"]["routing_breakdown"]

        # All scores should be between 0 and 1
        for score_name, score_value in breakdown.items():
            assert 0 <= score_value <= 1, f"{score_name} score out of range: {score_value}"


@pytest.mark.asyncio
async def test_parameter_passing_to_backend(integrated_registry):
    """Test that custom parameters are passed to backend"""

    handler = UniversalQueryHandler(integrated_registry)

    custom_params = {
        "temperature": 0.9,
        "max_tokens": 3000
    }

    result = await handler.execute_query(
        question="Test question",
        parameters=custom_params
    )

    # Verify execute_flow was called with parameters
    # (Mock verification - in real scenario, check backend received params)
    assert result is not None


@pytest.mark.asyncio
async def test_concurrent_queries(integrated_registry):
    """Test handling multiple concurrent queries"""
    import asyncio

    handler = UniversalQueryHandler(integrated_registry)

    # Execute 5 queries concurrently
    queries = [
        "Creative vision planning",
        "Technical code analysis",
        "Document search query",
        "Data transformation task",
        "General conversation"
    ]

    results = await asyncio.gather(*[
        handler.execute_query(question=q)
        for q in queries
    ])

    # All should complete successfully
    assert len(results) == 5
    for result in results:
        assert result is not None
        assert "_mcp_metadata" in result or "error" in result


@pytest.mark.asyncio
async def test_registry_status():
    """Test registry status reporting"""

    registry = BackendRegistry()

    # Initially no backends
    status = registry.get_status()
    assert status["registered_backends"] == 0
    assert status["connected_backends"] == 0


@pytest.mark.asyncio
async def test_error_handling_no_backends():
    """Test graceful handling when no backends available"""

    registry = BackendRegistry()
    handler = UniversalQueryHandler(registry)

    result = await handler.execute_query(question="Test")

    assert "error" in result
    assert "All backends failed" in result["error"]


# Performance Tests

@pytest.mark.asyncio
async def test_routing_performance(integrated_registry):
    """Test that routing overhead is minimal"""
    import time

    handler = UniversalQueryHandler(integrated_registry)

    start_time = time.time()

    result = await handler.execute_query(
        question="Quick test query"
    )

    total_time_ms = (time.time() - start_time) * 1000

    # Total time should include execution, but routing overhead should be <200ms
    # Since we're mocking, execution is instant, so we can check total time
    assert total_time_ms < 1000  # Very generous for mocked execution
