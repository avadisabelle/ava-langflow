#!/usr/bin/env python3
"""
Tests for Backend Management MCP Tools
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
import json
from unittest.mock import AsyncMock, Mock, patch

from agentic_flywheel.backends.base import BackendType, UniversalFlow, FlowBackend
from agentic_flywheel.tools.backend_tools import (
    handle_backend_registry_status,
    handle_backend_discover,
    handle_backend_connect,
    handle_backend_list_flows,
    handle_backend_execute_universal,
    handle_backend_performance_compare
)


# Test Fixtures

@pytest.fixture
def mock_flowise_backend():
    """Create mock Flowise backend"""
    backend = Mock(spec=FlowBackend)
    backend.backend_type = BackendType.FLOWISE
    backend.base_url = "http://localhost:3000"
    backend.health_check = AsyncMock(return_value=True)
    backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="flow1",
            name="Creative Orientation",
            description="Structural tension guidance",
            backend=BackendType.FLOWISE,
            backend_specific_id="csv2507",
            intent_keywords=["creative", "goal"],
            capabilities=[],
            input_types=[],
            output_types=[]
        ),
        UniversalFlow(
            id="flow2",
            name="Technical Analysis",
            description="Code analysis",
            backend=BackendType.FLOWISE,
            backend_specific_id="tech001",
            intent_keywords=["technical", "code"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ])
    backend.execute_flow = AsyncMock(return_value={"result": "Test response"})
    return backend


@pytest.fixture
def mock_langflow_backend():
    """Create mock Langflow backend"""
    backend = Mock(spec=FlowBackend)
    backend.backend_type = BackendType.LANGFLOW
    backend.base_url = "http://localhost:7860"
    backend.health_check = AsyncMock(return_value=True)
    backend.discover_flows = AsyncMock(return_value=[
        UniversalFlow(
            id="langflow1",
            name="Document QA",
            description="Document search",
            backend=BackendType.LANGFLOW,
            backend_specific_id="doc_qa_001",
            intent_keywords=["document", "search"],
            capabilities=[],
            input_types=[],
            output_types=[]
        )
    ])
    backend.execute_flow = AsyncMock(return_value={"result": "Document found"})
    return backend


# Backend Registry Status Tests

@pytest.mark.asyncio
async def test_backend_registry_status_success(mock_flowise_backend, mock_langflow_backend):
    """Test successful registry status retrieval"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry, \
         patch('agentic_flywheel.tools.backend_tools.get_router') as mock_get_router:

        # Mock registry
        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend, mock_langflow_backend])
        mock_get_registry.return_value = mock_registry

        # Mock router with empty performance data
        mock_router = Mock()
        mock_router.performance_tracker = Mock()
        mock_router.performance_tracker._history = {}
        mock_get_router.return_value = mock_router

        result = await handle_backend_registry_status("backend_registry_status", {})

        assert len(result) == 1
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["total_backends"] == 2
        assert data["healthy_count"] == 2
        assert data["unhealthy_count"] == 0
        assert len(data["backends"]) == 2
        assert data["summary"]["recommendation"] == "All backends healthy"


@pytest.mark.asyncio
async def test_backend_registry_status_partial_failure(mock_flowise_backend, mock_langflow_backend):
    """Test registry status with one backend offline"""
    # Make Langflow unhealthy
    mock_langflow_backend.health_check = AsyncMock(return_value=False)

    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry, \
         patch('agentic_flywheel.tools.backend_tools.get_router') as mock_get_router:

        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend, mock_langflow_backend])
        mock_get_registry.return_value = mock_registry

        mock_router = Mock()
        mock_router.performance_tracker = Mock()
        mock_router.performance_tracker._history = {}
        mock_get_router.return_value = mock_router

        result = await handle_backend_registry_status("backend_registry_status", {})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["healthy_count"] == 1
        assert data["unhealthy_count"] == 1
        assert "1 backend(s) offline" in data["summary"]["recommendation"]


# Backend Discover Tests

@pytest.mark.asyncio
async def test_backend_discover_success(mock_flowise_backend):
    """Test successful backend discovery"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend])
        mock_get_registry.return_value = mock_registry

        result = await handle_backend_discover("backend_discover", {})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["discovered"] == 1
        assert data["registered"] == 1
        assert len(data["backends"]) == 1
        assert data["backends"][0]["type"] == "flowise"


@pytest.mark.asyncio
async def test_backend_discover_with_errors():
    """Test backend discovery with connection errors"""
    failing_backend = Mock(spec=FlowBackend)
    failing_backend.backend_type = BackendType.FLOWISE
    failing_backend.base_url = "http://invalid:9999"
    failing_backend.health_check = AsyncMock(side_effect=Exception("Connection refused"))

    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry:
        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[failing_backend])
        mock_get_registry.return_value = mock_registry

        result = await handle_backend_discover("backend_discover", {})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert len(data["errors"]) > 0


# Backend Connect Tests

@pytest.mark.asyncio
async def test_backend_connect_flowise_success():
    """Test successful Flowise backend connection"""
    with patch('agentic_flywheel.tools.backend_tools.FlowiseBackend') as mock_flowise_class, \
         patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry:

        # Mock backend instance
        mock_backend = Mock()
        mock_backend.health_check = AsyncMock(return_value=True)
        mock_backend.discover_flows = AsyncMock(return_value=[Mock(), Mock()])
        mock_flowise_class.return_value = mock_backend

        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        arguments = {
            "backend_type": "flowise",
            "base_url": "http://localhost:3000",
            "api_key": "test_key",
            "name": "Test Flowise"
        }

        result = await handle_backend_connect("backend_connect", arguments)

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["success"] is True
        assert data["backend"]["type"] == "flowise"
        assert data["backend"]["flows_discovered"] == 2


@pytest.mark.asyncio
async def test_backend_connect_missing_params():
    """Test backend connect with missing parameters"""
    result = await handle_backend_connect("backend_connect", {})

    response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
    assert "required" in response_text.lower()


@pytest.mark.asyncio
async def test_backend_connect_unsupported_type():
    """Test backend connect with unsupported backend type"""
    arguments = {
        "backend_type": "unsupported",
        "base_url": "http://localhost:3000"
    }

    result = await handle_backend_connect("backend_connect", arguments)

    response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
    assert "Unsupported backend type" in response_text


# Backend List Flows Tests

@pytest.mark.asyncio
async def test_backend_list_flows_all(mock_flowise_backend, mock_langflow_backend):
    """Test listing all flows from all backends"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry, \
         patch('agentic_flywheel.tools.backend_tools.get_router') as mock_get_router:

        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend, mock_langflow_backend])
        mock_get_registry.return_value = mock_registry

        mock_router = Mock()
        mock_router.performance_tracker = Mock()
        mock_router.performance_tracker._history = {}
        mock_router.performance_tracker.get_score = Mock(return_value=0.75)
        mock_get_router.return_value = mock_router

        result = await handle_backend_list_flows("backend_list_flows", {"backend_filter": "all"})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["total_flows"] == 3  # 2 from flowise + 1 from langflow
        assert len(data["flows"]) == 3
        assert data["summary"]["by_backend"]["flowise"] == 2
        assert data["summary"]["by_backend"]["langflow"] == 1


@pytest.mark.asyncio
async def test_backend_list_flows_filtered_by_backend(mock_flowise_backend, mock_langflow_backend):
    """Test listing flows filtered by backend type"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry, \
         patch('agentic_flywheel.tools.backend_tools.get_router') as mock_get_router:

        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend, mock_langflow_backend])
        mock_get_registry.return_value = mock_registry

        mock_router = Mock()
        mock_router.performance_tracker = Mock()
        mock_router.performance_tracker._history = {}
        mock_router.performance_tracker.get_score = Mock(return_value=0.75)
        mock_get_router.return_value = mock_router

        result = await handle_backend_list_flows("backend_list_flows", {"backend_filter": "flowise"})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["total_flows"] == 2  # Only flowise flows
        assert all(flow["backend"] == "flowise" for flow in data["flows"])


@pytest.mark.asyncio
async def test_backend_list_flows_intent_filter(mock_flowise_backend):
    """Test listing flows with intent keyword filter"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry, \
         patch('agentic_flywheel.tools.backend_tools.get_router') as mock_get_router:

        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend])
        mock_get_registry.return_value = mock_registry

        mock_router = Mock()
        mock_router.performance_tracker = Mock()
        mock_router.performance_tracker._history = {}
        mock_router.performance_tracker.get_score = Mock(return_value=0.75)
        mock_get_router.return_value = mock_router

        result = await handle_backend_list_flows(
            "backend_list_flows",
            {"intent_filter": "creative"}
        )

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        # Should only return flows with "creative" keyword
        assert all("creative" in flow["intent_keywords"] for flow in data["flows"])


# Backend Execute Universal Tests

@pytest.mark.asyncio
async def test_backend_execute_universal_success(mock_flowise_backend):
    """Test successful universal execution"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry, \
         patch('agentic_flywheel.tools.backend_tools.get_router') as mock_get_router:

        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend])
        mock_get_registry.return_value = mock_registry

        mock_router = Mock()
        mock_router.performance_tracker = Mock()
        mock_router.performance_tracker.record = Mock()
        mock_get_router.return_value = mock_router

        arguments = {
            "flow_id": "csv2507",
            "input_data": {"question": "What is structural tension?"}
        }

        result = await handle_backend_execute_universal("backend_execute_universal", arguments)

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["flow_id"] == "csv2507"
        assert data["backend_used"] == "flowise"
        assert "result" in data
        assert data["metadata"]["fallback_used"] is False


@pytest.mark.asyncio
async def test_backend_execute_universal_flow_not_found():
    """Test execution with non-existent flow"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry:
        mock_backend = Mock()
        mock_backend.health_check = AsyncMock(return_value=True)
        mock_backend.discover_flows = AsyncMock(return_value=[])

        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_backend])
        mock_get_registry.return_value = mock_registry

        arguments = {
            "flow_id": "nonexistent",
            "input_data": {}
        }

        result = await handle_backend_execute_universal("backend_execute_universal", arguments)

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        assert "not found" in response_text.lower()


@pytest.mark.asyncio
async def test_backend_execute_universal_missing_flow_id():
    """Test execution with missing flow_id"""
    result = await handle_backend_execute_universal("backend_execute_universal", {"input_data": {}})

    response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
    assert "required" in response_text.lower()


# Backend Performance Compare Tests

@pytest.mark.asyncio
async def test_backend_performance_compare_latency(mock_flowise_backend, mock_langflow_backend):
    """Test performance comparison by latency"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry, \
         patch('agentic_flywheel.tools.backend_tools.get_router') as mock_get_router:

        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_flowise_backend, mock_langflow_backend])
        mock_get_registry.return_value = mock_registry

        # Mock performance history
        mock_router = Mock()
        mock_router.performance_tracker = Mock()
        mock_router.performance_tracker._history = {
            "flowise:flow1": [
                {"latency_ms": 1200, "success": True},
                {"latency_ms": 1300, "success": True},
                {"latency_ms": 1100, "success": True}
            ],
            "langflow:langflow1": [
                {"latency_ms": 900, "success": True},
                {"latency_ms": 1000, "success": True},
                {"latency_ms": 950, "success": True}
            ]
        }
        mock_get_router.return_value = mock_router

        result = await handle_backend_performance_compare(
            "backend_performance_compare",
            {"metric": "latency", "time_range": "24h"}
        )

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["metric"] == "latency"
        assert len(data["comparison"]) == 2
        assert data["winner"] is not None
        assert "recommendation" in data


@pytest.mark.asyncio
async def test_backend_performance_compare_no_data():
    """Test performance comparison with no historical data"""
    with patch('agentic_flywheel.tools.backend_tools.get_registry') as mock_get_registry, \
         patch('agentic_flywheel.tools.backend_tools.get_router') as mock_get_router:

        mock_backend = Mock()
        mock_backend.backend_type = BackendType.FLOWISE

        mock_registry = Mock()
        mock_registry.discover_backends = AsyncMock()
        mock_registry.get_all_backends = Mock(return_value=[mock_backend])
        mock_get_registry.return_value = mock_registry

        mock_router = Mock()
        mock_router.performance_tracker = Mock()
        mock_router.performance_tracker._history = {}
        mock_get_router.return_value = mock_router

        result = await handle_backend_performance_compare("backend_performance_compare", {})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert len(data["comparison"]) == 0
        assert "Insufficient data" in data["recommendation"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
