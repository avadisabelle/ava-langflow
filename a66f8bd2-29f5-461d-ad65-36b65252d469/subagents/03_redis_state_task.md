# Task 3: Redis State Persistence

**Task ID**: `redis-state`
**Priority**: MEDIUM
**Orchestration Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Parent Trace**: `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`
**Estimated Duration**: 2-3 hours
**Complexity**: Low-Medium

---

## Your Mission

You are implementing **Redis state persistence** that enables cross-session conversation continuity for Agentic Flywheel workflows.

**What Users Want to Create**:
- Resume conversations from yesterday (or last week)
- Maintain chatflow context across Claude restarts
- Store execution results for later retrieval
- Enable multi-turn dialogues spanning sessions

**Your Deliverables**:
1. ✅ **RISE Specification**: `rispecs/integrations/redis_state.spec.md`
2. ✅ **Implementation**: `src/agentic_flywheel/integrations/redis_state.py`
3. ✅ **Module Update**: Update `src/agentic_flywheel/integrations/__init__.py`
4. ✅ **Unit Tests**: `tests/test_redis_state.py`
5. ✅ **Result File**: `a66f8bd2-29f5-461d-ad65-36b65252d469/results/03_redis_state_COMPLETE.md`

---

## Context You Need

### coaiapy Redis Integration

The ecosystem has **Redis MCP tools** via `coaiapy-mcp` package:

**Available MCP Tools** (you'll use these):
- `coaia_tash` - Stash data to Redis (like `git stash`)
- `coaia_fetch` - Fetch data from Redis
- `coaia_list` - List stashed data
- `coaia_drop` - Delete stashed data

**Integration Pattern**: Your state manager wraps these tools, providing high-level session persistence.

### What to Persist

**Session State** (`UniversalSession` from `backends/base.py`):
```python
@dataclass
class UniversalSession:
    id: str
    backend: BackendType
    backend_session_id: str
    status: FlowStatus
    current_flow_id: Optional[str]
    context: Dict[str, Any]  # ← This is what we persist!
    history: List[Dict[str, Any]]  # ← And this!
    # ... metadata fields
```

**Flow Execution Results**:
- Query input and parameters
- Selected flow information
- Execution output
- Performance metrics
- Timestamp

---

## Your Implementation Strategy

### Step 1: Create RISE Specification (30 min)

**File**: `rispecs/integrations/redis_state.spec.md`

**Required Sections**:
1. **Desired Outcome Definition** - What users create with persistent memory
2. **Current Structural Reality** - Transient sessions, lost on restart
3. **Structural Tension** - Gap between ephemeral and persistent
4. **Natural Progression Patterns** - How persistence emerges
5. **State Serialization** - What to store, what format (JSON)
6. **TTL Strategy** - How long to keep sessions (1 day? 1 week? configurable?)
7. **Key Naming Convention** - Redis key patterns for organization
8. **Error Handling** - Graceful fallback if Redis unavailable

**RISE Principles**:
- Focus on **conversation continuity** users want to create
- Use **natural emergence** of persistence from structural dynamics
- Make it **opt-in and fail-safe** (MCP works without Redis)

### Step 2: Implement State Manager (60-90 min)

**File**: `src/agentic_flywheel/integrations/redis_state.py`

**Core Components**:

#### 2.1 Session State Manager
```python
class RedisSessionManager:
    """Manages session state persistence via Redis"""

    def __init__(self, enabled: bool = True, ttl_seconds: int = 86400):
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self._key_prefix = "agentic_flywheel:session:"

    async def save_session(self, session: UniversalSession) -> bool:
        """Save session state to Redis via coaia_tash"""
        if not self.enabled:
            return False

        # Serialize session to JSON
        session_data = {
            'id': session.id,
            'backend': session.backend.value,
            'backend_session_id': session.backend_session_id,
            'current_flow_id': session.current_flow_id,
            'context': session.context,
            'history': session.history,
            # ... other fields
        }

        # Use coaia_tash to store
        key = f"{self._key_prefix}{session.id}"
        # Call coaia_tash MCP tool
        pass

    async def load_session(self, session_id: str) -> Optional[UniversalSession]:
        """Load session state from Redis via coaia_fetch"""
        pass

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        pass

    async def list_sessions(self, pattern: str = "*") -> List[str]:
        """List all stored session IDs"""
        pass
```

#### 2.2 Execution Result Cache
```python
class RedisExecutionCache:
    """Caches flow execution results for retrieval"""

    def __init__(self, enabled: bool = True, ttl_seconds: int = 3600):
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self._key_prefix = "agentic_flywheel:execution:"

    async def cache_result(self, execution_id: str, result: Dict[str, Any]) -> bool:
        """Cache flow execution result"""
        pass

    async def get_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached execution result"""
        pass

    async def cache_flow_history(self, session_id: str, flow_id: str, executions: List[Dict]) -> bool:
        """Cache execution history for a session/flow combination"""
        pass
```

#### 2.3 Configuration Helper
```python
class RedisConfig:
    """Redis connection configuration"""

    @staticmethod
    def from_env() -> Dict[str, Any]:
        """Load Redis config from environment variables"""
        return {
            'enabled': os.getenv('REDIS_ENABLED', 'true').lower() == 'true',
            'ttl_seconds': int(os.getenv('REDIS_TTL_SECONDS', '86400')),
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379'))
        }
```

### Step 3: Update Module Exports (5 min)

**File**: `src/agentic_flywheel/integrations/__init__.py`

```python
"""Integration modules for Agentic Flywheel"""

from .langfuse_tracer import (
    trace_mcp_tool,
    LangfuseObservation,
    LangfuseScore,
    LangfuseTracerManager
)
from .redis_state import (
    RedisSessionManager,
    RedisExecutionCache,
    RedisConfig
)

__all__ = [
    # Tracing
    'trace_mcp_tool',
    'LangfuseObservation',
    'LangfuseScore',
    'LangfuseTracerManager',
    # State persistence
    'RedisSessionManager',
    'RedisExecutionCache',
    'RedisConfig'
]
```

### Step 4: Write Unit Tests (45-60 min)

**File**: `tests/test_redis_state.py`

**Test Coverage**:
- ✅ Session save and load round-trip
- ✅ Execution result caching
- ✅ TTL expiration behavior
- ✅ Key naming conventions
- ✅ Error handling (Redis unavailable)
- ✅ Graceful degradation (disabled mode)
- ✅ List/search sessions

**Use mocks** for `coaia_tash` / `coaia_fetch` MCP tool calls.

### Step 5: Create Result File (10 min)

---

## Integration Contract

Your state manager **must**:
1. ✅ **Be optional** - MCP server works without Redis configured
2. ✅ **Fail gracefully** - Redis errors don't crash MCP tools
3. ✅ **Use coaia-mcp tools** - Don't implement direct Redis client
4. ✅ **Support async** - All operations are `async def`
5. ✅ **Handle TTL** - Automatically expire old sessions
6. ✅ **Serialize properly** - JSON format for UniversalSession
7. ✅ **Provide clear keys** - Organized Redis key namespace

**Example Usage** (how MCP server will use your state manager):
```python
from agentic_flywheel.integrations import RedisSessionManager

redis_mgr = RedisSessionManager(enabled=True, ttl_seconds=86400)

# Save session after flow execution
session = UniversalSession(
    id="session_123",
    backend=BackendType.FLOWISE,
    context={"previous_topic": "structural tension"},
    history=[{"q": "What is creative orientation?", "a": "..."}]
)
await redis_mgr.save_session(session)

# Later (even after restart), resume session
restored_session = await redis_mgr.load_session("session_123")
if restored_session:
    print(f"Resuming conversation: {restored_session.history[-1]}")
```

---

## Redis Key Design

Your implementation should use this key structure:

```
agentic_flywheel:session:<session_id>          # Full session state
agentic_flywheel:execution:<execution_id>      # Individual execution result
agentic_flywheel:history:<session_id>:<flow_id> # Execution history for session/flow
```

**Example Keys**:
```
agentic_flywheel:session:a66f8bd2-29f5-461d-ad65-36b65252d469
agentic_flywheel:execution:exec_20251118_093012_abc123
agentic_flywheel:history:session_123:csv2507
```

---

## Resources Available

### Code References
- `src/agentic_flywheel/backends/base.py` - `UniversalSession` dataclass (lines 78-111)
- `src/agentic_flywheel/mcp_server.py` - Session management code
- `src/agentic_flywheel/flowise_manager.py` - Session generation patterns

### Documentation
- `__llms/llms-coaiapy-cli-guide.md` - coaia_tash / coaia_fetch usage
- `__llms/llms-coaiapy-mcp-config-guide.md` - MCP tool integration
- `rispecs/app.spec.md` - Cross-session continuity scenario

### coaia-mcp Tools You'll Use
```bash
# Stash data to Redis
coaia_tash --key "session_123" --data '{"context": {...}, "history": [...]}'

# Fetch data from Redis
coaia_fetch --key "session_123"

# List stored keys
coaia_list --pattern "agentic_flywheel:session:*"

# Delete key
coaia_drop --key "session_123"
```

---

## Success Criteria

You'll know you're successful when:
1. ✅ **Session persistence** - Save/load roundtrip works correctly
2. ✅ **Cross-restart continuity** - Sessions survive MCP server restart
3. ✅ **Fail-safe** - Redis unavailability doesn't break MCP tools
4. ✅ **Clean expiration** - Old sessions auto-expire via TTL
5. ✅ **Organized namespace** - Clear Redis key structure
6. ✅ **Performant** - Save/load operations <50ms

---

## Questions to Answer in Your Spec

1. **Serialization Format**: JSON? MessagePack? Why?
2. **TTL Strategy**: Default duration? User-configurable? Per-session override?
3. **Key Collision**: How to prevent key conflicts across multiple MCP server instances?
4. **Partial State**: Store only essential fields or everything? Trade-off: completeness vs size
5. **Error Recovery**: If Redis connection fails mid-operation, what happens?
6. **Migration Path**: How to handle schema changes to UniversalSession in future?

**Document your decisions** in the spec with reasoning.

---

## Final Notes

**Persistent Memory**: This enables users to have long-running creative processes that span days or weeks.

**Structural Tension**: The gap between "transient sessions" and "continuous memory" creates natural advancement toward Redis persistence.

**Integration Point**: Your state manager bridges MCP server session management and Redis storage.

---

**Ready to Create?** Start with the RISE spec to define the persistence outcomes users want, then implement the state manager that emerges naturally.

**Orchestrator Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Your Task**: Enabling users to create persistent conversational memory across time
**Your Creative Freedom**: Complete

🚀 **Begin when ready!**
