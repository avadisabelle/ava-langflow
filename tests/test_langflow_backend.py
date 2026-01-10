#!/usr/bin/env python3
"""
Tests for the Langflow Backend Adapter.
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
import httpx
from unittest.mock import AsyncMock

from agentic_flywheel.backends.langflow.langflow_backend import LangflowBackend

BASE_URL = "http://fake-langflow-host.com"
API_KEY = "fake-api-key"


@pytest.fixture
def backend():
    """Provides a LangflowBackend instance for testing."""
    return LangflowBackend(base_url=BASE_URL, api_key=API_KEY)


@pytest.mark.asyncio
async def test_connect_and_health_check_success(backend: LangflowBackend, mocker):
    """
    Tests successful connection and health check.
    """
    mock_request = httpx.Request("GET", "/api/v1/flows")
    mock_response = httpx.Response(200, json=[], request=mock_request)
    mock_get = AsyncMock(return_value=mock_response)

    mocker.patch(
        "httpx.AsyncClient.get",
        mock_get
    )

    connected = await backend.connect()

    assert connected is True
    assert backend.is_connected is True
    mock_get.assert_called_once_with("/api/v1/flows")
    await backend.disconnect()
    assert backend.is_connected is False


@pytest.mark.asyncio
async def test_health_check_failure_on_request_error(backend: LangflowBackend, mocker):
    """
    Tests that the health check fails gracefully on an HTTP request error.
    """
    mock_get = AsyncMock(side_effect=httpx.RequestError("Test Error", request=None))
    mocker.patch(
        "httpx.AsyncClient.get",
        mock_get
    )
    
    # We need to manually create the client to test health_check in isolation
    backend._client = httpx.AsyncClient(base_url=BASE_URL)
    
    healthy = await backend.health_check()

    assert healthy is False


@pytest.mark.asyncio
async def test_health_check_failure_on_bad_status(backend: LangflowBackend, mocker):
    """

    Tests that the health check fails gracefully on a non-2xx HTTP status.
    """
    mock_request = httpx.Request("GET", "/api/v1/flows")
    mock_response = httpx.Response(500, request=mock_request)
    mock_get = AsyncMock(return_value=mock_response)
    mocker.patch(
        "httpx.AsyncClient.get",
        mock_get
    )

    # We need to manually create the client to test health_check in isolation
    backend._client = httpx.AsyncClient(base_url=BASE_URL)

    healthy = await backend.health_check()

    assert healthy is False


@pytest.mark.asyncio
async def test_discover_flows_success(backend: LangflowBackend, mocker):
    """
    Tests successful discovery of flows from the backend.
    """
    mock_flows_data = [
        {"id": "flow1", "name": "Test Flow 1", "description": "First test flow"},
        {"id": "flow2", "name": "Test Flow 2", "description": "Second test flow"}
    ]
    mock_request = httpx.Request("GET", "/api/v1/flows")
    mock_response = httpx.Response(200, json=mock_flows_data, request=mock_request)
    mock_get = AsyncMock(return_value=mock_response)

    mocker.patch("httpx.AsyncClient.get", mock_get)

    await backend.connect()
    flows = await backend.discover_flows()

    assert len(flows) == 2
    assert flows[0].name == "Test Flow 1"
    assert flows[1].name == "Test Flow 2"
    assert flows[0].backend.value == "langflow"
    await backend.disconnect()


@pytest.mark.asyncio
async def test_discover_flows_not_connected(backend: LangflowBackend):
    """
    Tests that discover_flows returns empty list when not connected.
    """
    flows = await backend.discover_flows()
    assert flows == []


@pytest.mark.asyncio
async def test_discover_flows_request_error(backend: LangflowBackend, mocker):
    """
    Tests that discover_flows handles request errors gracefully.
    """
    mock_get = AsyncMock(side_effect=httpx.RequestError("Network error", request=None))
    mocker.patch("httpx.AsyncClient.get", mock_get)

    await backend.connect()
    flows = await backend.discover_flows()

    assert flows == []
    await backend.disconnect()


@pytest.mark.asyncio
async def test_get_flow_success(backend: LangflowBackend, mocker):
    """
    Tests successful retrieval of a specific flow.
    """
    mock_flow_data = {"id": "flow1", "name": "Test Flow", "description": "A test flow"}

    # Mock both the connection request and the get_flow request
    mock_request1 = httpx.Request("GET", "/api/v1/flows")
    mock_request2 = httpx.Request("GET", "/api/v1/flows/flow1")
    responses = [
        httpx.Response(200, json=[], request=mock_request1),  # For connect
        httpx.Response(200, json=mock_flow_data, request=mock_request2)  # For get_flow
    ]
    mock_get = AsyncMock(side_effect=responses)
    mocker.patch("httpx.AsyncClient.get", mock_get)

    await backend.connect()
    flow = await backend.get_flow("flow1")

    assert flow is not None
    assert flow.name == "Test Flow"
    assert flow.backend_specific_id == "flow1"
    await backend.disconnect()


@pytest.mark.asyncio
async def test_get_flow_not_found(backend: LangflowBackend, mocker):
    """
    Tests that get_flow returns None for non-existent flow.
    """
    mock_request1 = httpx.Request("GET", "/api/v1/flows")
    mock_request2 = httpx.Request("GET", "/api/v1/flows/nonexistent")
    responses = [
        httpx.Response(200, json=[], request=mock_request1),  # For connect
        httpx.Response(404, request=mock_request2)  # For get_flow
    ]
    mock_get = AsyncMock(side_effect=responses)
    mocker.patch("httpx.AsyncClient.get", mock_get)

    await backend.connect()
    flow = await backend.get_flow("nonexistent")

    assert flow is None
    await backend.disconnect()


@pytest.mark.asyncio
async def test_execute_flow_success(backend: LangflowBackend, mocker):
    """
    Tests successful flow execution.
    """
    mock_execution_result = {
        "outputs": {"output": "Flow execution result"},
        "status": "success"
    }

    mock_request_get = httpx.Request("GET", "/api/v1/flows")
    mock_request_post = httpx.Request("POST", "/api/v1/run/flow1")
    mock_get = AsyncMock(return_value=httpx.Response(200, json=[], request=mock_request_get))
    mock_post = AsyncMock(return_value=httpx.Response(200, json=mock_execution_result, request=mock_request_post))

    mocker.patch("httpx.AsyncClient.get", mock_get)
    mocker.patch("httpx.AsyncClient.post", mock_post)

    await backend.connect()
    result = await backend.execute_flow("flow1", "test input", {"param1": "value1"})

    assert "result" in result
    assert "raw" in result
    assert result["raw"] == mock_execution_result
    await backend.disconnect()


@pytest.mark.asyncio
async def test_execute_flow_not_connected(backend: LangflowBackend):
    """
    Tests that execute_flow returns error when not connected.
    """
    result = await backend.execute_flow("flow1", "test input")

    assert "error" in result
    assert result["error"] == "Backend is not connected."


@pytest.mark.asyncio
async def test_execute_flow_request_error(backend: LangflowBackend, mocker):
    """
    Tests that execute_flow handles request errors gracefully.
    """
    mock_request_get = httpx.Request("GET", "/api/v1/flows")
    mock_get = AsyncMock(return_value=httpx.Response(200, json=[], request=mock_request_get))
    mock_post = AsyncMock(side_effect=httpx.RequestError("Network error", request=None))

    mocker.patch("httpx.AsyncClient.get", mock_get)
    mocker.patch("httpx.AsyncClient.post", mock_post)

    await backend.connect()
    result = await backend.execute_flow("flow1", "test input")

    assert "error" in result
    await backend.disconnect()


@pytest.mark.asyncio
async def test_stream_flow(backend: LangflowBackend, mocker):
    """
    Tests stream_flow method (currently a wrapper around execute_flow).
    """
    mock_execution_result = {"outputs": {"output": "Streaming result"}}

    mock_request_get = httpx.Request("GET", "/api/v1/flows")
    mock_request_post = httpx.Request("POST", "/api/v1/run/flow1")
    mock_get = AsyncMock(return_value=httpx.Response(200, json=[], request=mock_request_get))
    mock_post = AsyncMock(return_value=httpx.Response(200, json=mock_execution_result, request=mock_request_post))

    mocker.patch("httpx.AsyncClient.get", mock_get)
    mocker.patch("httpx.AsyncClient.post", mock_post)

    await backend.connect()

    results = []
    async for chunk in backend.stream_flow("flow1", "test input"):
        results.append(chunk)

    assert len(results) == 1
    assert "result" in results[0]
    await backend.disconnect()


@pytest.mark.asyncio
async def test_create_session(backend: LangflowBackend):
    """
    Tests session creation (returns mock session for stateless backend).
    """
    session = await backend.create_session("flow1")

    assert session is not None
    assert session.current_flow_id == "flow1"
    assert session.backend.value == "langflow"
    assert "langflow_session_" in session.id


@pytest.mark.asyncio
async def test_get_session(backend: LangflowBackend):
    """
    Tests session retrieval (returns None for stateless backend).
    """
    session = await backend.get_session("any_session_id")
    assert session is None


@pytest.mark.asyncio
async def test_update_session(backend: LangflowBackend):
    """
    Tests session update (returns mock session for stateless backend).
    """
    session = await backend.update_session("session_id", {"current_flow_id": "flow2"})

    assert session is not None
    assert session.current_flow_id == "flow2"


@pytest.mark.asyncio
async def test_delete_session(backend: LangflowBackend):
    """
    Tests session deletion (always returns True for stateless backend).
    """
    result = await backend.delete_session("any_session_id")
    assert result is True


@pytest.mark.asyncio
async def test_list_sessions(backend: LangflowBackend):
    """
    Tests session listing (returns empty list for stateless backend).
    """
    sessions = await backend.list_sessions()
    assert sessions == []


@pytest.mark.asyncio
async def test_get_performance_metrics(backend: LangflowBackend):
    """
    Tests performance metrics retrieval.
    """
    metrics = await backend.get_performance_metrics("flow1")

    assert metrics is not None
    assert metrics.backend.value == "langflow"
    assert metrics.flow_id == "flow1"


@pytest.mark.asyncio
async def test_get_system_metrics(backend: LangflowBackend):
    """
    Tests system metrics retrieval.
    """
    metrics = await backend.get_system_metrics()
    assert metrics == {}


@pytest.mark.asyncio
async def test_analyze_usage_patterns(backend: LangflowBackend):
    """
    Tests usage pattern analysis.
    """
    patterns = await backend.analyze_usage_patterns("flow1")
    assert patterns == {}


@pytest.mark.asyncio
async def test_validate_parameters(backend: LangflowBackend):
    """
    Tests parameter validation.
    """
    params = {"param1": "value1", "param2": 123}
    result = await backend.validate_parameters("flow1", params)

    assert result["validated"] is True
    assert result["parameters"] == params


@pytest.mark.asyncio
async def test_get_parameter_schema(backend: LangflowBackend):
    """
    Tests parameter schema retrieval.
    """
    schema = await backend.get_parameter_schema("flow1")
    assert schema == {}


@pytest.mark.asyncio
async def test_to_universal_flow_with_complete_data(backend: LangflowBackend):
    """
    Tests conversion of backend flow to universal flow with complete data.
    """
    backend_flow = {
        "id": "test_flow_123",
        "name": "Complete Test Flow",
        "description": "A fully specified test flow"
    }

    universal_flow = backend.to_universal_flow(backend_flow)

    assert universal_flow.id == "langflow_test_flow_123"
    assert universal_flow.name == "Complete Test Flow"
    assert universal_flow.description == "A fully specified test flow"
    assert universal_flow.backend.value == "langflow"
    assert universal_flow.backend_specific_id == "test_flow_123"


@pytest.mark.asyncio
async def test_to_universal_flow_with_minimal_data(backend: LangflowBackend):
    """
    Tests conversion of backend flow to universal flow with minimal data.
    """
    backend_flow = {"id": "minimal_flow"}

    universal_flow = backend.to_universal_flow(backend_flow)

    assert universal_flow.id == "langflow_minimal_flow"
    assert universal_flow.name == "Unnamed Langflow Flow"
    assert universal_flow.description == ""
    assert universal_flow.backend_specific_id == "minimal_flow"


@pytest.mark.asyncio
async def test_connect_when_already_connected(backend: LangflowBackend, mocker):
    """
    Tests that connect returns True when already connected.
    """
    mock_request = httpx.Request("GET", "/api/v1/flows")
    mock_response = httpx.Response(200, json=[], request=mock_request)
    mock_get = AsyncMock(return_value=mock_response)
    mocker.patch("httpx.AsyncClient.get", mock_get)

    # First connection
    connected1 = await backend.connect()
    assert connected1 is True

    # Second connection (should reuse existing client)
    connected2 = await backend.connect()
    assert connected2 is True

    await backend.disconnect()


@pytest.mark.asyncio
async def test_disconnect_when_not_connected(backend: LangflowBackend):
    """
    Tests that disconnect works safely when not connected.
    """
    await backend.disconnect()  # Should not raise any errors
    assert backend.is_connected is False
