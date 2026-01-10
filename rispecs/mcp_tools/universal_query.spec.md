# RISE Specification: Universal Query MCP Tool

**Component**: Universal Query MCP Tool
**Version**: 1.0.0
**Status**: Implementation Ready
**Created**: 2025-11-18
**Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`

---

## 1. Desired Outcome Definition

**What Users Want to Create:**

Users want to interact with AI workflows **without platform concerns**. They want to:

1. **Ask Questions Naturally**: "Help me analyze this technical document" - without knowing whether Langflow or Flowise handles it better
2. **Seamless Experience**: The system routes to the optimal backend transparently
3. **Reliability**: If the primary backend fails, fallback to secondary backend automatically
4. **Observability**: Understand which backend handled their query and why
5. **Session Continuity**: Maintain conversation context across multiple queries

**Creative Outcome**: Users experience a unified AI workflow platform that intelligently orchestrates multiple backends, making the underlying complexity invisible while delivering optimal results.

---

## 2. Current Structural Reality

### Existing State

**Platform-Specific Tools** (`mcp_server.py`):
- `flowise_query` - Hardcoded to Flowise backend only
- Manual backend selection required
- No cross-platform routing
- No fallback mechanisms

**Backend Infrastructure** (available):
- `BackendRegistry` - Manages multiple backends
- `FlowBackend` interface - Universal abstraction
- `LangflowBackend` - New backend implementation
- `FlowiseBackend` - Existing backend (via manager)

**Gaps**:
- No intelligent routing algorithm
- No intent-to-backend mapping
- No performance-based selection
- No unified query interface

---

## 3. Structural Tension

**From**: Fragmented platform-specific queries
**To**: Unified intelligent query routing

**Tension Points**:
1. **Manual → Automatic**: Users manually choose backends → System auto-selects optimal backend
2. **Single → Multi**: One backend per query → Multiple backends with fallback
3. **Opaque → Transparent**: Hidden routing logic → Observable decision-making
4. **Stateless → Stateful**: No session context → Cross-session continuity

**Natural Progression**: The system wants to resolve routing complexity into simple, natural queries.

---

## 4. Routing Algorithm

### 4.1 Intent Classification

**Input**: User question (string)
**Output**: Intent category + confidence score

**Categories**:
- `creative-orientation` - Creative/vision work (Robert Fritz patterns)
- `technical-analysis` - Code analysis, debugging, technical deep-dives
- `structural-thinking` - System design, architecture, patterns
- `conversation` - General chat, Q&A
- `rag-retrieval` - Document retrieval, knowledge base queries
- `data-processing` - ETL, transformation, analysis

**Implementation Pattern**:
```python
def classify_intent(question: str) -> Tuple[str, float]:
    """
    Classify user intent from question text

    Returns:
        (intent_category, confidence_score)
    """
    # Keyword-based classification (can be enhanced with ML)
    keywords = question.lower()

    if any(word in keywords for word in ['creative', 'vision', 'goal', 'tension']):
        return ('creative-orientation', 0.9)
    elif any(word in keywords for word in ['code', 'debug', 'error', 'function']):
        return ('technical-analysis', 0.85)
    elif any(word in keywords for word in ['architecture', 'design', 'pattern', 'system']):
        return ('structural-thinking', 0.8)
    elif any(word in keywords for word in ['document', 'find', 'search', 'retrieve']):
        return ('rag-retrieval', 0.85)
    else:
        return ('conversation', 0.5)
```

### 4.2 Backend Scoring Algorithm

**Inputs**:
- User intent + confidence
- Available backends
- Backend health status
- Historical performance metrics

**Scoring Formula**:
```
Backend Score = (
    flow_match_score * 0.4 +      # Does backend have matching flows?
    health_score * 0.3 +            # Is backend healthy/responsive?
    performance_score * 0.2 +       # Historical performance
    capability_score * 0.1          # Backend-specific capabilities
)
```

**Component Scores**:

1. **Flow Match Score** (0.0 - 1.0):
   - 1.0: Backend has flows with exact intent match
   - 0.7: Backend has flows with partial intent match
   - 0.3: Backend has general-purpose flows
   - 0.0: Backend has no matching flows

2. **Health Score** (0.0 - 1.0):
   - 1.0: Backend connected and healthy
   - 0.5: Backend connected but slow to respond
   - 0.0: Backend disconnected or unhealthy

3. **Performance Score** (0.0 - 1.0):
   - Based on historical latency, success rate, quality scores
   - Cached from previous executions
   - Decays over time (recent performance weighted higher)

4. **Capability Score** (0.0 - 1.0):
   - Langflow: 1.0 for RAG, 0.7 for conversation
   - Flowise: 1.0 for conversation, 0.7 for RAG
   - Custom backends: Configurable

### 4.3 Selection Logic

```python
async def select_backend(
    question: str,
    backends: List[FlowBackend],
    user_preference: Optional[BackendType] = None
) -> Tuple[FlowBackend, UniversalFlow, float]:
    """
    Select optimal backend and flow for query execution

    Returns:
        (selected_backend, selected_flow, routing_score)
    """
    # User override takes precedence
    if user_preference:
        backend = get_backend(user_preference)
        if backend and backend.is_connected:
            flows = await backend.discover_flows()
            flow = select_best_flow(flows, question)
            return (backend, flow, 1.0)

    # Classify intent
    intent, confidence = classify_intent(question)

    # Score all backends
    scores = {}
    for backend in backends:
        if not backend.is_connected:
            continue

        # Get flows matching intent
        flows = await backend.discover_flows()
        matching_flows = [f for f in flows if intent in f.intent_keywords]

        # Calculate component scores
        flow_match = calculate_flow_match_score(matching_flows, intent, confidence)
        health = 1.0 if await backend.health_check() else 0.0
        performance = get_cached_performance(backend)
        capability = get_capability_score(backend, intent)

        # Combined score
        total_score = (
            flow_match * 0.4 +
            health * 0.3 +
            performance * 0.2 +
            capability * 0.1
        )

        scores[backend] = {
            'score': total_score,
            'flows': matching_flows,
            'breakdown': {
                'flow_match': flow_match,
                'health': health,
                'performance': performance,
                'capability': capability
            }
        }

    # Select highest scoring backend
    if not scores:
        raise NoBackendsAvailable("No healthy backends available")

    best_backend = max(scores.items(), key=lambda x: x[1]['score'])
    backend, info = best_backend

    # Select best flow from backend
    flow = select_best_flow(info['flows'], question)

    return (backend, flow, info['score'])
```

---

## 5. Fallback Strategy

### 5.1 Primary Execution Failure

**Trigger**: Primary backend execution fails or times out

**Fallback Cascade**:
1. **Retry Once**: Attempt same backend again (transient errors)
2. **Secondary Backend**: Try next highest-scoring backend
3. **Any Healthy Backend**: Try any available healthy backend
4. **Graceful Failure**: Return informative error to user

**Implementation**:
```python
async def execute_with_fallback(
    question: str,
    backends: List[FlowBackend],
    max_retries: int = 2
) -> Dict[str, Any]:
    """Execute query with fallback strategy"""

    # Get ranked backends
    ranked = await rank_backends(question, backends)

    for attempt, (backend, flow, score) in enumerate(ranked):
        try:
            result = await backend.execute_flow(
                flow_id=flow.backend_specific_id,
                input_data={"question": question},
                timeout=30.0
            )

            # Success - add metadata
            result['_routing'] = {
                'backend_used': backend.backend_type.value,
                'flow_id': flow.id,
                'routing_score': score,
                'attempt': attempt + 1,
                'fallback_used': attempt > 0
            }

            return result

        except Exception as e:
            logger.warning(
                f"Backend {backend.backend_type.value} failed (attempt {attempt + 1}): {e}"
            )

            if attempt == len(ranked) - 1:
                # All backends failed
                return {
                    'error': 'All backends failed',
                    'attempts': attempt + 1,
                    'last_error': str(e)
                }

            # Continue to next backend
            continue
```

### 5.2 Timeout Handling

**Timeout Tiers**:
- Backend health check: 5 seconds
- Flow discovery: 10 seconds
- Flow execution: 30 seconds (configurable)
- Overall universal_query: 45 seconds

**Graceful Degradation**:
- If discovery times out: Use cached flow list
- If execution times out: Try faster backend
- If all time out: Return partial results with timeout notice

---

## 6. Performance Optimization

### 6.1 Caching Strategy

**Flow Discovery Cache**:
- TTL: 5 minutes (configurable)
- Invalidation: On backend reconnect
- Warm-up: Periodic background refresh

**Backend Health Cache**:
- TTL: 30 seconds
- Fast path: Return cached health for routing decisions

**Performance Metrics Cache**:
- Rolling window: Last 100 executions per backend
- Metrics: Latency (p50, p95), success rate, quality scores

### 6.2 Parallel Queries (Future Enhancement)

For high-confidence routing (score > 0.9), execute on single backend.
For low-confidence routing (score < 0.6), execute on top 2 backends in parallel:
- Return fastest successful response
- Use slower response for performance learning

---

## 7. MCP Tool Schema

### 7.1 Tool Definition

```python
types.Tool(
    name="universal_query",
    description="""Query AI workflows across all backends with intelligent routing.

    Automatically selects the optimal backend (Flowise, Langflow, etc.) based on:
    - Question intent and complexity
    - Backend health and availability
    - Historical performance metrics
    - Flow capabilities

    Supports automatic fallback if primary backend fails.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Question or prompt to send to AI workflow"
            },
            "intent": {
                "type": "string",
                "description": "Optional explicit intent (creative-orientation, technical-analysis, etc.)",
                "enum": [
                    "creative-orientation",
                    "technical-analysis",
                    "structural-thinking",
                    "conversation",
                    "rag-retrieval",
                    "data-processing",
                    "auto"
                ],
                "default": "auto"
            },
            "backend": {
                "type": "string",
                "description": "Optional backend selection (auto = intelligent routing)",
                "enum": ["auto", "flowise", "langflow"],
                "default": "auto"
            },
            "session_id": {
                "type": "string",
                "description": "Session ID for conversation continuity across queries"
            },
            "parameters": {
                "type": "object",
                "description": "Flow-specific parameters (temperature, max_tokens, etc.)",
                "properties": {
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                    "max_tokens": {"type": "integer", "minimum": 1},
                    "stream": {"type": "boolean"}
                }
            },
            "timeout": {
                "type": "number",
                "description": "Execution timeout in seconds (default: 30)",
                "minimum": 1,
                "maximum": 120,
                "default": 30
            }
        },
        "required": ["question"]
    }
)
```

### 7.2 Response Format

**Success Response**:
```json
{
  "result": "AI workflow response text",
  "session_id": "session_abc123",
  "_mcp_metadata": {
    "backend_used": "langflow",
    "flow_id": "langflow_creative_flow_001",
    "flow_name": "Creative Orientation Assistant",
    "routing_score": 0.87,
    "routing_breakdown": {
      "flow_match": 0.9,
      "health": 1.0,
      "performance": 0.8,
      "capability": 0.8
    },
    "intent_classified": "creative-orientation",
    "intent_confidence": 0.92,
    "execution_time_ms": 1847,
    "fallback_used": false,
    "attempt": 1
  }
}
```

**Error Response**:
```json
{
  "error": "All backends failed",
  "attempts": 2,
  "backends_tried": ["langflow", "flowise"],
  "last_error": "Connection timeout",
  "_mcp_metadata": {
    "routing_attempted": true,
    "backends_available": ["langflow", "flowise"],
    "all_healthy": false
  }
}
```

---

## 8. Integration Contract

### 8.1 Must Support

1. ✅ **Standard MCP Tool Interface**: Accept `name: str, arguments: dict`
2. ✅ **Return MCP Response**: `List[types.TextContent]`
3. ✅ **BackendRegistry Integration**: Use global registry for backend discovery
4. ✅ **Automatic + Manual Modes**: Support both "auto" routing and explicit backend selection
5. ✅ **Error Handling**: Graceful failures, never raise unhandled exceptions
6. ✅ **Metadata Enrichment**: Include routing decisions in response
7. ✅ **Session Support**: Accept and propagate session_id
8. ✅ **Timeout Handling**: Respect user-provided timeout values

### 8.2 Optional Integrations

1. **Langfuse Tracing**: If available, trace routing decisions and execution
2. **Redis State**: If available, persist session context
3. **Performance Metrics**: Store execution metrics for future routing decisions

### 8.3 Dependencies

**Required**:
- `BackendRegistry` (backends/registry.py)
- At least one backend implementation (FlowiseBackend or LangflowBackend)

**Optional**:
- `LangfuseTracerManager` (integrations/langfuse_tracer.py)
- `RedisStateManager` (integrations/redis_state.py)

---

## 9. Testing Strategy

### 9.1 Unit Tests

**Coverage Requirements**: >80%

**Test Categories**:

1. **Intent Classification** (5 tests):
   - Test each intent category recognition
   - Test multi-keyword matching
   - Test low-confidence classification
   - Test edge cases (empty string, very long text)

2. **Backend Scoring** (8 tests):
   - Test flow match scoring
   - Test health score integration
   - Test performance score calculation
   - Test capability scoring
   - Test combined score formula
   - Test score ranking
   - Test tie-breaking

3. **Backend Selection** (6 tests):
   - Test auto-selection (highest score wins)
   - Test explicit backend override
   - Test no backends available error
   - Test single backend scenario
   - Test multiple backends with clear winner
   - Test multiple backends with similar scores

4. **Fallback Logic** (5 tests):
   - Test primary backend success (no fallback)
   - Test primary failure → secondary success
   - Test all backends fail
   - Test timeout handling
   - Test retry logic

5. **MCP Tool Integration** (4 tests):
   - Test tool invocation with minimal args
   - Test tool invocation with all args
   - Test tool response format
   - Test tool error format

6. **Session Continuity** (3 tests):
   - Test session_id propagation
   - Test session creation
   - Test cross-query context

### 9.2 Integration Tests

1. **Multi-Backend Scenario**:
   - Set up mock Flowise + Langflow backends
   - Send queries requiring different intents
   - Verify correct routing decisions

2. **Fallback Scenario**:
   - Simulate primary backend failure
   - Verify fallback to secondary
   - Verify metadata reflects fallback

3. **Performance Test**:
   - 100 sequential queries
   - Verify routing overhead < 200ms
   - Verify caching effectiveness

---

## 10. Success Metrics

### 10.1 Functional Success

- ✅ **Routing Accuracy**: 90%+ correct backend selection (measured against manual labels)
- ✅ **Availability**: 99%+ query success rate (with fallback)
- ✅ **Latency**: <200ms routing overhead (excluding backend execution)
- ✅ **Fallback Rate**: <5% of queries require fallback

### 10.2 User Experience Success

- ✅ **Transparency**: Users can see which backend handled their query
- ✅ **Simplicity**: Single tool interface for all backends
- ✅ **Reliability**: No manual intervention needed for backend selection
- ✅ **Observability**: Full trace of routing decisions available

### 10.3 Integration Success

- ✅ **Zero Breaking Changes**: Existing `flowise_query` tool continues to work
- ✅ **Backward Compatible**: New tool coexists with legacy tools
- ✅ **Composable**: Works with tracing, state persistence, admin tools

---

## 11. Implementation Phases

### Phase 1: Core Routing (This Task)
- Intent classification
- Backend scoring and selection
- Basic fallback logic
- MCP tool integration
- Unit tests

### Phase 2: Performance Optimization (Future)
- Advanced caching strategies
- Parallel query execution
- ML-based intent classification
- Performance metric collection

### Phase 3: Advanced Features (Future)
- Multi-turn conversation optimization
- Context-aware routing (use previous queries to inform routing)
- User preference learning
- A/B testing framework for routing strategies

---

## 12. RISE Alignment

**Reverse-Engineering**: Traced from user desire for "simple, unified AI queries"
**Intent-Extraction**: Users want platform complexity hidden, optimal results delivered
**Specification**: Implementation-agnostic patterns enable multiple implementations
**Export**: Clean, composable interface integrates naturally with ecosystem

**Creative Advancement**: Bridges gap from "manual platform selection" to "intelligent automatic orchestration"

---

**Status**: ✅ Implementation Ready
**Estimated Implementation Time**: 3-4 hours
**Complexity**: Medium-High
**Next Steps**: Implement routing logic, create tests, integrate with MCP server
