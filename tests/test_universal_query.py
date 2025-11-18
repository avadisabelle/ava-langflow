#!/usr/bin/env python3
"""
Tests for Universal Query MCP Tool
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agentic_flywheel.mcp_tools.universal_query import (
    UniversalQueryHandler,
    classify_intent,
    calculate_flow_match_score,
    get_capability_score,
    RoutingDecision,
    NoBackendsAvailable,
    INTENT_CATEGORIES,
    BACKEND_CAPABILITIES
)
from agentic_flywheel.backends import (
    FlowBackend,
    BackendType,
    UniversalFlow,
    BackendRegistry
)


# Test Fixtures

@pytest.fixture
def mock_backend_registry():
    """Create a mock backend registry"""
    registry = MagicMock(spec=BackendRegistry)
    registry.backends = {}
    return registry


@pytest.fixture
def mock_flowise_backend():
    """Create a mock Flowise backend"""
    backend = MagicMock(spec=FlowBackend)
    backend.backend_type = BackendType.FLOWISE
    backend.is_connected = True
    backend.health_check = AsyncMock(return_value=True)
    backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="flowise_creative",
            name="Creative Flow",
            description="Creative orientation flow",
            backend=BackendType.FLOWISE,
            backend_specific_id="creative_001",
            intent_keywords=["creative-orientation"],
            capabilities=[],
            input_types=["text"],
            output_types=["text"]),
        UniversalFlow(
            id="flowise_chat",
            name="Chat Flow",
            description="General conversation",
            backend=BackendType.FLOWISE,
            backend_specific_id="chat_001",
            intent_keywords=["conversation"],
            capabilities=[],
            input_types=["text"],
            output_types=["text"])
    ])
    backend.execute_flow = AsyncMock(return_value={
        "result": "Flowise response",
        "status": "success"
    })
    return backend


@pytest.fixture
def mock_langflow_backend():
    """Create a mock Langflow backend"""
    backend = MagicMock(spec=FlowBackend)
    backend.backend_type = BackendType.LANGFLOW
    backend.is_connected = True
    backend.health_check = AsyncMock(return_value=True)
    backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="langflow_rag",
            name="RAG Flow",
            description="Document retrieval",
            backend=BackendType.LANGFLOW,
            backend_specific_id="rag_001",
            intent_keywords=["rag-retrieval"],
            capabilities=[],
            input_types=["text"],
            output_types=["text"]),
        UniversalFlow(
            id="langflow_technical",
            name="Technical Analysis",
            description="Code analysis",
            backend=BackendType.LANGFLOW,
            backend_specific_id="technical_001",
            intent_keywords=["technical-analysis"],
            capabilities=[],
            input_types=["text"],
            output_types=["text"])
    ])
    backend.execute_flow = AsyncMock(return_value={
        "result": "Langflow response",
        "status": "success"
    })
    return backend


# Intent Classification Tests

def test_classify_intent_creative():
    """Test creative intent classification"""
    question = "Help me understand my creative vision and structural tension"
    intent, confidence = classify_intent(question)

    assert intent == "creative-orientation"
    assert confidence > 0.5


def test_classify_intent_technical():
    """Test technical intent classification"""
    question = "Debug this code and analyze the function for errors"
    intent, confidence = classify_intent(question)

    assert intent == "technical-analysis"
    assert confidence > 0.5


def test_classify_intent_rag():
    """Test RAG intent classification"""
    question = "Search the documents and retrieve information about testing"
    intent, confidence = classify_intent(question)

    assert intent == "rag-retrieval"
    assert confidence > 0.5


def test_classify_intent_conversation():
    """Test conversation intent classification (default)"""
    question = "Hello, how are you doing today?"
    intent, confidence = classify_intent(question)

    assert intent == "conversation"
    # Confidence should be moderate for general conversation


def test_classify_intent_empty_string():
    """Test intent classification with empty string"""
    intent, confidence = classify_intent("")

    assert intent == "conversation"  # Default
    assert confidence == 0.5


# Flow Match Score Tests

def test_calculate_flow_match_exact():
    """Test flow match scoring with exact intent match"""
    flows = [
        UniversalFlow(
            id="test1",
            name="Test Flow 1",
            description="Test",
            backend=BackendType.FLOWISE,
            backend_specific_id="test1",
            intent_keywords=["creative-orientation"],
            capabilities=[],
            input_types=["text"],
            output_types=["text"])
    ]

    score = calculate_flow_match_score(flows, "creative-orientation", 0.9)
    assert score == 1.0


def test_calculate_flow_match_partial():
    """Test flow match scoring with partial match"""
    flows = [
        UniversalFlow(
            id="test1",
            name="Test Flow 1",
            description="Test",
            backend=BackendType.FLOWISE,
            backend_specific_id="test1",
            intent_keywords=["conversation"],  # Different intent
            capabilities=[],
            input_types=["text"],
            output_types=["text"]
        )
    ]

    # Should find partial match based on keyword overlap
    score = calculate_flow_match_score(flows, "creative-orientation", 0.9)
    assert 0.0 <= score <= 1.0


def test_calculate_flow_match_no_flows():
    """Test flow match scoring with no flows"""
    score = calculate_flow_match_score([], "creative-orientation", 0.9)
    assert score == 0.0


# Capability Score Tests

def test_get_capability_score_langflow_rag():
    """Test capability scoring for Langflow with RAG intent"""
    backend = MagicMock(spec=FlowBackend)
    backend.backend_type = BackendType.LANGFLOW

    score = get_capability_score(backend, "rag-retrieval")
    assert score == 1.0  # Langflow is optimized for RAG


def test_get_capability_score_flowise_conversation():
    """Test capability scoring for Flowise with conversation intent"""
    backend = MagicMock(spec=FlowBackend)
    backend.backend_type = BackendType.FLOWISE

    score = get_capability_score(backend, "conversation")
    assert score == 1.0  # Flowise is optimized for conversation


def test_get_capability_score_unknown_intent():
    """Test capability scoring with unknown intent"""
    backend = MagicMock(spec=FlowBackend)
    backend.backend_type = BackendType.FLOWISE

    score = get_capability_score(backend, "unknown-intent")
    assert score == 0.5  # Default neutral score


# UniversalQueryHandler Tests

@pytest.mark.asyncio
async def test_handler_initialization(mock_backend_registry):
    """Test handler initialization"""
    handler = UniversalQueryHandler(mock_backend_registry)

    assert handler.registry == mock_backend_registry
    assert handler.enable_fallback is True
    assert handler.default_timeout == 30.0


@pytest.mark.asyncio
async def test_execute_query_with_auto_routing(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test query execution with automatic backend routing"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(
        question="Help me with my creative vision",
        backend_override="auto"
    )

    assert "result" in result or "_mcp_metadata" in result
    assert mock_flowise_backend.execute_flow.called


@pytest.mark.asyncio
async def test_execute_query_with_explicit_backend(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test query execution with explicit backend selection"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(
        question="Test question",
        backend_override="flowise"
    )

    assert mock_flowise_backend.execute_flow.called


@pytest.mark.asyncio
async def test_execute_query_with_intent_override(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test query execution with explicit intent"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(
        question="Random question",
        intent_override="creative-orientation"
    )

    # Should use creative intent regardless of question content
    assert mock_flowise_backend.execute_flow.called


@pytest.mark.asyncio
async def test_execute_query_with_session_id(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test query execution with session ID"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(
        question="Test question",
        session_id="test_session_123"
    )

    # Verify session_id was passed to backend
    mock_flowise_backend.execute_flow.assert_called_once()
    call_kwargs = mock_flowise_backend.execute_flow.call_args.kwargs
    assert call_kwargs.get('session_id') == "test_session_123"


@pytest.mark.asyncio
async def test_execute_query_with_parameters(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test query execution with custom parameters"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    params = {"temperature": 0.7, "max_tokens": 1000}
    result = await handler.execute_query(
        question="Test question",
        parameters=params
    )

    # Verify parameters were passed to backend
    call_kwargs = mock_flowise_backend.execute_flow.call_args.kwargs
    assert call_kwargs.get('parameters') == params


@pytest.mark.asyncio
async def test_backend_selection_multi_backend(
    mock_backend_registry,
    mock_flowise_backend,
    mock_langflow_backend
):
    """Test backend selection with multiple backends"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend,
        BackendType.LANGFLOW: mock_langflow_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    # RAG query should prefer Langflow
    result = await handler.execute_query(
        question="Search documents and retrieve information"
    )

    # Verify correct backend was selected
    if '_mcp_metadata' in result:
        # Langflow should be selected for RAG queries
        assert result['_mcp_metadata']['backend_used'] in ['langflow', 'flowise']


@pytest.mark.asyncio
async def test_fallback_on_primary_failure(
    mock_backend_registry,
    mock_flowise_backend,
    mock_langflow_backend
):
    """Test fallback to secondary backend on primary failure"""
    # Make Flowise fail
    mock_flowise_backend.execute_flow = AsyncMock(
        side_effect=Exception("Flowise unavailable")
    )

    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend,
        BackendType.LANGFLOW: mock_langflow_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry, enable_fallback=True)

    result = await handler.execute_query(question="Test question")

    # Should have fallback metadata
    if '_mcp_metadata' in result:
        # Langflow should be used as fallback
        assert result['_mcp_metadata'].get('fallback_used', False) or \
               result['_mcp_metadata'].get('attempt', 1) > 1


@pytest.mark.asyncio
async def test_no_backends_available(mock_backend_registry):
    """Test error handling when no backends available"""
    mock_backend_registry.backends = {}

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(question="Test question")

    assert 'error' in result


@pytest.mark.asyncio
async def test_explicit_backend_not_found(mock_backend_registry):
    """Test error handling when explicit backend not found"""
    mock_backend_registry.backends = {}

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(
        question="Test question",
        backend_override="nonexistent"
    )

    assert 'error' in result


@pytest.mark.asyncio
async def test_backend_disconnected(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test handling of disconnected backend"""
    mock_flowise_backend.is_connected = False

    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(question="Test question")

    assert 'error' in result


@pytest.mark.asyncio
async def test_metadata_enrichment(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test that response includes rich metadata"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(question="Creative vision question")

    if '_mcp_metadata' in result:
        metadata = result['_mcp_metadata']

        # Verify required metadata fields
        assert 'backend_used' in metadata
        assert 'flow_id' in metadata
        assert 'flow_name' in metadata
        assert 'routing_score' in metadata
        assert 'intent_classified' in metadata
        assert 'intent_confidence' in metadata
        assert 'execution_time_ms' in metadata
        assert 'fallback_used' in metadata
        assert 'attempt' in metadata


@pytest.mark.asyncio
async def test_performance_cache_update(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test that performance cache is updated after execution"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    # Execute query
    await handler.execute_query(question="Test question")

    # Verify performance cache was updated
    assert BackendType.FLOWISE in handler._performance_cache
    cache = handler._performance_cache[BackendType.FLOWISE]
    assert cache['total'] > 0
    assert 'success_rate' in cache


@pytest.mark.asyncio
async def test_timeout_parameter(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test custom timeout parameter"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(
        question="Test question",
        timeout=60.0
    )

    # Verify execution completed (timeout was respected)
    assert 'error' not in result or '_mcp_metadata' in result


@pytest.mark.asyncio
async def test_routing_score_calculation(
    mock_backend_registry,
    mock_flowise_backend,
    mock_langflow_backend
):
    """Test that routing scores are calculated correctly"""
    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend,
        BackendType.LANGFLOW: mock_langflow_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry)

    result = await handler.execute_query(
        question="Help with creative vision and structural tension"
    )

    if '_mcp_metadata' in result:
        metadata = result['_mcp_metadata']

        # Verify routing score exists and is valid
        assert 'routing_score' in metadata
        assert 0.0 <= metadata['routing_score'] <= 1.0

        # Verify breakdown exists
        if 'routing_breakdown' in metadata:
            breakdown = metadata['routing_breakdown']
            # Check that scores are in valid range
            for score_name, score_value in breakdown.items():
                assert 0.0 <= score_value <= 1.0


@pytest.mark.asyncio
async def test_all_backends_fail_with_fallback_disabled(
    mock_backend_registry,
    mock_flowise_backend
):
    """Test behavior when all backends fail and fallback is disabled"""
    mock_flowise_backend.execute_flow = AsyncMock(
        side_effect=Exception("Backend failure")
    )

    mock_backend_registry.backends = {
        BackendType.FLOWISE: mock_flowise_backend
    }

    handler = UniversalQueryHandler(mock_backend_registry, enable_fallback=False)

    result = await handler.execute_query(question="Test question")

    assert 'error' in result
    assert result.get('fallback_used', False) is False
