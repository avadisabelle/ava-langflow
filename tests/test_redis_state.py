#!/usr/bin/env python3
"""
Tests for Redis State Persistence and Execution Caching
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
import json
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime

from agentic_flywheel.integrations.redis_state import (
    RedisConfig,
    RedisSessionManager,
    RedisExecutionCache,
    REDIS_AVAILABLE
)
from agentic_flywheel.backends.base import UniversalSession, BackendType, FlowStatus


# Test Fixtures

@pytest.fixture
def mock_redis():
    """Create mock Redis connection"""
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=1)
    redis.scan = AsyncMock(return_value=(0, []))
    redis.close = AsyncMock()
    return redis


@pytest.fixture
def sample_session():
    """Create sample session for testing"""
    session = UniversalSession(
        id="test_session_123",
        backend=BackendType.FLOWISE,
        backend_session_id="flowise_abc",
        status=FlowStatus.ACTIVE,
        current_flow_id="flow_001",
        context={"topic": "structural tension", "user": "test_user"},
        history=[
            {
                "timestamp": "2025-11-18T10:00:00Z",
                "question": "What is creative orientation?",
                "flow_id": "flow_001",
                "response": "Creative orientation focuses on...",
                "duration_ms": 1234
            }
        ]
    )
    session.metadata = {"created_at": "2025-11-18T09:00:00Z"}
    session.created_at = "2025-11-18T09:00:00Z"
    return session


# RedisConfig Tests

def test_redis_config_from_env_defaults():
    """Test RedisConfig loads defaults correctly"""
    with patch.dict('os.environ', {}, clear=True):
        config = RedisConfig.from_env()

        assert config['enabled'] is True
        assert config['ttl_seconds'] == 604800  # 7 days
        assert config['host'] == 'localhost'
        assert config['port'] == 6379


def test_redis_config_from_env_custom():
    """Test RedisConfig loads custom environment variables"""
    with patch.dict('os.environ', {
        'REDIS_ENABLED': 'false',
        'REDIS_TTL_SECONDS': '3600',
        'REDIS_HOST': 'redis.example.com',
        'REDIS_PORT': '6380'
    }):
        config = RedisConfig.from_env()

        assert config['enabled'] is False
        assert config['ttl_seconds'] == 3600
        assert config['host'] == 'redis.example.com'
        assert config['port'] == 6380


# RedisSessionManager Tests

@pytest.mark.asyncio
async def test_session_manager_disabled():
    """Test session manager when disabled"""
    manager = RedisSessionManager(enabled=False)

    assert manager.enabled is False

    # Operations should return early
    result = await manager.save_session(Mock())
    assert result is False

    session = await manager.load_session("test")
    assert session is None

    deleted = await manager.delete_session("test")
    assert deleted is False

    sessions = await manager.list_sessions()
    assert sessions == []


@pytest.mark.asyncio
async def test_session_manager_redis_unavailable():
    """Test session manager when Redis package unavailable"""
    with patch('agentic_flywheel.integrations.redis_state.REDIS_AVAILABLE', False):
        manager = RedisSessionManager(enabled=True)

        # Should auto-disable if Redis not available
        assert manager.enabled is False


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_session_manager_connection_success(mock_redis):
    """Test successful Redis connection"""
    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        redis = await manager._get_redis()

        assert redis is not None
        mock_redis.ping.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_session_manager_connection_failure(mock_redis):
    """Test Redis connection failure handling"""
    mock_redis.ping.side_effect = Exception("Connection refused")

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        redis = await manager._get_redis()

        # Should disable on connection failure
        assert redis is None
        assert manager.enabled is False


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_save_session_success(mock_redis, sample_session):
    """Test successful session save"""
    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True, ttl_seconds=3600)

        result = await manager.save_session(sample_session)

        assert result is True

        # Verify Redis setex was called with correct parameters
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args

        assert call_args[0][0] == "agentic_flywheel:session:test_session_123"
        assert call_args[0][1] == 3600  # TTL

        # Verify JSON data
        saved_data = json.loads(call_args[0][2])
        assert saved_data['id'] == "test_session_123"
        assert saved_data['backend'] == "flowise"
        assert saved_data['status'] == "active"
        assert saved_data['current_flow_id'] == "flow_001"
        assert 'last_active' in saved_data


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_save_session_failure(mock_redis, sample_session):
    """Test session save failure handling"""
    mock_redis.setex.side_effect = Exception("Redis error")

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        result = await manager.save_session(sample_session)

        # Should return False but not crash
        assert result is False


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_load_session_success(mock_redis, sample_session):
    """Test successful session load"""
    # Prepare mock data
    session_data = {
        'id': "test_session_123",
        'backend': "flowise",
        'backend_session_id': "flowise_abc",
        'status': "active",
        'current_flow_id': "flow_001",
        'context': {"topic": "structural tension"},
        'history': [{"question": "test", "response": "answer"}],
        'metadata': {"created_at": "2025-11-18T09:00:00Z"},
        'created_at': "2025-11-18T09:00:00Z",
        'last_active': "2025-11-18T10:00:00Z"
    }
    mock_redis.get.return_value = json.dumps(session_data)

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        session = await manager.load_session("test_session_123")

        assert session is not None
        assert session.id == "test_session_123"
        assert session.backend == BackendType.FLOWISE
        assert session.status == FlowStatus.ACTIVE
        assert session.current_flow_id == "flow_001"
        assert session.context == {"topic": "structural tension"}
        assert len(session.history) == 1

        # Verify Redis get was called
        mock_redis.get.assert_called_once_with("agentic_flywheel:session:test_session_123")


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_load_session_not_found(mock_redis):
    """Test loading non-existent session"""
    mock_redis.get.return_value = None

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        session = await manager.load_session("nonexistent")

        assert session is None


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_load_session_corrupted_data(mock_redis):
    """Test loading session with corrupted JSON"""
    mock_redis.get.return_value = "invalid json {{{["

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        session = await manager.load_session("test")

        # Should return None on error, not crash
        assert session is None


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_delete_session_success(mock_redis):
    """Test successful session deletion"""
    mock_redis.delete.return_value = 1  # 1 key deleted

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        result = await manager.delete_session("test_session")

        assert result is True
        mock_redis.delete.assert_called_once_with("agentic_flywheel:session:test_session")


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_delete_session_not_found(mock_redis):
    """Test deleting non-existent session"""
    mock_redis.delete.return_value = 0  # 0 keys deleted

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        result = await manager.delete_session("nonexistent")

        assert result is False


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_list_sessions_success(mock_redis):
    """Test successful session listing"""
    # Mock SCAN returning keys
    mock_redis.scan.return_value = (
        0,  # Cursor (0 means done)
        [
            "agentic_flywheel:session:session1",
            "agentic_flywheel:session:session2",
            "agentic_flywheel:session:session3"
        ]
    )

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        sessions = await manager.list_sessions()

        assert len(sessions) == 3
        assert "session1" in sessions
        assert "session2" in sessions
        assert "session3" in sessions

        # Verify SCAN was called with correct pattern
        mock_redis.scan.assert_called_once()
        call_args = mock_redis.scan.call_args
        assert call_args[1]['match'] == "agentic_flywheel:session:*"


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_list_sessions_with_pattern(mock_redis):
    """Test session listing with custom pattern"""
    mock_redis.scan.return_value = (0, ["agentic_flywheel:session:test_session1"])

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        sessions = await manager.list_sessions(pattern="test_*")

        # Verify pattern was used
        call_args = mock_redis.scan.call_args
        assert call_args[1]['match'] == "agentic_flywheel:session:test_*"


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_list_sessions_pagination(mock_redis):
    """Test session listing with pagination"""
    # Mock SCAN requiring multiple iterations
    mock_redis.scan.side_effect = [
        (100, ["agentic_flywheel:session:session1"]),  # First batch
        (200, ["agentic_flywheel:session:session2"]),  # Second batch
        (0, ["agentic_flywheel:session:session3"])     # Last batch (cursor=0)
    ]

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        sessions = await manager.list_sessions()

        assert len(sessions) == 3
        assert mock_redis.scan.call_count == 3


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_session_manager_close(mock_redis):
    """Test session manager connection close"""
    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        # Establish connection
        await manager._get_redis()
        assert manager._redis is not None

        # Close connection
        await manager.close()

        mock_redis.close.assert_called_once()
        assert manager._redis is None


# RedisExecutionCache Tests

@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_cache_result_success(mock_redis):
    """Test successful execution result caching"""
    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        cache = RedisExecutionCache(enabled=True, ttl_seconds=3600)

        result_data = {
            "result": "Structural tension is...",
            "metadata": {"duration_ms": 1234}
        }

        cached = await cache.cache_result("exec_123", result_data)

        assert cached is True

        # Verify Redis setex was called
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args

        assert call_args[0][0] == "agentic_flywheel:execution:exec_123"
        assert call_args[0][1] == 3600  # TTL

        # Verify JSON data
        cached_data = json.loads(call_args[0][2])
        assert cached_data['result'] == "Structural tension is..."


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_cache_result_disabled():
    """Test caching when disabled"""
    cache = RedisExecutionCache(enabled=False)

    result = await cache.cache_result("exec_123", {"result": "test"})

    assert result is False


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_get_result_success(mock_redis):
    """Test successful cached result retrieval"""
    cached_data = {
        "result": "Cached response",
        "metadata": {"cached_at": "2025-11-18T10:00:00Z"}
    }
    mock_redis.get.return_value = json.dumps(cached_data)

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        cache = RedisExecutionCache(enabled=True)

        result = await cache.get_result("exec_123")

        assert result is not None
        assert result['result'] == "Cached response"

        mock_redis.get.assert_called_once_with("agentic_flywheel:execution:exec_123")


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_get_result_not_found(mock_redis):
    """Test retrieving non-existent cached result"""
    mock_redis.get.return_value = None

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        cache = RedisExecutionCache(enabled=True)

        result = await cache.get_result("nonexistent")

        assert result is None


@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_execution_cache_close(mock_redis):
    """Test execution cache connection close"""
    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        cache = RedisExecutionCache(enabled=True)

        await cache._get_redis()
        assert cache._redis is not None

        await cache.close()

        mock_redis.close.assert_called_once()
        assert cache._redis is None


# Integration Tests

@pytest.mark.asyncio
@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis package not available")
async def test_roundtrip_session_save_load(mock_redis, sample_session):
    """Test complete session save/load roundtrip"""
    saved_data = None

    def mock_setex(key, ttl, data):
        nonlocal saved_data
        saved_data = data
        return True

    def mock_get(key):
        return saved_data

    mock_redis.setex.side_effect = mock_setex
    mock_redis.get.side_effect = mock_get

    with patch('agentic_flywheel.integrations.redis_state.aioredis.from_url',
               return_value=mock_redis):
        manager = RedisSessionManager(enabled=True)

        # Save session
        save_result = await manager.save_session(sample_session)
        assert save_result is True

        # Load session
        loaded_session = await manager.load_session(sample_session.id)

        # Verify loaded data matches original
        assert loaded_session.id == sample_session.id
        assert loaded_session.backend == sample_session.backend
        assert loaded_session.status == sample_session.status
        assert loaded_session.current_flow_id == sample_session.current_flow_id
        assert loaded_session.context == sample_session.context


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
