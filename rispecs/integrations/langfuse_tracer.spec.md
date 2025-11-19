# RISE Specification: Langfuse Tracing Integration

**Component**: Langfuse Creative Archaeology Tracer
**Version**: 1.0
**Created**: 2025-11-18
**Parent Spec**: `rispecs/app.spec.md`
**Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Parent Trace**: `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`

---

## 🎨 Desired Outcome Definition

Users who integrate the Agentic Flywheel MCP into their creative workflows want to create:

### **Complete Creative Archaeology**
- **Visual Journey Maps**: See the entire decision path from question → intent → flow → execution → result
- **Pattern Recognition**: Identify recurring interaction patterns that indicate workflow optimization opportunities
- **Quality Evolution**: Track how response quality improves over time through accumulated learning
- **Decision Transparency**: Understand *why* the system selected specific flows for specific queries
- **Historical Context**: Reference past conversations and decisions when building new capabilities

### **Actionable Intelligence**
- **Performance Insights**: Know which flows perform best for which intents
- **Bottleneck Identification**: Discover where execution slows down or fails
- **Human Feedback Loop**: Capture annotations and corrections that improve future decisions
- **Cost Awareness**: Track token usage and API costs across workflows
- **Confidence Metrics**: See how certain the system was about each decision

### **Fail-Safe Observability**
- **Non-Blocking Traces**: Tracing failures never interrupt creative flow
- **Graceful Degradation**: System works perfectly even when Langfuse is unavailable
- **Zero Configuration**: Tracing "just works" when Langfuse credentials are present
- **Privacy Respect**: Sensitive data can be filtered from traces automatically

---

## 📊 Current Structural Reality

The Agentic Flywheel MCP currently operates in an **ephemeral mode**:

### **What Exists**
- ✅ MCP server with 7 operational tools
- ✅ Intelligent flow selection via intent classification
- ✅ Session management with in-memory state
- ✅ Flow execution with success/failure responses
- ✅ Available Langfuse tools via `coaiapy-mcp` (coaia_fuse_trace_create, coaia_fuse_add_observation, coaia_fuse_score_create)

### **What's Missing**
- ❌ **No historical record**: Each interaction disappears after completion
- ❌ **No decision visibility**: Users don't know *why* a specific flow was chosen
- ❌ **No performance tracking**: Can't identify slow flows or bottlenecks
- ❌ **No quality learning**: System can't learn from past successes/failures
- ❌ **No error archaeology**: Failed executions leave no diagnostic trail

### **The Gap**
Between "intelligent execution" and "intelligent evolution" — the system makes good decisions but cannot learn from them because they vanish.

---

## ⚡ Structural Tension

**Current Reality**: Ephemeral, invisible AI orchestration
**Desired Outcome**: Observable, improvable creative archaeology

This tension creates natural advancement toward tracing:
1. **Users want to understand** → System provides transparency
2. **Users want to optimize** → System captures performance data
3. **Users want to improve** → System enables learning loops
4. **Users want reliability** → System diagnoses failures

---

## 🌱 Natural Progression Patterns

### **Pattern 1: Decorator Emergence**
Rather than rewriting MCP tools, tracing *wraps* existing functions:
```python
@trace_mcp_tool("flowise_query")
async def handle_flowise_query(name: str, arguments: dict):
    # Original logic unchanged
    return result
```
The decorator handles all trace creation, observation logging, and scoring **transparently**.

### **Pattern 2: Observation Hierarchy**
Traces naturally organize into parent-child relationships:
```
Trace: "flowise_query execution"
├─ Observation: "Intent Classification" (creative-orientation, 0.95 confidence)
├─ Observation: "Flow Selection" (csv2507, backend: flowise)
├─ Observation: "Flow Execution" (input, output, 1.2s duration)
└─ Scores: Quality (0.9), Latency (1200ms), Success (1.0)
```

### **Pattern 3: Fail-Safe Design**
All tracing operations are wrapped in try-except blocks that log failures but never propagate exceptions:
```python
try:
    await create_trace(...)
except Exception as e:
    logger.warning(f"Tracing failed: {e}")
    # Continue execution normally
```

### **Pattern 4: Content-First Logging**
Following coaia-fuse guidance, observations prioritize `input_data` and `output_data` over `metadata`:
- **✅ input_data**: User question, flow configuration, execution context
- **✅ output_data**: Flow response, decision reasoning, performance metrics
- **metadata**: Only high-level tags (environment, model, version)

---

## 🏗️ Tracing Architecture

### **Components**

#### 1. **Trace Decorator** (`@trace_mcp_tool`)
**Purpose**: Automatically wrap MCP tool execution with Langfuse trace lifecycle

**Responsibilities**:
- Create trace at start of MCP tool call
- Store trace_id in async context for child observations
- Execute wrapped function
- Add final execution observation with input/output
- Add performance scores (latency, success)
- Handle errors gracefully (log but don't crash)

**Interface**:
```python
def trace_mcp_tool(tool_name: str, parent_trace_id: Optional[str] = None):
    """
    Decorator for MCP tool handlers that creates Langfuse trace automatically

    Args:
        tool_name: Name of the MCP tool being traced
        parent_trace_id: Optional parent trace for hierarchical tracing

    Returns:
        Decorated async function with transparent tracing
    """
```

#### 2. **LangfuseObservation Helper**
**Purpose**: Structured observation creation for key decision points

**Methods**:
- `add_intent_classification(trace_id, intent, confidence, keywords)`: Document intent classification decision
- `add_flow_selection(trace_id, flow_id, flow_name, backend, reasoning)`: Document flow selection logic
- `add_execution(trace_id, input_data, output_data, duration_ms)`: Document flow execution with I/O
- `add_error(trace_id, error_type, error_message, stack_trace)`: Document execution failures

**Interface**:
```python
class LangfuseObservation:
    """Helper for adding structured observations to Langfuse traces"""

    @staticmethod
    async def add_intent_classification(
        trace_id: str,
        intent: str,
        confidence: float,
        matched_keywords: List[str]
    ) -> bool:
        """
        Add observation documenting intent classification decision

        Returns: True if observation added, False if tracing disabled/failed
        """
```

#### 3. **LangfuseScore Helper**
**Purpose**: Add quantitative metrics to traces for analysis

**Methods**:
- `add_quality_score(trace_id, score, reasoning)`: User-facing quality (0.0-1.0)
- `add_latency_score(trace_id, duration_ms)`: Execution performance metric
- `add_success_score(trace_id, success, error)`: Binary success/failure indicator
- `add_cost_score(trace_id, tokens, cost_usd)`: Token usage and API cost tracking

**Scoring Semantics**:
- **Quality**: 0.0 (poor) → 1.0 (excellent), based on response relevance and completeness
- **Latency**: Raw milliseconds (lower is better)
- **Success**: 1.0 (success) or 0.0 (failure)
- **Cost**: Total USD cost for the execution

#### 4. **LangfuseTracerManager**
**Purpose**: Centralized tracer configuration and lifecycle management

**Responsibilities**:
- Enable/disable tracing globally
- Store parent trace ID for session-level tracing
- Manage active trace registry (trace_id → metadata)
- Provide context management for nested traces
- Handle Langfuse client initialization (lazy, fail-safe)

**Configuration**:
```python
# Via environment variables
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
AGENTIC_FLYWHEEL_PARENT_TRACE_ID=a50f3fc2-eb8c-434d-a37e-ef9615d9c07d

# Or via code
tracer_manager = LangfuseTracerManager(
    enabled=True,
    parent_trace_id="a50f3fc2-eb8c-434d-a37e-ef9615d9c07d"
)
```

---

## 🔗 Integration Points

### **MCP Server Lifecycle**

#### **Phase 1: Server Initialization**
```python
# In mcp_server.py or universal_mcp_server.py
from agentic_flywheel.integrations import LangfuseTracerManager

# Initialize tracer at server startup
tracer = LangfuseTracerManager(
    enabled=os.getenv("LANGFUSE_ENABLED", "true").lower() == "true",
    parent_trace_id=os.getenv("AGENTIC_FLYWHEEL_PARENT_TRACE_ID")
)
```

#### **Phase 2: Tool Handler Decoration**
```python
from agentic_flywheel.integrations import trace_mcp_tool, LangfuseObservation, LangfuseScore

@app.call_tool()
@trace_mcp_tool("flowise_query")
async def handle_flowise_query(name: str, arguments: dict):
    trace_id = get_current_trace_id()  # From decorator context

    # Intent classification
    intent = classify_intent(arguments["question"])
    await LangfuseObservation.add_intent_classification(
        trace_id, intent, 0.95, ["creative", "goal"]
    )

    # Flow selection
    flow = select_flow(intent)
    await LangfuseObservation.add_flow_selection(
        trace_id, flow.id, flow.name, "flowise",
        f"Selected based on intent '{intent}' matching keywords {flow.intent_keywords}"
    )

    # Execute
    start = time.time()
    result = await execute_flow(flow, arguments["question"])
    duration = (time.time() - start) * 1000

    await LangfuseObservation.add_execution(
        trace_id, arguments["question"], result, duration
    )

    # Scores
    await LangfuseScore.add_latency_score(trace_id, duration)
    await LangfuseScore.add_success_score(trace_id, True)

    return result
```

#### **Phase 3: Error Handling**
```python
@trace_mcp_tool("flowise_query")
async def handle_flowise_query(name: str, arguments: dict):
    trace_id = get_current_trace_id()

    try:
        # ... execution ...
    except Exception as e:
        await LangfuseObservation.add_error(
            trace_id, type(e).__name__, str(e), traceback.format_exc()
        )
        await LangfuseScore.add_success_score(trace_id, False, str(e))
        raise  # Re-raise to MCP server
```

---

## 🌳 Trace Hierarchy

### **Session-Level Parent Trace**
Created once per user session (e.g., Claude Code session):
```
Parent Trace: "avaLangflowAgenticFlywheel Session"
├─ Trace: flowise_query (csv2507)
├─ Trace: flowise_query (faith2story2507)
├─ Trace: flowise_list_flows
└─ Trace: flowise_query (csv2507)
```

### **Tool-Level Child Traces**
Created for each MCP tool invocation:
```
Trace: "flowise_query: What is structural tension?"
├─ Observation: Intent Classification
├─ Observation: Flow Selection
├─ Observation: Flow Execution
└─ Scores: Quality, Latency, Success
```

### **Nested Observations**
Complex operations create observation hierarchies:
```
Observation: Flow Execution
├─ input_data: "What is structural tension?"
├─ output_data: "Structural tension is..."
└─ Child Observation: API Call
    ├─ input_data: HTTP request details
    └─ output_data: HTTP response details
```

---

## 🛡️ Error Handling Strategy

### **Principle**: **Never break user experience due to tracing failures**

### **Levels of Failure**

#### **Level 1: Langfuse Unavailable**
- **Detection**: coaia_fuse_trace_create times out or returns error
- **Response**: Log warning, set `tracer.enabled = False`, continue execution
- **User Impact**: None (tracing silently disabled)

#### **Level 2: Individual Observation Fails**
- **Detection**: coaia_fuse_add_observation raises exception
- **Response**: Log warning, skip observation, continue execution
- **User Impact**: None (trace incomplete but execution succeeds)

#### **Level 3: Score Creation Fails**
- **Detection**: coaia_fuse_score_create raises exception
- **Response**: Log warning, skip score, continue execution
- **User Impact**: None (trace has observations but missing scores)

### **Implementation Pattern**
```python
async def add_observation(...):
    if not tracer.enabled:
        return False

    try:
        # Call coaia_fuse_add_observation MCP tool
        await call_mcp_tool("coaia_fuse_add_observation", {...})
        return True
    except Exception as e:
        logger.warning(f"Observation failed (non-blocking): {e}")
        return False
```

---

## ⏱️ Performance Considerations

### **Target Overhead**: <100ms per MCP tool call

### **Optimization Strategies**:
1. **Async-First**: All tracing operations are `async` and non-blocking
2. **Batch Observations**: Group related observations into single API call where possible
3. **Lazy Initialization**: Only initialize Langfuse client when first trace created
4. **Background Tasks**: Use asyncio.create_task() for non-critical scores
5. **Caching**: Cache trace_id in context vars to avoid repeated lookups

### **Latency Budget**:
- Trace creation: ~30ms
- Observation addition: ~20ms each (parallelizable)
- Score creation: ~15ms each (background task)
- Total: ~50-80ms with 3 observations + 3 scores

---

## 🔧 Configuration Interface

### **Environment Variables**
```bash
# Required for tracing
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional configuration
LANGFUSE_ENABLED=true                                    # Enable/disable tracing
AGENTIC_FLYWHEEL_PARENT_TRACE_ID=a50f3fc2-...           # Session parent trace
LANGFUSE_TRACE_TIMEOUT_MS=5000                          # Timeout for trace operations
LANGFUSE_FILTER_SENSITIVE_DATA=true                     # Redact sensitive content
```

### **Programmatic Configuration**
```python
from agentic_flywheel.integrations import LangfuseTracerManager

# Global configuration
tracer = LangfuseTracerManager(
    enabled=True,
    parent_trace_id="a50f3fc2-eb8c-434d-a37e-ef9615d9c07d",
    timeout_ms=5000,
    filter_sensitive=True
)

# Per-tool configuration
@trace_mcp_tool("sensitive_tool", capture_input=False)
async def handle_sensitive_tool(...):
    # Input data not logged to Langfuse
    pass
```

---

## 🧪 Testing Strategy

### **Unit Tests** (tests/test_langfuse_tracer.py)

#### **Test 1: Decorator Functionality**
- Verify decorator wraps function without changing behavior
- Ensure trace_id is accessible in decorated function context
- Confirm original function return value preserved

#### **Test 2: Observation Creation**
- Mock coaia_fuse_add_observation calls
- Verify correct parameters passed (trace_id, observation structure)
- Test input_data/output_data population

#### **Test 3: Score Helpers**
- Mock coaia_fuse_score_create calls
- Verify score names and values calculated correctly
- Test latency, quality, success, cost scores

#### **Test 4: Error Handling**
- Simulate Langfuse unavailable (timeout)
- Verify execution continues successfully
- Confirm warning logged but no exception raised

#### **Test 5: Parent-Child Traces**
- Create parent trace, then child traces
- Verify parent_trace_id correctly propagated
- Test trace hierarchy retrieval

#### **Test 6: Performance**
- Measure decorator overhead with mocked Langfuse calls
- Verify total overhead <100ms
- Test async execution doesn't block main thread

---

## 📋 Implementation Checklist

### **Phase 1: Core Infrastructure** (60 min)
- [ ] Create `src/agentic_flywheel/integrations/__init__.py`
- [ ] Create `src/agentic_flywheel/integrations/langfuse_tracer.py`
- [ ] Implement `LangfuseTracerManager` class
- [ ] Implement `@trace_mcp_tool` decorator
- [ ] Add async context management for trace_id

### **Phase 2: Observation Helpers** (30 min)
- [ ] Implement `LangfuseObservation.add_intent_classification()`
- [ ] Implement `LangfuseObservation.add_flow_selection()`
- [ ] Implement `LangfuseObservation.add_execution()`
- [ ] Implement `LangfuseObservation.add_error()`

### **Phase 3: Score Helpers** (20 min)
- [ ] Implement `LangfuseScore.add_quality_score()`
- [ ] Implement `LangfuseScore.add_latency_score()`
- [ ] Implement `LangfuseScore.add_success_score()`
- [ ] Implement `LangfuseScore.add_cost_score()`

### **Phase 4: Testing** (45 min)
- [ ] Write unit tests for decorator
- [ ] Write unit tests for observations
- [ ] Write unit tests for scores
- [ ] Write integration test (mock MCP server)
- [ ] Achieve >80% coverage

### **Phase 5: Documentation** (15 min)
- [ ] Add docstrings to all public methods
- [ ] Create usage examples
- [ ] Document environment variables
- [ ] Update README with tracing section

---

## 🎯 Success Metrics

### **Functional Success**
- ✅ Decorator adds <100ms overhead to MCP tool calls
- ✅ All key decision points captured in observations
- ✅ Traces viewable in Langfuse UI with complete data
- ✅ System continues working when Langfuse unavailable
- ✅ No exceptions propagate from tracing code

### **User Experience Success**
- ✅ Users can see full decision path for any query
- ✅ Performance bottlenecks identifiable via latency scores
- ✅ Quality trends visible over time (improving/degrading)
- ✅ Error patterns diagnosable via error observations
- ✅ Zero configuration needed beyond Langfuse credentials

### **Integration Success**
- ✅ Existing MCP tools work unchanged after adding decorator
- ✅ New tools can add observations without boilerplate
- ✅ Trace hierarchy reflects actual execution flow
- ✅ coaia_fuse_* tools called correctly via coaiapy-mcp

---

## 🔮 Future Enhancements

### **Phase 2: Advanced Observability**
- Automatic quality scoring via LLM evaluation
- Cost tracking with per-flow token counting
- A/B testing support (trace variant decisions)
- Human-in-loop feedback UI integration

### **Phase 3: Learning Loops**
- Pattern detection (recurring successful flows)
- Automated flow optimization suggestions
- Confidence interval tracking (decision uncertainty)
- Feedback-driven flow ranking

---

## 📚 Dependencies

### **Runtime Dependencies**
- `coaiapy-mcp` - Provides coaia_fuse_* MCP tools
- `langfuse` - Langfuse Python SDK (optional, coaiapy-mcp wraps this)
- `mcp` - Model Context Protocol SDK

### **Development Dependencies**
- `pytest` - Unit testing framework
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking Langfuse calls
- `pytest-cov` - Coverage reporting

---

## 🌟 Alignment with RISE Principles

### **Reverse-Engineering**:
This spec reverse-engineers successful creative archaeology patterns from coaia-fuse guidance and real-world tracing needs.

### **Intent-Extraction**:
The intent is **transparent observability** — users want to *understand* and *improve* their AI orchestration, not just use it.

### **Specification**:
This document provides implementation-agnostic patterns. Another LLM could implement from this spec alone.

### **Export**:
The tracer module exports clean, composable primitives (`@trace_mcp_tool`, `LangfuseObservation`, `LangfuseScore`) that integrate naturally with existing code.

---

## ✨ Creative Advancement Scenario

**Before Tracing** (Current Reality):
> User: "Why did the system choose the Faith2Story flow for my creative question?"
> System: *Cannot answer — no record of decision process*

**After Tracing** (Desired Outcome):
> User: "Why did the system choose the Faith2Story flow for my creative question?"
> System: *Shows Langfuse trace with:*
> - Intent classification: "spiritual-creative" (confidence: 0.87)
> - Keyword matches: ["faith", "story", "create"]
> - Flow selection reasoning: "Faith2Story scored highest (0.92) for spiritual-creative intent"
> - Alternative flows considered: csv2507 (0.75), technical-analysis (0.23)

**The Gap**: Between "working system" and "understandable system" — tracing bridges this gap naturally.

---

**Specification Complete** ✅
**Ready for Implementation**: `src/agentic_flywheel/integrations/langfuse_tracer.py`
**Integration Target**: All MCP servers in agentic_flywheel
**Creative Outcome**: Users create complete archaeological records of their AI orchestration journeys
