# RISE Specification: Redis State Persistence

**Component**: Redis Session State Manager
**Version**: 1.0
**Created**: 2025-11-18
**Parent Spec**: `rispecs/app.spec.md`
**Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`

---

## 🎨 Desired Outcome Definition

Users want to create **continuous conversational experiences** that transcend individual sessions, enabling long-running creative processes that span days, weeks, or even months.

### **Cross-Session Continuity**
- Resume conversations from yesterday or last week seamlessly
- Maintain full context across Claude restarts
- Reference previous interactions in ongoing dialogues
- Build upon past work without re-explaining context

### **Persistent Memory**
- Chatflow execution history preserved
- Session context and state maintained
- Execution results retrievable after session ends
- Multi-turn dialogues spanning multiple sessions

### **Fail-Safe Persistence**
- Persistence never blocks or crashes MCP operations
- Graceful fallback when Redis unavailable
- Optional feature (works without Redis)
- Transparent to users (happens automatically)

---

## 📊 Current Structural Reality

Sessions are **ephemeral** - state exists only in memory and vanishes on restart.

### **What Exists**
- ✅ Session management via `UniversalSession` dataclass
- ✅ In-memory session storage
- ✅ Context and history tracking during active session
- ✅ Available Redis tools via `coaiapy-mcp` (coaia_tash, coaia_fetch)

### **What's Missing**
- ❌ No cross-session persistence
- ❌ Context lost on MCP server restart
- ❌ Cannot resume conversations from previous days
- ❌ Execution history disappears
- ❌ No long-term memory capability

---

## ⚡ Structural Tension

**Current**: Transient, in-memory sessions
**Desired**: Persistent, cross-session continuity

This tension drives natural advancement toward Redis-backed state persistence.

---

## 🔑 Redis Key Design

```
agentic_flywheel:session:<session_id>              # Full session state
agentic_flywheel:execution:<execution_id>          # Individual execution
agentic_flywheel:history:<session_id>:<flow_id>    # Execution history
```

**TTL Strategy**: 7 days default, configurable per key type

---

## 💾 State Serialization

**Format**: JSON (human-readable, debuggable, universal)

**Session Data**:
```json
{
  "id": "session_abc123",
  "backend": "flowise",
  "backend_session_id": "flowise_xyz",
  "status": "active",
  "current_flow_id": "csv2507",
  "context": {
    "topic": "structural tension",
    "previous_queries": ["What is creative orientation?"]
  },
  "history": [
    {
      "timestamp": "2025-11-18T10:00:00Z",
      "question": "What is creative orientation?",
      "flow_id": "csv2507",
      "response": "Creative orientation focuses on...",
      "duration_ms": 1234
    }
  ],
  "metadata": {
    "created_at": "2025-11-18T10:00:00Z",
    "last_active": "2025-11-18T10:05:00Z"
  }
}
```

---

## 🧪 Implementation Pattern

```python
from agentic_flywheel.integrations import RedisSessionManager

# Initialize
redis_mgr = RedisSessionManager(enabled=True, ttl_seconds=604800)  # 7 days

# Save session
await redis_mgr.save_session(session)

# Load session (even after restart)
session = await redis_mgr.load_session("session_abc123")

# If Redis fails, falls back gracefully
```

---

## ✅ Integration Contract

1. **Optional**: Works without Redis configured
2. **Fail-safe**: Redis errors don't crash MCP
3. **Async**: All operations async
4. **TTL-managed**: Auto-expiration
5. **JSON serialized**: Standard format
6. **Organized keys**: Clear namespace

---

## 🎯 Success Metrics

- Session save/load roundtrip < 50ms
- Cross-restart continuity works
- Graceful Redis unavailability handling
- Auto-expiration via TTL
- Clean key organization

**Specification Complete** ✅