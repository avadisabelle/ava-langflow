#!/usr/bin/env python3
"""
Tests for Universal Query MCP Tool and Routing Logic
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
from unittest.mock import AsyncMock, Mock, patch

from agentic_flywheel.routing.router import (
    UniversalRouter,
    PerformanceTracker,
    BackendScore,
    classify_intent,
    extract_keywords
)
from agentic_flywheel.backends.base import FlowBackend, BackendType, UniversalFlow
from agentic_flywheel.tools.universal_query import (
    handle_universal_query,
    format_universal_response
)


# Test Fixtures

@pytest.fixture
def mock_flowise_backend():
    """Create mock Flowise backend"""
    backend = Mock(spec=FlowBackend)
    backend.backend_type = BackendType.FLOWISE
    backend.health_check = AsyncMock(return_value=True)
    backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="flowise_flow1",
            name="Creative Orientation",
            description="Structural tension guidance",
            backend=BackendType.FLOWISE,
            backend_specific_id="flow1",
            intent_keywords=["creative-orientation", "creative", "goal"],
            capabilities=[],
            input_types=[],
            output_types=[]
        ),
        UniversalFlow(
            id="flowise_flow2",
            name="Technical Analysis",
            description="Code analysis",
            backend=BackendType.FLOWISE,
            backend_specific_id="flow2",
            intent_keywords=["technical-analysis", "code", "debug"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ])
    backend.execute_flow = AsyncMock(return_value={
        "result": "Structural tension is the gap between current reality and desired outcome."
    })
    return backend


@pytest.fixture
def mock_langflow_backend():
    """Create mock Langflow backend"""
    backend = Mock(spec=FlowBackend)
    backend.backend_type = BackendType.LANGFLOW
    backend.health_check = AsyncMock(return_value=True)
    backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="langflow_flow1",
            name="Document QA",
            description="Document search",
            backend=BackendType.LANGFLOW,
            backend_specific_id="flow1",
            intent_keywords=["document-qa", "search", "find"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ])
    backend.execute_flow = AsyncMock(return_value={
        "result": "Here is the document information you requested."
    })
    return backend


# Intent Classification Tests

def test_classify_intent_creative():
    """Test intent classification for creative queries"""
    question = "What is structural tension and how do I create desired outcomes?"
    intent = classify_intent(question)
    assert intent == "creative-orientation"


def test_classify_intent_technical():
    """Test intent classification for technical queries"""
    question = "How do I debug this error in my code?"
    intent = classify_intent(question)
    assert intent == "technical-analysis"


def test_classify_intent_document():
    """Test intent classification for document queries"""
    question = "Find information about the project documentation"
    intent = classify_intent(question)
    assert intent == "document-qa"


def test_classify_intent_fallback():
    """Test intent classification fallback for unrecognized queries"""
    question = "Some random question without specific keywords"
    intent = classify_intent(question)
    assert intent == "general"


def test_extract_keywords():
    """Test keyword extraction from questions"""
    question = "What is structural tension in the creative orientation framework?"
    keywords = extract_keywords(question)

    assert "structural" in keywords
    assert "tension" in keywords
    assert "creative" in keywords
    assert "orientation" in keywords
    assert "framework" in keywords
    # Stop words should be filtered
    assert "what" not in keywords
    assert "the" not in keywords


# Performance Tracker Tests

def test_performance_tracker_record():
    """Test performance tracking records execution"""
    tracker = PerformanceTracker(max_history=5)

    tracker.record("flowise", "creative-orientation", 1000.0, True)
    tracker.record("flowise", "creative-orientation", 1200.0, True)
    tracker.record("flowise", "creative-orientation", 2000.0, False)

    score = tracker.get_score("flowise", "creative-orientation")

    # Should have recorded data and calculated a score
    assert 0.0 <= score <= 1.0
    # Success rate is 2/3, should influence score positively
    assert score > 0.4


def test_performance_tracker_no_history():
    """Test performance tracker with no history returns neutral score"""
    tracker = PerformanceTracker()

    score = tracker.get_score("flowise", "unknown-intent")

    # No history should return 0.5 (neutral)
    assert score == 0.5


def test_performance_tracker_max_history():
    """Test performance tracker respects max history limit"""
    tracker = PerformanceTracker(max_history=3)

    # Record 5 entries
    for i in range(5):
        tracker.record("backend", "intent", 1000.0, True)

    # Should only keep last 3
    history = tracker._history["backend:intent"]
    assert len(history) == 3


# Router Tests

@pytest.mark.asyncio
async def test_router_match_score_calculation():
    """Test flow match score calculation"""
    router = UniversalRouter()

    flows = [
        UniversalFlow(
            id="flow1",
            name="Test Flow",
            description="Test",
            backend=BackendType.FLOWISE,
            backend_specific_id="f1",
            intent_keywords=["creative-orientation", "goal", "vision"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ]

    score, matching, best = router._calculate_match_score(flows, "creative-orientation")

    assert score > 0.5  # Should have positive match
    assert len(matching) == 1
    assert best.id == "flow1"


@pytest.mark.asyncio
async def test_router_match_score_no_match():
    """Test match score when no flows match intent"""
    router = UniversalRouter()

    flows = [
        UniversalFlow(
            id="flow1",
            name="Test Flow",
            description="Test",
            backend=BackendType.FLOWISE,
            backend_specific_id="f1",
            intent_keywords=["other-intent"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ]

    score, matching, best = router._calculate_match_score(flows, "creative-orientation")

    assert score == 0.0
    assert len(matching) == 0
    assert best is None


@pytest.mark.asyncio
async def test_router_select_backend_intelligent(mock_flowise_backend, mock_langflow_backend):
    """Test intelligent backend selection"""
    router = UniversalRouter()

    backends = [mock_flowise_backend, mock_langflow_backend]
    question = "What is structural tension?"

    decision = await router.select_backend(backends, question, intent="creative-orientation")

    # Should select Flowise (has creative-orientation flow)
    assert decision.backend.backend_type == BackendType.FLOWISE
    assert decision.method == "intelligent"
    assert decision.score > 0.0
    assert decision.intent == "creative-orientation"


@pytest.mark.asyncio
async def test_router_select_backend_explicit(mock_flowise_backend, mock_langflow_backend):
    """Test explicit backend selection"""
    router = UniversalRouter()

    backends = [mock_flowise_backend, mock_langflow_backend]
    question = "Find documents"

    decision = await router.select_backend(
        backends,
        question,
        intent="document-qa",
        backend_override="langflow"
    )

    # Should select Langflow explicitly
    assert decision.backend.backend_type == BackendType.LANGFLOW
    assert decision.method == "explicit"
    assert decision.score == 1.0


@pytest.mark.asyncio
async def test_router_select_backend_no_backends():
    """Test router handles no available backends"""
    router = UniversalRouter()

    with pytest.raises(ValueError, match="No backends available"):
        await router.select_backend([], "test question")


@pytest.mark.asyncio
async def test_router_select_backend_no_matching_flows(mock_flowise_backend):
    """Test router handles no matching flows for intent"""
    router = UniversalRouter()

    # Mock backend with no matching flows
    mock_flowise_backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="flow1",
            name="Other Flow",
            description="Test",
            backend=BackendType.FLOWISE,
            backend_specific_id="f1",
            intent_keywords=["other-intent"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ])

    with pytest.raises(ValueError, match="No backends have flows matching intent"):
        await router.select_backend([mock_flowise_backend], "test", intent="creative-orientation")


@pytest.mark.asyncio
async def test_router_health_check_influences_selection(mock_flowise_backend, mock_langflow_backend):
    """Test that backend health affects selection"""
    router = UniversalRouter()

    # Make Flowise unhealthy
    mock_flowise_backend.health_check = AsyncMock(return_value=False)

    # Both have creative-orientation, but only Langflow is healthy
    mock_langflow_backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="langflow_flow",
            name="Creative Flow",
            description="Test",
            backend=BackendType.LANGFLOW,
            backend_specific_id="f1",
            intent_keywords=["creative-orientation"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ])

    backends = [mock_flowise_backend, mock_langflow_backend]
    decision = await router.select_backend(backends, "creative question", intent="creative-orientation")

    # Should select healthy Langflow over unhealthy Flowise
    assert decision.backend.backend_type == BackendType.LANGFLOW


# Universal Query Handler Tests

@pytest.mark.asyncio
async def test_handle_universal_query_success(mock_flowise_backend):
    """Test successful universal query execution"""
    with patch('agentic_flywheel.tools.universal_query.BackendRegistry') as mock_registry_class:
        # Setup mock registry
        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend])
        mock_registry_class.return_value = mock_registry

        arguments = {
            "question": "What is structural tension?",
            "backend": "auto",
            "include_routing_metadata": True
        }

        result = await handle_universal_query("universal_query", arguments)

        assert len(result) == 1
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        assert "Structural tension" in response_text
        assert "Routing Info" in response_text  # Metadata included


@pytest.mark.asyncio
async def test_handle_universal_query_missing_question():
    """Test universal query with missing question parameter"""
    result = await handle_universal_query("universal_query", {})

    assert len(result) == 1
    response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
    assert "Error" in response_text
    assert "question" in response_text


@pytest.mark.asyncio
async def test_handle_universal_query_no_healthy_backends(mock_flowise_backend):
    """Test universal query when no backends are healthy"""
    # Make backend unhealthy
    mock_flowise_backend.health_check = AsyncMock(return_value=False)

    with patch('agentic_flywheel.tools.universal_query.BackendRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend])
        mock_registry_class.return_value = mock_registry

        arguments = {"question": "Test question"}

        result = await handle_universal_query("universal_query", arguments)

        assert len(result) == 1
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        assert "No healthy backends" in response_text


@pytest.mark.asyncio
async def test_handle_universal_query_with_fallback(mock_flowise_backend, mock_langflow_backend):
    """Test universal query fallback when primary backend fails"""
    # Make Flowise fail on execution
    mock_flowise_backend.execute_flow = AsyncMock(side_effect=Exception("Flowise error"))

    # Langflow should work
    mock_langflow_backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="langflow_creative",
            name="Creative Flow",
            description="Fallback flow",
            backend=BackendType.LANGFLOW,
            backend_specific_id="f1",
            intent_keywords=["creative-orientation"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ])

    with patch('agentic_flywheel.tools.universal_query.BackendRegistry') as mock_registry_class:
        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend, mock_langflow_backend])
        mock_registry_class.return_value = mock_registry

        arguments = {
            "question": "What is structural tension?",
            "backend": "auto"
        }

        result = await handle_universal_query("universal_query", arguments)

        assert len(result) == 1
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text

        # Should show fallback was used
        assert "Fallback" in response_text or "langflow" in response_text.lower()


# Response Formatting Tests

def test_format_universal_response_with_metadata():
    """Test response formatting with metadata"""
    mock_decision = Mock()
    mock_decision.method = "intelligent"
    mock_decision.score = 0.92
    mock_decision.intent = "creative-orientation"
    mock_decision.all_scores = []

    result = {"result": "Test response"}

    formatted = format_universal_response(
        result=result,
        backend="flowise",
        flow_name="Creative Orientation",
        routing_decision=mock_decision,
        duration_ms=1234.5,
        include_metadata=True
    )

    assert "Test response" in formatted
    assert "Backend: flowise" in formatted
    assert "Flow: Creative Orientation" in formatted
    assert "Intelligent" in formatted
    assert "0.92" in formatted
    assert "1235ms" in formatted


def test_format_universal_response_without_metadata():
    """Test response formatting without metadata"""
    mock_decision = Mock()
    mock_decision.method = "intelligent"

    result = {"result": "Test response"}

    formatted = format_universal_response(
        result=result,
        backend="flowise",
        flow_name="Creative Orientation",
        routing_decision=mock_decision,
        duration_ms=1234.5,
        include_metadata=False
    )

    # Should only contain the response, no metadata
    assert formatted == "Test response"


def test_format_universal_response_fallback():
    """Test response formatting for fallback execution"""
    mock_decision = Mock()
    mock_decision.method = "intelligent"
    mock_decision.score = 0.85
    mock_decision.intent = "creative-orientation"
    mock_decision.all_scores = []

    result = {"result": "Fallback response"}

    formatted = format_universal_response(
        result=result,
        backend="langflow",
        flow_name="Creative Flow",
        routing_decision=mock_decision,
        duration_ms=2000.0,
        include_metadata=True,
        is_fallback=True,
        primary_backend="flowise",
        primary_error="Connection timeout"
    )

    assert "Fallback response" in formatted
    assert "Fallback: flowise → langflow" in formatted
    assert "Primary Error: Connection timeout" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
