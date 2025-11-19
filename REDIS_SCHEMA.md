# Redis Schema Documentation - ava-langflow v2.0.0

**Version**: 2.0.0
**Last Updated**: 2025-11-18
**Purpose**: Document Redis key naming conventions and data structures for cross-instance standardization

---

## Overview

The ava-langflow platform uses Redis for:
1. **Session State Persistence**: Maintain conversation context across requests
2. **Execution Result Caching**: Cache flow execution results for performance
3. **Backend Performance Tracking**: Store and retrieve backend performance metrics

---

## Key Naming Conventions

### General Format
```
{namespace}:{entity_type}:{identifier}
```

### Namespaces
- `langflow`: All ava-langflow platform keys use this namespace
- Future: Could be `platform` or `agentic_flywheel` for cross-platform standardization

### Entity Types
- `session`: User conversation sessions
- `execution`: Flow execution results
- `backend`: Backend performance data

---

## Schema Details

### 1. Session State Keys

**Format**: `langflow:session:{session_id}`

**Purpose**: Store complete conversation context including history, current state, and metadata

**Data Structure**:
```json
{
  "session_id": "unique-session-identifier",
  "history": [
    {
      "role": "user",
      "content": "User message",
      "timestamp": "2025-11-18T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Assistant response",
      "timestamp": "2025-11-18T10:30:05Z"
    }
  ],
  "current_state": {
    "last_backend": "flowise",
    "last_flow_id": "flow-123",
    "conversation_count": 5
  },
  "metadata": {
    "created_at": "2025-11-18T10:00:00Z",
    "updated_at": "2025-11-18T10:30:05Z",
    "user_id": "optional-user-id",
    "tags": ["creative", "structural-tension"]
  }
}
```

**TTL**: 604800 seconds (7 days)
**Configured by**: `REDIS_TTL_SECONDS` environment variable

**Example Keys**:
- `langflow:session:user_abc_123`
- `langflow:session:conversation_xyz_789`
- `langflow:session:temp_session_001`

---

### 2. Execution Result Cache Keys

**Format**: `langflow:execution:{backend}:{flow_id}:{input_hash}`

**Purpose**: Cache flow execution results to avoid redundant API calls

**Data Structure**:
```json
{
  "input": {
    "question": "What is structural tension?",
    "session_id": "user_abc_123",
    "overrideConfig": {}
  },
  "output": {
    "result": "Structural tension is the gap between...",
    "backend": "flowise",
    "flow_id": "creative-orientation-flow",
    "execution_time_ms": 1250
  },
  "metadata": {
    "cached_at": "2025-11-18T10:30:00Z",
    "hit_count": 3
  }
}
```

**TTL**: 3600 seconds (1 hour)
**Rationale**: Execution results can become stale; shorter TTL ensures freshness

**Input Hash Algorithm**:
```python
import hashlib
import json

def generate_input_hash(question: str, session_id: str = None, config: dict = None) -> str:
    """Generate deterministic hash for execution cache key"""
    cache_input = {
        "question": question.strip().lower(),
        "session_id": session_id or "",
        "config": config or {}
    }
    return hashlib.md5(json.dumps(cache_input, sort_keys=True).encode()).hexdigest()[:16]
```

**Example Keys**:
- `langflow:execution:flowise:creative-flow:a1b2c3d4e5f6g7h8`
- `langflow:execution:langflow:tech-flow:9i8j7k6l5m4n3o2p`

---

### 3. Backend Performance Keys

**Format**: `langflow:backend:{backend_name}:metrics`

**Purpose**: Track performance metrics for intelligent routing decisions

**Data Structure**:
```json
{
  "backend_name": "flowise",
  "metrics": {
    "total_requests": 1523,
    "successful_requests": 1489,
    "failed_requests": 34,
    "total_latency_ms": 1825000,
    "avg_latency_ms": 1198,
    "last_success": "2025-11-18T10:30:00Z",
    "last_failure": "2025-11-18T09:15:23Z",
    "health_score": 0.98,
    "uptime_percentage": 99.2
  },
  "recent_latencies": [1200, 1150, 1320, 1180, 1250],
  "updated_at": "2025-11-18T10:30:05Z"
}
```

**TTL**: No expiration (persistent metrics)
**Update Frequency**: After each request

**Example Keys**:
- `langflow:backend:flowise:metrics`
- `langflow:backend:langflow:metrics`

---

## TTL Policies

| Key Type | Default TTL | Configurable | Environment Variable | Rationale |
|----------|-------------|--------------|---------------------|-----------|
| Session State | 7 days | Yes | `REDIS_TTL_SECONDS` | Long-term conversation continuity |
| Execution Cache | 1 hour | No | Hardcoded | Balance freshness vs performance |
| Backend Metrics | No expiration | No | N/A | Historical performance tracking |

---

## Configuration

### Environment Variables

```bash
# Enable/disable Redis persistence
REDIS_ENABLED=true

# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Optional

# Session TTL (seconds)
REDIS_TTL_SECONDS=604800  # 7 days default
```

### Code Configuration

**Location**: `src/agentic_flywheel/agentic_flywheel/state_manager.py`

```python
class RedisStateManager:
    """Manages Redis state persistence"""

    # TTL Constants
    SESSION_TTL = int(os.getenv("REDIS_TTL_SECONDS", "604800"))  # 7 days
    EXECUTION_CACHE_TTL = 3600  # 1 hour (hardcoded)

    # Key Prefixes
    SESSION_PREFIX = "langflow:session:"
    EXECUTION_PREFIX = "langflow:execution:"
    BACKEND_PREFIX = "langflow:backend:"
```

---

## API Operations

### Session Operations

**Save Session**:
```python
await state_manager.save_session(
    session_id="user_abc_123",
    session_data={
        "history": [...],
        "current_state": {...},
        "metadata": {...}
    }
)
# Key: langflow:session:user_abc_123
# TTL: 7 days
```

**Load Session**:
```python
session_data = await state_manager.load_session("user_abc_123")
# Returns dict or None if not found/expired
```

**Delete Session**:
```python
await state_manager.delete_session("user_abc_123")
# Removes key immediately
```

### Execution Cache Operations

**Cache Result**:
```python
await state_manager.cache_execution_result(
    backend="flowise",
    flow_id="creative-flow",
    input_hash="a1b2c3d4e5f6g7h8",
    result_data={...}
)
# Key: langflow:execution:flowise:creative-flow:a1b2c3d4e5f6g7h8
# TTL: 1 hour
```

**Retrieve Cached Result**:
```python
cached = await state_manager.get_cached_execution(
    backend="flowise",
    flow_id="creative-flow",
    input_hash="a1b2c3d4e5f6g7h8"
)
# Returns dict or None if cache miss/expired
```

### Backend Metrics Operations

**Update Metrics**:
```python
await state_manager.update_backend_metrics(
    backend="flowise",
    request_success=True,
    latency_ms=1250
)
# Key: langflow:backend:flowise:metrics
# No TTL (persistent)
```

**Get Metrics**:
```python
metrics = await state_manager.get_backend_metrics("flowise")
# Returns metrics dict or empty dict if not found
```

---

## Cross-Instance Standardization Proposal

### Recommended Changes for Platform-Wide Consistency

#### 1. Universal Namespace
**Current**: `langflow:*`
**Proposed**: `agentic_flywheel:*` or `platform:*`
**Rationale**: Works across ava-langflow, ava-Flowise, and future platforms

#### 2. Standardized Key Format
```
{namespace}:{platform}:{entity_type}:{identifier}
```

**Examples**:
- `agentic_flywheel:langflow:session:user_abc_123`
- `agentic_flywheel:flowise:session:user_abc_123`
- `agentic_flywheel:shared:backend:flowise:metrics`

**Benefits**:
- Clear platform ownership
- Easy cross-platform session sharing
- Namespace collision prevention

#### 3. Shared Session Format
**Goal**: Enable session sharing between ava-langflow and ava-Flowise

**Proposed Structure**:
```json
{
  "session_id": "universal-id",
  "platform_sessions": {
    "langflow": {
      "last_flow": "creative-flow",
      "last_backend": "flowise",
      "conversation_count": 5
    },
    "flowise": {
      "last_chatflow": "tech-support",
      "context_domains": ["technical", "python"],
      "conversation_count": 3
    }
  },
  "shared_history": [...],
  "metadata": {...}
}
```

#### 4. Shared TTL Configuration Module
**Create**: `libs/redis-config/ttl_policies.py` (shared package)

```python
# Shared TTL policies across platforms
SESSION_TTL_DAYS = 7
SESSION_TTL_SECONDS = SESSION_TTL_DAYS * 24 * 60 * 60

EXECUTION_CACHE_TTL_HOURS = 1
EXECUTION_CACHE_TTL_SECONDS = EXECUTION_CACHE_TTL_HOURS * 60 * 60

METRICS_TTL = None  # No expiration
```

---

## Migration Path

### Phase 1: Documentation (Current)
- ✅ Document current ava-langflow schema
- [ ] Instance 4 documents ava-Flowise schema
- [ ] Compare and identify differences

### Phase 2: Standardization (This Week)
- [ ] Agree on universal namespace (`agentic_flywheel` vs `platform`)
- [ ] Agree on key format with platform identifier
- [ ] Agree on shared session data structure
- [ ] Create shared Redis configuration module

### Phase 3: Implementation (Next Week)
- [ ] Both platforms adopt new key naming convention
- [ ] Implement backward compatibility (dual-write period)
- [ ] Migrate existing keys to new format
- [ ] Remove old key support after validation

### Phase 4: Integration (Next 2 Weeks)
- [ ] Implement cross-platform session sharing
- [ ] Test ava-langflow → ava-Flowise session handoff
- [ ] Test ava-Flowise → ava-langflow session handoff
- [ ] Create integration tests

---

## Testing Recommendations

### Unit Tests
```python
async def test_session_key_format():
    """Validate session key naming convention"""
    key = state_manager.get_session_key("test_session")
    assert key == "langflow:session:test_session"

async def test_execution_cache_key_format():
    """Validate execution cache key naming"""
    key = state_manager.get_execution_cache_key(
        backend="flowise",
        flow_id="test-flow",
        input_hash="abc123"
    )
    assert key == "langflow:execution:flowise:test-flow:abc123"

async def test_session_ttl():
    """Validate session TTL is set correctly"""
    await state_manager.save_session("test", {"data": "value"})
    ttl = await redis_client.ttl("langflow:session:test")
    assert 604700 < ttl <= 604800  # Allow for small timing variance
```

### Integration Tests
```python
async def test_cross_platform_session_sharing():
    """Test session sharing between platforms"""
    # ava-langflow creates session
    await langflow_state.save_session("shared_123", {...})

    # ava-Flowise loads same session
    session = await flowise_state.load_session("shared_123")
    assert session is not None
    assert session["platform_sessions"]["langflow"] is not None
```

---

## Monitoring & Observability

### Key Metrics to Track

1. **Redis Operation Latency**
   - GET operations: Target <10ms
   - SET operations: Target <15ms
   - Pipeline operations: Target <30ms

2. **Cache Hit Rates**
   - Execution cache hit rate: Target >50%
   - Session cache hit rate: Target >80%

3. **TTL Effectiveness**
   - Sessions expiring before use: Should be <5%
   - Execution cache serving stale data: Monitor and adjust TTL

4. **Key Space Growth**
   - Total keys: Monitor for unbounded growth
   - Memory usage: Alert if >80% capacity

### Recommended Langfuse Tracing

```python
from langfuse import Langfuse

@trace_operation("redis_save_session")
async def save_session(session_id: str, data: dict):
    """Trace Redis session save operations"""
    # Implementation with Langfuse span
```

---

## Appendix: Current Implementation

### Files
- **State Manager**: `src/agentic_flywheel/agentic_flywheel/state_manager.py`
- **Tests**: `tests/test_state_manager.py`
- **Configuration**: `.env.example` (REDIS_* variables)

### Dependencies
```toml
[project.optional-dependencies]
server = [
    "redis[asyncio]>=4.5.0"
]
```

### Redis Client Setup
```python
import redis.asyncio as aioredis

async def get_redis_client():
    """Create Redis client with connection pooling"""
    return await aioredis.from_url(
        f"redis://{host}:{port}/{db}",
        encoding="utf-8",
        decode_responses=True,
        max_connections=10
    )
```

---

**Document Status**: ✅ Complete
**Next Action**: Instance 4 to document ava-Flowise Redis schema
**Coordination**: Compare schemas and propose standardization plan

**Last Updated**: 2025-11-18
**Maintained By**: Instance 3 (ava-langflow)
