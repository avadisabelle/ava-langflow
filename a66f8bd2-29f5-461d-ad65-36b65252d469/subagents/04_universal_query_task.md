# Task 4: Universal Query MCP Tool

**Task ID**: `universal-query`
**Priority**: HIGH
**Orchestration Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Parent Trace**: `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`
**Estimated Duration**: 3-4 hours
**Complexity**: Medium-High
**Dependencies**: Langflow backend (can use mocks initially)

---

## Your Mission

You are implementing the **Universal Query MCP Tool** - the primary user-facing interface for executing AI workflows across both Langflow and Flowise platforms with intelligent routing.

**What Users Want to Create**:
- Ask questions without caring which platform handles them
- Automatic backend selection based on capabilities
- Intelligent intent classification
- Seamless cross-platform workflow execution

**Your Deliverables**:
1. ✅ **RISE Specification**: `rispecs/mcp_tools/universal_query.spec.md`
2. ✅ **Tool Implementation Patterns**: Document integration into `universal_mcp_server.py`
3. ✅ **Routing Logic**: Intent → optimal backend selection algorithm
4. ✅ **Unit Tests**: `tests/test_universal_query.py`
5. ✅ **Result File**: `a66f8bd2-29f5-461d-ad65-36b65252d469/results/04_universal_query_COMPLETE.md`

---

## Context You Need

### Current Query Tools

**Existing** (`mcp_server.py`):
- `flowise_query` - Queries Flowise with intent classification
- Returns response from single backend only

**Your Universal Tool Should**:
- `universal_query` - Queries any backend (Flowise OR Langflow)
- Intelligent routing based on:
  - Flow capabilities (which backend has matching flows)
  - Backend health (which backends are available)
  - Performance metrics (which backend is faster)
  - User preferences (explicit backend override)

### Backend Registry Integration

**File**: `src/agentic_flywheel/backends/registry.py`

Your tool will use `BackendRegistry` to:
1. Discover available backends (Flowise, Langflow)
2. Get flows from all backends
3. Route queries to optimal backend
4. Handle fallback if primary backend fails

---

## Your Implementation Strategy

### Step 1: Create RISE Specification (45 min)

**File**: `rispecs/mcp_tools/universal_query.spec.md`

**Required Sections**:
1. **Desired Outcome** - What users create with universal query capability
2. **Current Reality** - Platform-specific queries, manual backend selection
3. **Structural Tension** - Gap between fragmented and unified querying
4. **Routing Algorithm** - How intent → backend selection works
5. **Fallback Strategy** - What happens if optimal backend fails
6. **Performance Optimization** - Caching, parallel queries, streaming
7. **Tool Schema** - MCP tool input/output specification

### Step 2: Design Routing Logic (60 min)

**Core Algorithm**:
```python
async def route_query(question: str, backends: List[FlowBackend]) -> FlowBackend:
    """
    Select optimal backend for query execution

    Algorithm:
    1. Classify intent from question
    2. Find flows matching intent across all backends
    3. Score backends based on:
       - Flow match quality (0-1)
       - Backend health (0-1)
       - Historical performance (0-1)
       - User preference weight
    4. Select highest scoring backend
    5. Return backend for execution
    """

    # Intent classification
    intent = classify_intent(question)

    # Find matching flows per backend
    backend_flows = {}
    for backend in backends:
        flows = await backend.discover_flows()
        matching = [f for f in flows if intent in f.intent_keywords]
        backend_flows[backend] = matching

    # Score backends
    scores = {}
    for backend, flows in backend_flows.items():
        match_score = calculate_match_score(flows, intent)
        health_score = await backend.health_check()
        perf_score = get_historical_performance(backend)

        scores[backend] = (
            match_score * 0.5 +
            health_score * 0.3 +
            perf_score * 0.2
        )

    # Select best backend
    return max(scores.items(), key=lambda x: x[1])[0]
```

### Step 3: MCP Tool Schema (30 min)

**Tool Definition**:
```python
types.Tool(
    name="universal_query",
    description="Query AI workflows across all backends with intelligent routing",
    inputSchema={
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "Question or prompt to send to AI workflow"
            },
            "intent": {
                "type": "string",
                "description": "Optional intent override (creative-orientation, technical-analysis, etc.)"
            },
            "backend": {
                "type": "string",
                "enum": ["flowise", "langflow", "auto"],
                "description": "Backend selection (auto = intelligent routing)",
                "default": "auto"
            },
            "session_id": {
                "type": "string",
                "description": "Session ID for conversation continuity"
            },
            "parameters": {
                "type": "object",
                "description": "Flow-specific parameters (temperature, max_tokens, etc.)"
            }
        },
        "required": ["question"]
    }
)
```

### Step 4: Tool Implementation Pattern (60 min)

**Handler Function**:
```python
@app.call_tool()
@trace_mcp_tool("universal_query")  # If tracing enabled
async def handle_universal_query(name: str, arguments: dict):
    question = arguments["question"]
    backend_pref = arguments.get("backend", "auto")
    session_id = arguments.get("session_id")

    # Get backend registry
    registry = BackendRegistry()
    await registry.discover_backends()

    if backend_pref == "auto":
        # Intelligent routing
        backend = await route_query(question, registry.get_all_backends())
    else:
        # Use specified backend
        backend = registry.get_backend(BackendType(backend_pref))

    # Execute query on selected backend
    result = await backend.execute_flow(
        flow_id=selected_flow.id,
        input_data={"question": question},
        parameters=arguments.get("parameters", {}),
        session_id=session_id
    )

    # Enhance result with metadata
    result["_mcp_metadata"] = {
        "backend_used": backend.backend_type.value,
        "flow_id": selected_flow.id,
        "routing_score": backend_score,
        "session_id": session_id
    }

    return [types.TextContent(type="text", text=format_response(result))]
```

### Step 5: Unit Tests (45-60 min)

**Test Coverage**:
- ✅ Intent classification accuracy
- ✅ Backend routing logic
- ✅ Fallback when primary backend fails
- ✅ Session continuity
- ✅ Parameter passing to backends
- ✅ Metadata enrichment

---

## Integration Contract

Your universal_query tool **must**:
1. ✅ Accept standard MCP tool schema
2. ✅ Return `List[types.TextContent]` response
3. ✅ Use `BackendRegistry` for backend discovery
4. ✅ Support both "auto" and explicit backend selection
5. ✅ Handle errors gracefully (backend unavailable, flow execution failed)
6. ✅ Provide rich metadata about routing decisions
7. ✅ Integrate with tracing (if langfuse_tracer available)
8. ✅ Support session persistence (if redis_state available)

---

## Resources Available

### Code References
- `src/agentic_flywheel/mcp_server.py` - Existing `flowise_query` tool (lines 486-502)
- `src/agentic_flywheel/backends/registry.py` - Backend discovery patterns
- `src/agentic_flywheel/flowise_manager.py` - Intent classification logic
- `rispecs/app.spec.md` - Universal query scenario (Scenario 1)

### Documentation
- `__llms/llms-rise-framework.txt` - RISE principles
- `src/agentic_flywheel/PLAN_BACKEND_MIGRATION_250929.md` - Universal tools design

---

## Success Criteria

1. ✅ **Transparent routing** - Users don't need to know which backend handles query
2. ✅ **Intelligent selection** - Routing picks optimal backend 90%+ of time
3. ✅ **Graceful fallback** - Fails to secondary backend if primary unavailable
4. ✅ **Rich metadata** - Response includes routing decisions for observability
5. ✅ **Performance** - Routing adds <200ms overhead

---

**Orchestrator Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Your Task**: Enabling users to query AI workflows without platform concerns
**Your Creative Freedom**: Complete

🚀 **Begin when ready!**
