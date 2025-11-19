# RISE Specification: Universal Query MCP Tool

**Component**: Universal Query MCP Tool
**Version**: 1.0
**Created**: 2025-11-18
**Parent Spec**: `rispecs/app.spec.md`
**Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Parent Trace**: `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`

---

## 🎨 Desired Outcome Definition

Users who integrate the Agentic Flywheel MCP into their creative workflows want to create:

### **Platform-Agnostic AI Interaction**
- **Ask Questions Naturally**: Users ask questions without needing to know which platform (Flowise or Langflow) handles them
- **Automatic Optimization**: System automatically selects the best backend based on capabilities, health, and performance
- **Seamless Experience**: Transitions between backends are invisible to users
- **Single Interface**: One tool (`universal_query`) replaces multiple platform-specific tools

### **Intelligent Routing**
- **Intent-Based Selection**: System understands question intent and routes to flows with matching capabilities
- **Health-Aware**: Automatically avoids unhealthy backends
- **Performance-Optimized**: Prefers faster, more reliable backends
- **User-Overridable**: Advanced users can specify backend explicitly when needed

### **Rich Observability**
- **Routing Transparency**: Users can see which backend was selected and why
- **Decision Metrics**: Scores for each backend decision factor visible in response metadata
- **Fallback Tracking**: When primary backend fails, users see fallback chain
- **Performance Insights**: Execution time, token usage, costs tracked per backend

---

## 📊 Current Structural Reality

The Agentic Flywheel currently has **fragmented querying**:

### **What Exists**
- ✅ `flowise_query` tool - Queries Flowise backend only
- ✅ Intent classification logic in `flowise_manager.py`
- ✅ `BackendRegistry` for multi-backend management
- ✅ `LangflowBackend` adapter (Task 1 complete)
- ✅ `FlowiseBackend` adapter (existing)
- ✅ Universal `FlowBackend` interface

### **What's Missing**
- ❌ **No unified query tool**: Users must choose `flowise_query` or hypothetical `langflow_query`
- ❌ **No intelligent routing**: No automatic backend selection based on capabilities
- ❌ **No fallback**: If Flowise is down, queries fail instead of routing to Langflow
- ❌ **No performance optimization**: No backend selection based on historical performance
- ❌ **No cross-backend comparison**: Can't evaluate which backend is better for specific intents

### **The Gap**
Between "manual platform selection" and "intelligent platform-agnostic querying" — users must know backend internals instead of just asking questions.

---

## ⚡ Structural Tension

**Current Reality**: Fragmented, platform-specific AI querying
**Desired Outcome**: Unified, intelligent, platform-agnostic querying

This tension creates natural advancement toward universal query tool:
1. **Users want simplicity** → System provides single interface
2. **Users want reliability** → System routes to healthy backends
3. **Users want performance** → System selects optimal backends
4. **Users want visibility** → System exposes routing decisions

---

## 🌱 Natural Progression Patterns

### **Pattern 1: Transparent Routing**
```python
# User doesn't specify backend
result = await universal_query("What is structural tension?")

# System internally:
# 1. Classifies intent → "creative-orientation"
# 2. Finds flows across all backends
# 3. Scores backends: Flowise (0.92), Langflow (0.75)
# 4. Routes to Flowise
# 5. Returns result + routing metadata
```

### **Pattern 2: Graceful Fallback**
```python
# Primary backend fails
backends = [flowise_backend, langflow_backend]

try:
    result = await route_to_backend(flowise_backend, query)
except BackendError:
    # Automatic fallback to secondary
    result = await route_to_backend(langflow_backend, query)
    result["_routing"]["fallback"] = True
```

### **Pattern 3: Explicit Override**
```python
# Advanced user specifies backend
result = await universal_query(
    question="Analyze this code",
    backend="langflow"  # Explicit selection
)
# System skips routing, uses Langflow directly
```

### **Pattern 4: Performance Learning**
```python
# System tracks backend performance
performance_tracker.record({
    "backend": "flowise",
    "intent": "creative-orientation",
    "latency_ms": 1250,
    "success": True
})

# Future queries use historical data
# "creative-orientation" queries → prefer flowise (faster historically)
```

---

## 🧭 Routing Algorithm

### **Multi-Factor Scoring**

Each backend receives a composite score based on:

#### **1. Flow Match Score** (50% weight)
```python
def calculate_match_score(flows: List[UniversalFlow], intent: str) -> float:
    """
    Score how well backend's flows match the query intent

    Returns: 0.0 (no match) to 1.0 (perfect match)
    """
    if not flows:
        return 0.0

    # Find flows with matching intent keywords
    matching_flows = [f for f in flows if intent in f.intent_keywords]

    if not matching_flows:
        return 0.0

    # Best flow determines score
    best_flow = max(matching_flows, key=lambda f: len(f.intent_keywords))

    # Score based on keyword specificity
    # More keywords = more specific = higher score
    specificity = min(len(best_flow.intent_keywords) / 10, 1.0)

    return 0.5 + (specificity * 0.5)  # Range: 0.5 to 1.0 for matches
```

#### **2. Health Score** (30% weight)
```python
async def calculate_health_score(backend: FlowBackend) -> float:
    """
    Score backend health and availability

    Returns: 0.0 (unhealthy) to 1.0 (healthy)
    """
    is_healthy = await backend.health_check()
    return 1.0 if is_healthy else 0.0
```

#### **3. Performance Score** (20% weight)
```python
def calculate_performance_score(
    backend: FlowBackend,
    intent: str,
    performance_history: Dict
) -> float:
    """
    Score based on historical performance for this intent

    Returns: 0.0 (poor performance) to 1.0 (excellent performance)
    """
    backend_id = backend.backend_type.value

    # Get historical performance for this backend + intent
    history = performance_history.get(f"{backend_id}:{intent}", [])

    if not history:
        return 0.5  # Neutral score if no history

    # Recent performance matters more (last 10 executions)
    recent = history[-10:]

    # Calculate success rate
    success_rate = sum(1 for r in recent if r["success"]) / len(recent)

    # Calculate average latency (normalized)
    avg_latency = sum(r["latency_ms"] for r in recent) / len(recent)
    latency_score = 1.0 - min(avg_latency / 5000, 1.0)  # 5s = 0.0 score

    # Combined performance score
    return (success_rate * 0.7) + (latency_score * 0.3)
```

#### **4. Composite Score**
```python
async def score_backend(
    backend: FlowBackend,
    intent: str,
    performance_history: Dict
) -> float:
    """
    Calculate composite score for backend selection

    Returns: 0.0 (worst) to 1.0 (best)
    """
    flows = await backend.discover_flows()

    match_score = calculate_match_score(flows, intent) * 0.5
    health_score = await calculate_health_score(backend) * 0.3
    perf_score = calculate_performance_score(backend, intent, performance_history) * 0.2

    return match_score + health_score + perf_score
```

---

## 🛡️ Fallback Strategy

### **Multi-Tier Fallback**

1. **Primary Backend Failure** → Route to highest scoring alternate
2. **All Backends Unhealthy** → Return cached response (if available)
3. **No Matching Flows** → Use generic flow or return helpful error
4. **Total System Failure** → Graceful error message with diagnostic info

```python
async def execute_with_fallback(
    backends: List[FlowBackend],
    query: str,
    intent: str
) -> Dict[str, Any]:
    """
    Execute query with automatic fallback chain
    """
    # Sort backends by score (highest first)
    scored_backends = await score_all_backends(backends, intent)
    scored_backends.sort(key=lambda x: x[1], reverse=True)

    last_error = None

    for backend, score in scored_backends:
        if score == 0.0:
            continue  # Skip backends with no matching flows

        try:
            result = await backend.execute_flow(...)
            result["_routing"]["backend_used"] = backend.backend_type.value
            result["_routing"]["score"] = score
            result["_routing"]["fallback_used"] = False
            return result

        except Exception as e:
            last_error = e
            logger.warning(f"Backend {backend.backend_type.value} failed: {e}")
            continue

    # All backends failed
    raise AllBackendsFailedError(
        f"All {len(backends)} backends failed. Last error: {last_error}"
    )
```

---

## ⚡ Performance Optimization

### **Caching Strategy**

#### **Flow Discovery Cache**
```python
# Cache discovered flows for 60 seconds
flow_cache = {
    "flowise": {"timestamp": 1637012345, "flows": [...]},
    "langflow": {"timestamp": 1637012345, "flows": [...]}
}

async def get_flows_cached(backend: FlowBackend) -> List[UniversalFlow]:
    cache_key = backend.backend_type.value
    cached = flow_cache.get(cache_key)

    if cached and (time.time() - cached["timestamp"]) < 60:
        return cached["flows"]

    # Cache miss or expired
    flows = await backend.discover_flows()
    flow_cache[cache_key] = {"timestamp": time.time(), "flows": flows}
    return flows
```

#### **Performance History Cache**
```python
# In-memory performance tracking (last 100 executions per backend:intent pair)
performance_cache = defaultdict(lambda: deque(maxlen=100))

def record_performance(backend: str, intent: str, latency_ms: float, success: bool):
    key = f"{backend}:{intent}"
    performance_cache[key].append({
        "timestamp": time.time(),
        "latency_ms": latency_ms,
        "success": success
    })
```

### **Parallel Backend Queries** (Future Enhancement)
```python
# Query all backends in parallel, use fastest response
async def parallel_query(backends: List[FlowBackend], query: str):
    tasks = [backend.execute_flow(...) for backend in backends]

    # Wait for first success
    for task in asyncio.as_completed(tasks):
        try:
            result = await task
            # Cancel remaining tasks
            for t in tasks:
                if not t.done():
                    t.cancel()
            return result
        except:
            continue
```

---

## 🔧 MCP Tool Schema

### **Tool Definition**

```json
{
  "name": "universal_query",
  "description": "Query AI workflows across all backends with intelligent routing. Automatically selects optimal backend (Flowise or Langflow) based on query intent, backend health, and performance. Supports session continuity and custom parameters.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "question": {
        "type": "string",
        "description": "Question or prompt to send to AI workflow. Can be multi-line for complex queries."
      },
      "intent": {
        "type": "string",
        "description": "Optional intent classification override. If not provided, system will classify automatically. Examples: 'creative-orientation', 'technical-analysis', 'document-qa'.",
        "enum": ["creative-orientation", "technical-analysis", "document-qa", "code-review", "general"]
      },
      "backend": {
        "type": "string",
        "enum": ["auto", "flowise", "langflow"],
        "description": "Backend selection strategy. 'auto' (default) uses intelligent routing. Specify 'flowise' or 'langflow' to force specific backend.",
        "default": "auto"
      },
      "session_id": {
        "type": "string",
        "description": "Session ID for conversation continuity. If provided, system maintains conversation context across queries."
      },
      "parameters": {
        "type": "object",
        "description": "Flow-specific parameters to customize execution",
        "properties": {
          "temperature": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 2.0,
            "description": "LLM temperature (0=deterministic, 2=creative)"
          },
          "max_tokens": {
            "type": "integer",
            "description": "Maximum tokens in response"
          },
          "stream": {
            "type": "boolean",
            "description": "Enable streaming response (if supported by backend)"
          }
        }
      },
      "include_routing_metadata": {
        "type": "boolean",
        "description": "Include routing decision metadata in response (backend selected, scores, fallback info)",
        "default": true
      }
    },
    "required": ["question"]
  }
}
```

---

## 💻 Implementation Pattern

### **Handler Function**

```python
from mcp import types
from agentic_flywheel.backends.registry import BackendRegistry
from agentic_flywheel.backends.base import BackendType
from agentic_flywheel.integrations import trace_mcp_tool, get_current_trace_id, LangfuseObservation

@app.call_tool()
@trace_mcp_tool("universal_query")
async def handle_universal_query(name: str, arguments: dict) -> List[types.TextContent]:
    """
    Universal query handler with intelligent backend routing
    """
    trace_id = get_current_trace_id()

    # Extract arguments
    question = arguments["question"]
    backend_pref = arguments.get("backend", "auto")
    session_id = arguments.get("session_id")
    intent_override = arguments.get("intent")
    parameters = arguments.get("parameters", {})
    include_metadata = arguments.get("include_routing_metadata", True)

    # Initialize backend registry
    registry = BackendRegistry()
    await registry.discover_backends()

    # Get available backends
    available_backends = registry.get_healthy_backends()

    if not available_backends:
        return [types.TextContent(
            type="text",
            text="❌ Error: No healthy backends available. All AI workflow platforms are currently offline."
        )]

    # Intent classification
    if intent_override:
        intent = intent_override
    else:
        intent = await classify_intent(question)
        await LangfuseObservation.add_intent_classification(
            trace_id, intent, 0.95, extract_keywords(question)
        )

    # Backend selection
    if backend_pref == "auto":
        # Intelligent routing
        backend, score = await select_optimal_backend(
            available_backends, intent, question
        )
        routing_method = "intelligent"
    else:
        # Explicit backend selection
        backend = registry.get_backend(BackendType(backend_pref))
        if not backend or not await backend.health_check():
            return [types.TextContent(
                type="text",
                text=f"❌ Error: Requested backend '{backend_pref}' is unavailable or unhealthy."
            )]
        score = 1.0
        routing_method = "explicit"

    await LangfuseObservation.add_flow_selection(
        trace_id,
        backend.backend_type.value,
        f"{backend.backend_type.value} backend",
        backend.backend_type.value,
        f"Selected via {routing_method} routing (score: {score:.2f})"
    )

    # Find best matching flow on selected backend
    flows = await backend.discover_flows()
    matching_flows = [f for f in flows if intent in f.intent_keywords]

    if not matching_flows:
        # Fallback to generic flow or return error
        return [types.TextContent(
            type="text",
            text=f"⚠️ No matching flows found for intent '{intent}' on {backend.backend_type.value}. Please rephrase your question or try a different backend."
        )]

    selected_flow = matching_flows[0]  # Best match

    # Execute flow
    start_time = time.time()

    try:
        result = await backend.execute_flow(
            flow_id=selected_flow.backend_specific_id,
            input_data={"question": question},
            parameters=parameters,
            session_id=session_id
        )

        duration_ms = (time.time() - start_time) * 1000

        await LangfuseObservation.add_execution(
            trace_id,
            {"question": question, "parameters": parameters},
            result,
            duration_ms
        )

        # Record performance for future routing
        record_performance(
            backend.backend_type.value,
            intent,
            duration_ms,
            success=True
        )

        # Format response
        response_text = format_universal_response(
            result=result,
            backend=backend.backend_type.value,
            flow_name=selected_flow.name,
            routing_score=score,
            routing_method=routing_method,
            duration_ms=duration_ms,
            include_metadata=include_metadata
        )

        return [types.TextContent(type="text", text=response_text)]

    except Exception as e:
        # Execution failed, try fallback
        await LangfuseObservation.add_error(
            trace_id,
            type(e).__name__,
            str(e),
            traceback.format_exc()
        )

        # Record failure
        duration_ms = (time.time() - start_time) * 1000
        record_performance(
            backend.backend_type.value,
            intent,
            duration_ms,
            success=False
        )

        # Attempt fallback to other backends
        remaining_backends = [b for b in available_backends if b != backend]

        if remaining_backends:
            # Try next best backend
            return await execute_with_fallback(
                remaining_backends,
                question,
                intent,
                parameters,
                session_id,
                trace_id
            )
        else:
            return [types.TextContent(
                type="text",
                text=f"❌ Error: Query execution failed on {backend.backend_type.value} and no fallback backends available.\n\nError: {str(e)}"
            )]
```

---

## 📋 Response Format

### **With Metadata** (default)

```markdown
✅ **Creative Orientation Guidance**

Structural tension is the gap between current reality and desired outcome...

---

**Routing Info**:
- Backend: flowise
- Flow: csv2507 (Creative Orientation)
- Selection: Intelligent (score: 0.92)
- Execution: 1,235ms
- Session: abc123
```

### **Without Metadata** (minimal)

```markdown
Structural tension is the gap between current reality and desired outcome...
```

---

## 🧪 Testing Strategy

### **Unit Tests** (tests/test_universal_query.py)

**Test Categories**:

1. **Intent Classification** (3 tests)
   - Automatic intent detection from question
   - Intent override via parameter
   - Unknown intent handling

2. **Backend Selection** (5 tests)
   - Auto routing selects highest scoring backend
   - Explicit backend selection (flowise/langflow)
   - Health check influences selection
   - Performance history influences selection
   - No healthy backends error

3. **Flow Matching** (3 tests)
   - Matching flows found for intent
   - No matching flows fallback
   - Best flow selection from multiple matches

4. **Execution** (4 tests)
   - Successful query execution
   - Parameter passing to backend
   - Session continuity
   - Result formatting

5. **Fallback** (4 tests)
   - Primary backend failure triggers fallback
   - Fallback chain exhausted error
   - All backends unhealthy error
   - Partial backend availability

6. **Performance Tracking** (2 tests)
   - Performance recorded after execution
   - Historical performance influences routing

7. **Metadata** (2 tests)
   - Metadata included by default
   - Metadata excluded when requested

**Total**: 23 comprehensive tests

---

## 🎯 Success Metrics

### **Functional Success**
- ✅ Routing accuracy >90% (selects optimal backend)
- ✅ Fallback success rate >95% (recovers from primary failures)
- ✅ Routing overhead <200ms
- ✅ All error conditions handled gracefully
- ✅ Session continuity maintained across backends

### **User Experience Success**
- ✅ Single tool replaces multiple platform-specific tools
- ✅ Users never need to know which backend handles query
- ✅ Routing decisions transparent and explainable
- ✅ Fallback invisible to users (seamless)
- ✅ Performance acceptable (no perceptible slowdown)

### **Integration Success**
- ✅ Works with BackendRegistry
- ✅ Integrates with langfuse_tracer (if available)
- ✅ Supports redis_state (if available)
- ✅ Standard MCP tool schema
- ✅ Compatible with existing flowise_query usage patterns

---

## 🔮 Future Enhancements

### **Phase 2: Advanced Routing**
- A/B testing support (route % of queries to test backends)
- Cost-aware routing (prefer cheaper backends)
- Latency-aware routing (prefer fastest for time-sensitive queries)
- Load balancing across multiple backend instances

### **Phase 3: Multi-Backend Queries**
- Parallel query execution (use fastest response)
- Consensus queries (query all backends, merge responses)
- Validation queries (cross-check answers across backends)

---

## 📚 Dependencies

### **Runtime Dependencies**
- `BackendRegistry` - Backend discovery and management
- `FlowBackend` implementations - Flowise, Langflow adapters
- `classify_intent()` - Intent classification function
- `langfuse_tracer` (optional) - Observability integration
- Standard library: `time`, `asyncio`, `traceback`

### **Development Dependencies**
- `pytest` - Unit testing
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking backend responses

---

## ✨ Alignment with RISE Principles

### **Reverse-Engineering**:
This spec reverse-engineers successful multi-platform query patterns from user needs and system capabilities.

### **Intent-Extraction**:
The intent is **platform-agnostic AI querying** — users want to ask questions, not manage backend infrastructure.

### **Specification**:
This document provides implementation-agnostic patterns. Another LLM could implement from this spec alone.

### **Export**:
The universal_query tool exports a clean, simple interface that hides backend complexity while exposing routing transparency.

---

## 🌟 Creative Advancement Scenario

**Before Universal Query** (Current Reality):
> User: "I want to ask about structural tension"
> System: "Which backend? flowise_query or langflow_query?"
> User: "Uh... I don't know. Which is better?"
> System: "Depends on your needs..."

**After Universal Query** (Desired Outcome):
> User: "What is structural tension?"
> System: *Automatically routes to Flowise (highest score for creative-orientation), executes, returns:*
> "Structural tension is the gap between current reality and desired outcome..."
> *(Routing: flowise, score: 0.92, 1.2s)*

**The Gap**: Between "user must understand backends" and "system handles backend selection intelligently" — universal query bridges this gap naturally.

---

**Specification Complete** ✅
**Ready for Implementation**: `universal_mcp_server.py` integration
**Integration Target**: All MCP servers in agentic_flywheel
**Creative Outcome**: Users create AI-powered solutions without platform concerns
