#!/usr/bin/env python3
"""
Tests for Redis State Persistence
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from agentic_flywheel.integrations.redis_state import (
    RedisSessionManager,
    RedisExecutionCache,
    RedisConfig
)
from agentic_flywheel.backends import (
    UniversalSession,
    BackendType,
    FlowStatus
)


# Test Fixtures

@pytest.fixture
def sample_session():
    """Create a sample UniversalSession for testing"""
    return UniversalSession(
        id="test_session_123",
        backend=BackendType.FLOWISE,
        backend_session_id="flowise_session_xyz",
        status=FlowStatus.RUNNING,
        current_flow_id="creative_flow_001",
        context={"topic": "structural tension", "count": 5},
        history=[
            {"role": "user", "content": "What is creative orientation?"},
            {"role": "assistant", "content": "Creative orientation is..."}
        ]
    )


@pytest.fixture
def redis_manager():
    """Create RedisSessionManager instance"""
    return RedisSessionManager(enabled=True, ttl_seconds=3600)


@pytest.fixture
def execution_cache():
    """Create RedisExecutionCache instance"""
    return RedisExecutionCache(enabled=True, ttl_seconds=1800)


# RedisConfig Tests

def test_redis_config_from_env_defaults():
    """Test RedisConfig loads defaults when no env vars set"""
    config = RedisConfig.from_env()

    assert config['enabled'] is True
    assert config['session_ttl'] == 604800  # 7 days
    assert config['execution_ttl'] == 86400  # 1 day
    assert config['key_prefix'] == 'agentic_flywheel'
    assert config['host'] == 'localhost'
    assert config['port'] == 6379


def test_redis_config_from_env_custom(monkeypatch):
    """Test RedisConfig loads custom env vars"""
    monkeypatch.setenv('REDIS_STATE_ENABLED', 'false')
    monkeypatch.setenv('REDIS_SESSION_TTL_SECONDS', '3600')
    monkeypatch.setenv('REDIS_KEY_PREFIX', 'test_prefix')

    config = RedisConfig.from_env()

    assert config['enabled'] is False
    assert config['session_ttl'] == 3600
    assert config['key_prefix'] == 'test_prefix'


# RedisSessionManager Tests

def test_session_manager_initialization():
    """Test RedisSessionManager initialization"""
    manager = RedisSessionManager(
        enabled=True,
        ttl_seconds=7200,
        key_prefix="test"
    )

    assert manager.enabled is True
    assert manager.ttl_seconds == 7200
    assert manager.key_prefix == "test"


def test_make_session_key(redis_manager):
    """Test session key generation"""
    key = redis_manager._make_session_key("session_abc123")

    assert key == "agentic_flywheel:session:session_abc123"


def test_serialize_session(redis_manager, sample_session):
    """Test session serialization to JSON"""
    json_str = redis_manager._serialize_session(sample_session)
    data = json.loads(json_str)

    assert data['_schema_version'] == '1.0'
    assert data['id'] == "test_session_123"
    assert data['backend'] == "flowise"
    assert data["status"] == "running"
    assert data['current_flow_id'] == "creative_flow_001"
    assert data['context'] == {"topic": "structural tension", "count": 5}
    assert len(data['history']) == 2


def test_deserialize_session(redis_manager, sample_session):
    """Test session deserialization from JSON"""
    # Serialize first
    json_str = redis_manager._serialize_session(sample_session)

    # Then deserialize
    restored_session = redis_manager._deserialize_session(json_str)

    assert restored_session.id == sample_session.id
    assert restored_session.backend == sample_session.backend
    assert restored_session.status == sample_session.status
    assert restored_session.current_flow_id == sample_session.current_flow_id
    assert restored_session.context == sample_session.context
    assert len(restored_session.history) == len(sample_session.history)


def test_serialize_deserialize_roundtrip(redis_manager, sample_session):
    """Test full serialization/deserialization round trip"""
    json_str = redis_manager._serialize_session(sample_session)
    restored = redis_manager._deserialize_session(json_str)

    assert restored.id == sample_session.id
    assert restored.backend == sample_session.backend
    assert restored.context == sample_session.context
    assert restored.history == sample_session.history


@pytest.mark.asyncio
async def test_save_session_disabled():
    """Test save_session when disabled"""
    manager = RedisSessionManager(enabled=False)
    session = UniversalSession(
        id="test",
        backend=BackendType.FLOWISE,
        backend_session_id="test",
        status=FlowStatus.PENDING,
        context={},
        history=[]
    )

    result = await manager.save_session(session)

    assert result is False


@pytest.mark.asyncio
async def test_save_session_success(redis_manager, sample_session):
    """Test successful session save"""
    # Mock coaia_tash
    redis_manager._call_coaia_tash = AsyncMock(return_value=True)

    result = await redis_manager.save_session(sample_session)

    assert result is True
    redis_manager._call_coaia_tash.assert_called_once()


@pytest.mark.asyncio
async def test_save_session_failure(redis_manager, sample_session):
    """Test session save failure"""
    # Mock coaia_tash to fail
    redis_manager._call_coaia_tash = AsyncMock(return_value=False)

    result = await redis_manager.save_session(sample_session)

    assert result is False


@pytest.mark.asyncio
async def test_save_session_exception(redis_manager, sample_session):
    """Test session save handles exceptions gracefully"""
    # Mock coaia_tash to raise exception
    redis_manager._call_coaia_tash = AsyncMock(side_effect=Exception("Redis error"))

    result = await redis_manager.save_session(sample_session)

    assert result is False  # Graceful failure


@pytest.mark.asyncio
async def test_load_session_disabled():
    """Test load_session when disabled"""
    manager = RedisSessionManager(enabled=False)

    result = await manager.load_session("test_id")

    assert result is None


@pytest.mark.asyncio
async def test_load_session_not_found(redis_manager):
    """Test load_session when session doesn't exist"""
    redis_manager._call_coaia_fetch = AsyncMock(return_value=None)

    result = await redis_manager.load_session("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_load_session_success(redis_manager, sample_session):
    """Test successful session load"""
    # Serialize session
    json_str = redis_manager._serialize_session(sample_session)

    # Mock coaia_fetch to return serialized data
    redis_manager._call_coaia_fetch = AsyncMock(return_value=json_str)

    result = await redis_manager.load_session("test_session_123")

    assert result is not None
    assert result.id == sample_session.id
    assert result.backend == sample_session.backend
    assert result.context == sample_session.context


@pytest.mark.asyncio
async def test_load_session_exception(redis_manager):
    """Test load_session handles exceptions gracefully"""
    redis_manager._call_coaia_fetch = AsyncMock(side_effect=Exception("Redis error"))

    result = await redis_manager.load_session("test_id")

    assert result is None  # Graceful failure


@pytest.mark.asyncio
async def test_delete_session_disabled():
    """Test delete_session when disabled"""
    manager = RedisSessionManager(enabled=False)

    result = await manager.delete_session("test_id")

    assert result is False


@pytest.mark.asyncio
async def test_delete_session_success(redis_manager):
    """Test successful session deletion"""
    redis_manager._call_coaia_drop = AsyncMock(return_value=True)

    result = await redis_manager.delete_session("test_session_123")

    assert result is True
    redis_manager._call_coaia_drop.assert_called_once()


@pytest.mark.asyncio
async def test_delete_session_failure(redis_manager):
    """Test session deletion failure"""
    redis_manager._call_coaia_drop = AsyncMock(return_value=False)

    result = await redis_manager.delete_session("test_session_123")

    assert result is False


@pytest.mark.asyncio
async def test_list_sessions_disabled():
    """Test list_sessions when disabled"""
    manager = RedisSessionManager(enabled=False)

    result = await manager.list_sessions()

    assert result == []


@pytest.mark.asyncio
async def test_list_sessions_success(redis_manager):
    """Test successful session listing"""
    mock_keys = [
        "agentic_flywheel:session:session_1",
        "agentic_flywheel:session:session_2",
        "agentic_flywheel:session:session_3"
    ]
    redis_manager._call_coaia_list = AsyncMock(return_value=mock_keys)

    result = await redis_manager.list_sessions()

    assert len(result) == 3
    assert "session_1" in result
    assert "session_2" in result
    assert "session_3" in result


@pytest.mark.asyncio
async def test_list_sessions_with_pattern(redis_manager):
    """Test session listing with pattern"""
    mock_keys = [
        "agentic_flywheel:session:test_123",
        "agentic_flywheel:session:test_456"
    ]
    redis_manager._call_coaia_list = AsyncMock(return_value=mock_keys)

    result = await redis_manager.list_sessions(pattern="test_*")

    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_sessions_exception(redis_manager):
    """Test list_sessions handles exceptions gracefully"""
    redis_manager._call_coaia_list = AsyncMock(side_effect=Exception("Redis error"))

    result = await redis_manager.list_sessions()

    assert result == []  # Graceful failure


# RedisExecutionCache Tests

def test_execution_cache_initialization():
    """Test RedisExecutionCache initialization"""
    cache = RedisExecutionCache(
        enabled=True,
        ttl_seconds=1800,
        key_prefix="test"
    )

    assert cache.enabled is True
    assert cache.ttl_seconds == 1800
    assert cache.key_prefix == "test"


def test_make_execution_key(execution_cache):
    """Test execution key generation"""
    key = execution_cache._make_execution_key("exec_123")

    assert key == "agentic_flywheel:execution:exec_123"


def test_make_history_key(execution_cache):
    """Test history key generation"""
    key = execution_cache._make_history_key("session_123", "flow_456")

    assert key == "agentic_flywheel:history:session_123:flow_456"


@pytest.mark.asyncio
async def test_cache_result_disabled():
    """Test cache_result when disabled"""
    cache = RedisExecutionCache(enabled=False)

    result = await cache.cache_result("exec_1", {"output": "test"})

    assert result is False


@pytest.mark.asyncio
async def test_cache_result_success(execution_cache):
    """Test successful result caching"""
    execution_cache._call_coaia_tash = AsyncMock(return_value=True)

    result_data = {
        "output": "Flow execution result",
        "latency_ms": 1500
    }

    result = await execution_cache.cache_result("exec_123", result_data)

    assert result is True
    execution_cache._call_coaia_tash.assert_called_once()


@pytest.mark.asyncio
async def test_cache_result_exception(execution_cache):
    """Test cache_result handles exceptions gracefully"""
    execution_cache._call_coaia_tash = AsyncMock(side_effect=Exception("Redis error"))

    result = await execution_cache.cache_result("exec_123", {"output": "test"})

    assert result is False  # Graceful failure


@pytest.mark.asyncio
async def test_get_result_disabled():
    """Test get_result when disabled"""
    cache = RedisExecutionCache(enabled=False)

    result = await cache.get_result("exec_1")

    assert result is None


@pytest.mark.asyncio
async def test_get_result_not_found(execution_cache):
    """Test get_result when result doesn't exist"""
    execution_cache._call_coaia_fetch = AsyncMock(return_value=None)

    result = await execution_cache.get_result("nonexistent")

    assert result is None


@pytest.mark.asyncio
async def test_get_result_success(execution_cache):
    """Test successful result retrieval"""
    cached_data = {
        "execution_id": "exec_123",
        "result": {"output": "Cached result"},
        "cached_at": datetime.now().isoformat()
    }
    execution_cache._call_coaia_fetch = AsyncMock(return_value=json.dumps(cached_data))

    result = await execution_cache.get_result("exec_123")

    assert result is not None
    assert result == {"output": "Cached result"}


@pytest.mark.asyncio
async def test_cache_flow_history_success(execution_cache):
    """Test successful flow history caching"""
    execution_cache._call_coaia_tash = AsyncMock(return_value=True)

    executions = [
        {"timestamp": "2025-11-18T10:00:00", "output": "Result 1"},
        {"timestamp": "2025-11-18T10:05:00", "output": "Result 2"}
    ]

    result = await execution_cache.cache_flow_history("session_123", "flow_456", executions)

    assert result is True
    execution_cache._call_coaia_tash.assert_called_once()


@pytest.mark.asyncio
async def test_cache_flow_history_disabled():
    """Test cache_flow_history when disabled"""
    cache = RedisExecutionCache(enabled=False)

    result = await cache.cache_flow_history("session_1", "flow_1", [])

    assert result is False


# Integration Tests

@pytest.mark.asyncio
async def test_full_session_lifecycle(redis_manager, sample_session):
    """Test complete session save/load/delete lifecycle"""
    # Setup mocks for full lifecycle
    saved_data = {}

    async def mock_save(key, data, ttl):
        saved_data[key] = data
        return True

    async def mock_fetch(key):
        return saved_data.get(key)

    async def mock_delete(key):
        if key in saved_data:
            del saved_data[key]
            return True
        return False

    redis_manager._call_coaia_tash = mock_save
    redis_manager._call_coaia_fetch = mock_fetch
    redis_manager._call_coaia_drop = mock_delete

    # Save session
    save_result = await redis_manager.save_session(sample_session)
    assert save_result is True

    # Load session
    loaded = await redis_manager.load_session(sample_session.id)
    assert loaded is not None
    assert loaded.id == sample_session.id
    assert loaded.context == sample_session.context

    # Delete session
    delete_result = await redis_manager.delete_session(sample_session.id)
    assert delete_result is True

    # Verify deleted
    loaded_after_delete = await redis_manager.load_session(sample_session.id)
    assert loaded_after_delete is None
