#!/usr/bin/env python3
"""
Tests for the Langflow Backend Adapter.
"""

import pytest
import httpx
from unittest.mock import AsyncMock

from src.agentic_flywheel.backends.langflow.langflow_backend import LangflowBackend

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
    mock_response = httpx.Response(200, json=[])
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
    mock_response = httpx.Response(500)
    mock_get = AsyncMock(return_value=mock_response)
    mocker.patch(
        "httpx.AsyncClient.get",
        mock_get
    )

    # We need to manually create the client to test health_check in isolation
    backend._client = httpx.AsyncClient(base_url=BASE_URL)

    healthy = await backend.health_check()

    assert healthy is False
