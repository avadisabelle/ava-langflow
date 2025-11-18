# RISE Specification: Redis State Persistence

**Component**: Redis State Persistence
**Version**: 1.0.0
**Status**: Implementation Ready
**Created**: 2025-11-18
**Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`

---

## 1. Desired Outcome Definition

**What Users Want to Create:**

Users want **persistent conversational memory** that transcends session boundaries:

1. **Resume Conversations**: "Continue where we left off yesterday"
2. **Long-Running Projects**: Work on creative projects over days/weeks
3. **Context Retention**: System remembers previous topics, decisions, patterns
4. **Cross-Restart Continuity**: Survive MCP server restarts without losing state

**Creative Outcome**: Users experience continuous, coherent AI collaboration that feels like working with a long-term creative partner who never forgets.

---

## 2. Current Structural Reality

**Existing State:**
- Sessions are **transient** - exist only in memory
- Server restart = **complete amnesia**
- No cross-session learning or context
- Users must re-explain context every session

**Gap:**
The system wants to maintain continuity but has no persistent storage mechanism.

---

## 3. Structural Tension

**From**: Ephemeral, amnesia-prone sessions
**To**: Persistent, context-aware conversations

**Natural Progression**: The need for continuity creates structural tension that resolves through persistent state storage.

---

## 4. State Serialization Strategy

### 4.1 What to Persist

**UniversalSession State** (essential fields):
```json
{
  "id": "session_abc123",
  "backend": "flowise",
  "backend_session_id": "flowise_session_xyz",
  "status": "active",
  "current_flow_id": "creative_flow_001",
  "context": {
    "topic": "structural tension",
    "previous_insights": ["..."],
    "user_preferences": {"temperature": 0.7}
  },
  "history": [
    {"role": "user", "content": "...", "timestamp": "..."},
    {"role": "assistant", "content": "...", "timestamp": "..."}
  ],
  "metadata": {
    "created_at": "2025-11-18T10:00:00Z",
    "last_active": "2025-11-18T14:30:00Z",
    "message_count": 15
  }
}
```

**Format Choice**: **JSON**
- **Why**: Universal, human-readable, debuggable
- **Trade-off**: Larger than MessagePack, but worth it for transparency
- **Alternative considered**: MessagePack (smaller, faster, but opaque)

### 4.2 What NOT to Persist

- Backend-specific internal state
- Temporary execution artifacts
- Large binary data
- Sensitive credentials (never persist)

---

## 5. TTL Strategy

### 5.1 Default TTLs

- **Active Sessions**: 7 days (604800 seconds)
- **Execution Results**: 1 day (86400 seconds)
- **Execution History**: 7 days (604800 seconds)

### 5.2 Rationale

- **7 days**: Balances persistence with storage costs
- **User-configurable**: Via environment variables
- **Per-session override**: Future enhancement

### 5.3 Expiration Behavior

- **Automatic**: Redis TTL handles expiration
- **Grace period**: No hard cutoff - gradual degradation
- **Notification**: Log when sessions expire

---

## 6. Redis Key Design

### 6.1 Key Naming Convention

**Pattern**:
```
agentic_flywheel:<component>:<identifier>[:<sub_identifier>]
```

**Specific Keys**:
```
agentic_flywheel:session:<session_id>
agentic_flywheel:execution:<execution_id>
agentic_flywheel:history:<session_id>:<flow_id>
agentic_flywheel:meta:server_id
```

### 6.2 Key Collision Prevention

**Multi-Instance Safety**:
- Include server/instance ID in key prefix (optional)
- Use UUIDs for session IDs
- Namespace per deployment environment

**Example**:
```
agentic_flywheel:prod:session:abc123
agentic_flywheel:dev:session:abc123
```

### 6.3 Key Organization Benefits

- **Scannable**: List all sessions with pattern matching
- **Hierarchical**: Logical grouping
- **Deletable**: Bulk operations by pattern
- **Debuggable**: Clear key meanings

---

## 7. Error Handling & Fail-Safe Design

### 7.1 Failure Modes

1. **Redis Unavailable**: Service down, network issue
2. **Connection Timeout**: Slow network
3. **Serialization Error**: Invalid data format
4. **Key Not Found**: Session expired or never existed

### 7.2 Graceful Degradation

**Principle**: **Redis enhances but doesn't break functionality**

```python
async def save_session(session):
    if not self.enabled:
        return False  # Silently skip

    try:
        await redis_save(session)
        return True
    except RedisError as e:
        logger.warning(f"Redis save failed: {e}")
        return False  # Don't crash - just log

    # MCP tool continues working without persistence
```

### 7.3 Fallback Behavior

- **Save failure**: Log warning, continue
- **Load failure**: Return None, create new session
- **List failure**: Return empty list
- **Delete failure**: Log warning, continue

**User Impact**: Minimal - session just won't persist across restarts

---

## 8. Implementation Architecture

### 8.1 Core Classes

**RedisSessionManager**:
- Save/load/delete/list sessions
- Wraps coaia-mcp tools (`coaia_tash`, `coaia_fetch`, etc.)
- Handles serialization/deserialization
- Manages TTL

**RedisExecutionCache**:
- Cache individual execution results
- Store execution history per session/flow
- Support result retrieval for analysis

**RedisConfig**:
- Load configuration from environment
- Validate settings
- Provide defaults

### 8.2 Integration Points

**With MCP Server**:
```python
# After flow execution
await redis_session_manager.save_session(session)

# At session start
existing_session = await redis_session_manager.load_session(session_id)
if existing_session:
    # Resume conversation
    session = existing_session
else:
    # New session
    session = create_new_session()
```

**With Universal Query Tool**:
- Automatically save session after each query
- Load session context before execution
- Enrich responses with historical context

---

## 9. coaia-mcp Tool Integration

### 9.1 Tool Mapping

| Operation | coaia Tool | Purpose |
|-----------|-----------|---------|
| Save | `coaia_tash` | Store session state |
| Load | `coaia_fetch` | Retrieve session state |
| List | `coaia_list` | Find all sessions |
| Delete | `coaia_drop` | Remove session |

### 9.2 Tool Call Pattern

```python
# Save session
async def _call_coaia_tash(key: str, data: dict, ttl: int):
    """Wrapper for coaia_tash MCP tool"""
    # In production: Use MCP client to call tool
    # In tests: Mock this function
    pass

async def save_session(session):
    key = f"agentic_flywheel:session:{session.id}"
    data = serialize_session(session)
    await self._call_coaia_tash(key, data, self.ttl_seconds)
```

### 9.3 Testing Strategy

- **Mock coaia tools**: Don't require real Redis in tests
- **Test serialization**: Verify JSON round-trip
- **Test error handling**: Simulate failures
- **Integration tests**: Optional real Redis tests

---

## 10. Schema Evolution & Migration

### 10.1 Versioning Strategy

Include schema version in stored data:
```json
{
  "_schema_version": "1.0",
  "id": "session_abc",
  ...
}
```

### 10.2 Migration Path

**V1 → V2 Transition**:
1. New code reads both V1 and V2
2. New saves write V2
3. Gradual migration as sessions are accessed
4. V1 expires naturally via TTL

**No forced migration needed** - sessions expire automatically.

---

## 11. Performance Characteristics

### 11.1 Latency Targets

- **Save operation**: <50ms
- **Load operation**: <30ms
- **List operation**: <100ms
- **Delete operation**: <20ms

### 11.2 Optimization Strategies

- **Lazy loading**: Load only when needed
- **Batch operations**: Save multiple updates together
- **Compression**: Optional gzip for large sessions
- **Caching**: In-memory cache with Redis fallback

---

## 12. Monitoring & Observability

### 12.1 Metrics to Track

- Save success/failure rate
- Load hit/miss rate
- Average session size
- TTL expiration events
- Operation latencies

### 12.2 Logging Strategy

```python
logger.info("Session saved", extra={
    "session_id": session.id,
    "size_bytes": len(serialized),
    "ttl_seconds": ttl
})

logger.warning("Session load failed", extra={
    "session_id": session_id,
    "error": str(e)
})
```

---

## 13. Security Considerations

### 13.1 Data Protection

- **No credentials**: Never store API keys or passwords
- **Sanitization**: Remove sensitive data before save
- **Encryption**: Optional field-level encryption
- **Access control**: Redis AUTH if available

### 13.2 Privacy

- **TTL enforcement**: Auto-delete old sessions
- **Manual deletion**: Support user-initiated deletion
- **Audit trail**: Log access to sensitive sessions

---

## 14. Configuration

### 14.1 Environment Variables

```bash
# Redis state persistence
REDIS_STATE_ENABLED=true                    # Enable/disable persistence
REDIS_SESSION_TTL_SECONDS=604800            # 7 days
REDIS_EXECUTION_TTL_SECONDS=86400           # 1 day
REDIS_KEY_PREFIX=agentic_flywheel           # Custom prefix
REDIS_HOST=localhost                        # Redis host
REDIS_PORT=6379                             # Redis port
```

### 14.2 Runtime Configuration

```python
config = RedisConfig.from_env()
session_mgr = RedisSessionManager(
    enabled=config['enabled'],
    ttl_seconds=config['session_ttl'],
    key_prefix=config['key_prefix']
)
```

---

## 15. Testing Strategy

### 15.1 Unit Tests (>80% coverage)

- Serialization/deserialization
- TTL handling
- Error scenarios
- Key naming
- Config loading

### 15.2 Integration Tests

- Real Redis instance (optional)
- End-to-end save/load
- Multi-session scenarios
- Expiration testing

### 15.3 Mock Strategy

```python
@pytest.fixture
def mock_coaia_tools(mocker):
    """Mock coaia-mcp tool calls"""
    return {
        'tash': mocker.patch('redis_state._call_coaia_tash'),
        'fetch': mocker.patch('redis_state._call_coaia_fetch'),
        'list': mocker.patch('redis_state._call_coaia_list'),
        'drop': mocker.patch('redis_state._call_coaia_drop')
    }
```

---

## 16. Success Criteria

- ✅ **Persistence works**: Save/load round-trip successful
- ✅ **Fail-safe**: Redis errors don't break MCP
- ✅ **Performance**: Operations <50ms
- ✅ **TTL enforcement**: Old sessions auto-expire
- ✅ **Tests pass**: >80% coverage, all tests green
- ✅ **Clear namespace**: Organized Redis keys
- ✅ **User experience**: Seamless conversation continuity

---

## 17. Implementation Checklist

- [ ] Create `RedisSessionManager` class
- [ ] Create `RedisExecutionCache` class
- [ ] Create `RedisConfig` helper
- [ ] Implement save_session
- [ ] Implement load_session
- [ ] Implement delete_session
- [ ] Implement list_sessions
- [ ] Add error handling
- [ ] Write unit tests (>20 tests)
- [ ] Update integrations __init__.py
- [ ] Create result file

---

**Status**: ✅ Implementation Ready
**Design Decisions**: Documented and justified
**Next Steps**: Implement classes and tests

**Key Insight**: Persistence emerges naturally from the structural tension between ephemeral and continuous collaboration.
