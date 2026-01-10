# Task 2: Langfuse Tracing Integration

**Task ID**: `langfuse-tracer`
**Priority**: HIGH
**Orchestration Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Parent Trace**: `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`
**Estimated Duration**: 2-3 hours
**Complexity**: Medium

---

## Your Mission

You are implementing **Langfuse tracing integration** that enables complete creative archaeology of all Agentic Flywheel MCP operations.

**What Users Want to Create**:
- Complete record of every AI interaction for learning and improvement
- Full decision tree visibility (intent → flow selection → execution → quality)
- Historical patterns analysis for optimization
- Human-in-loop feedback via Langfuse comments

**Your Deliverables**:
1. ✅ **RISE Specification**: `rispecs/integrations/langfuse_tracer.spec.md`
2. ✅ **Implementation**: `src/agentic_flywheel/integrations/langfuse_tracer.py`
3. ✅ **Module Init**: `src/agentic_flywheel/integrations/__init__.py`
4. ✅ **Unit Tests**: `tests/test_langfuse_tracer.py`
5. ✅ **Result File**: `a66f8bd2-29f5-461d-ad65-36b65252d469/results/02_langfuse_tracer_COMPLETE.md`

---

## Context You Need

### coaiapy-mcp Integration

The ecosystem already has **Langfuse MCP tools** via `coaiapy-mcp` package:

**Available MCP Tools** (you'll integrate with these):
- `coaia_fuse_trace_create` - Create new Langfuse trace
- `coaia_fuse_add_observation` - Add execution step observation
- `coaia_fuse_score_create` - Add quality/performance score
- `coaia_fuse_comments_create` - Add human feedback comment
- `coaia_fuse_trace_get` - Retrieve trace information

**Integration Pattern**: Your tracer wraps these MCP tools, making tracing transparent to MCP server implementations.

### Where Tracing Happens

**MCP Server Files** (you'll provide decorators for these):
- `src/agentic_flywheel/mcp_server.py` - Basic MCP server with 7 tools
- `src/agentic_flywheel/intelligent_mcp_server.py` - Admin-aware server
- Future: `universal_mcp_server.py` - Comprehensive server with 25+ tools

**Key Methods to Trace**:
```python
@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    # This is where tracing should wrap execution
    pass
```

### Existing Guidance

**File**: `__llms/llms-coaia-fuse-guidance.md`

This contains patterns for:
- Creating traces with metadata
- Adding observations at key execution points
- Capturing scores for quality metrics
- Structuring traces for multi-step workflows

---

## Your Implementation Strategy

### Step 1: Create RISE Specification (30 min)

**File**: `rispecs/integrations/langfuse_tracer.spec.md`

**Required Sections**:
1. **Desired Outcome Definition** - What users create with full observability
2. **Current Structural Reality** - Ephemeral executions, no trace history
3. **Structural Tension** - Gap between transient and observable
4. **Natural Progression Patterns** - How tracing emerges naturally
5. **Tracing Architecture** - Decorator pattern, observation points, score helpers
6. **Integration Points** - Where in MCP server lifecycle to inject tracing
7. **Trace Hierarchy** - Parent/child relationships for complex workflows
8. **Error Handling** - Graceful degradation if Langfuse unavailable

**RISE Principles**:
- Focus on **creative archaeology** users want to create
- Use **natural emergence** of tracing from structural dynamics
- Make it **opt-in and fail-safe** (never break MCP server if tracing fails)

### Step 2: Implement Tracing Module (60-90 min)

**File**: `src/agentic_flywheel/integrations/langfuse_tracer.py`

**Core Components**:

#### 2.1 Trace Decorator
```python
def trace_mcp_tool(tool_name: str):
    """Decorator that automatically traces MCP tool execution"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Create Langfuse trace via coaia_fuse_trace_create
            # 2. Execute original function
            # 3. Add observation with execution details
            # 4. Add performance score
            # 5. Handle errors gracefully
            pass
        return wrapper
    return decorator
```

#### 2.2 Observation Helpers
```python
class LangfuseObservation:
    """Helper for adding structured observations to traces"""

    @staticmethod
    async def add_intent_classification(trace_id: str, intent: str, confidence: float):
        """Add observation for intent classification decision"""
        pass

    @staticmethod
    async def add_flow_selection(trace_id: str, flow_id: str, flow_name: str, backend: str):
        """Add observation for flow selection"""
        pass

    @staticmethod
    async def add_execution(trace_id: str, input_data: Any, output_data: Any, duration: float):
        """Add observation for flow execution"""
        pass
```

#### 2.3 Score Helpers
```python
class LangfuseScore:
    """Helper for adding quality/performance scores"""

    @staticmethod
    async def add_quality_score(trace_id: str, score: float, reasoning: str):
        """Add score for response quality"""
        pass

    @staticmethod
    async def add_latency_score(trace_id: str, duration_ms: float):
        """Add score for execution performance"""
        pass

    @staticmethod
    async def add_success_score(trace_id: str, success: bool, error: Optional[str] = None):
        """Add score for execution success/failure"""
        pass
```

#### 2.4 Tracer Manager
```python
class LangfuseTracerManager:
    """Manages Langfuse tracing lifecycle and configuration"""

    def __init__(self, enabled: bool = True, parent_trace_id: Optional[str] = None):
        self.enabled = enabled
        self.parent_trace_id = parent_trace_id
        self._active_traces = {}

    async def create_trace(self, name: str, metadata: Dict = None) -> str:
        """Create new trace or child trace"""
        pass

    async def get_trace(self, trace_id: str) -> Dict:
        """Retrieve trace information"""
        pass

    async def end_trace(self, trace_id: str):
        """Mark trace as complete"""
        pass
```

### Step 3: Create Module Exports (5 min)

**File**: `src/agentic_flywheel/integrations/__init__.py`

```python
"""Integration modules for Agentic Flywheel"""

from .langfuse_tracer import (
    trace_mcp_tool,
    LangfuseObservation,
    LangfuseScore,
    LangfuseTracerManager
)

__all__ = [
    'trace_mcp_tool',
    'LangfuseObservation',
    'LangfuseScore',
    'LangfuseTracerManager'
]
```

### Step 4: Write Unit Tests (45-60 min)

**File**: `tests/test_langfuse_tracer.py`

**Test Coverage**:
- ✅ Trace decorator wraps functions correctly
- ✅ Observations added at key execution points
- ✅ Scores calculated and recorded appropriately
- ✅ Error handling (Langfuse unavailable, API failures)
- ✅ Parent/child trace relationships
- ✅ Graceful degradation (tracing fails, MCP tool still works)

**Use mocks** for `coaia_fuse_*` MCP tool calls.

### Step 5: Create Result File (10 min)

**File**: `a66f8bd2-29f5-461d-ad65-36b65252d469/results/02_langfuse_tracer_COMPLETE.md`

---

## Integration Contract

Your tracing module **must**:
1. ✅ **Be optional** - MCP server works without tracing configured
2. ✅ **Fail gracefully** - Tracing errors don't crash MCP tools
3. ✅ **Use coaia-mcp tools** - Don't implement direct Langfuse SDK calls
4. ✅ **Support async** - All tracing functions are `async def`
5. ✅ **Provide decorators** - Easy to wrap existing MCP tool handlers
6. ✅ **Capture key events**:
   - Intent classification decision
   - Flow selection logic
   - Execution input/output
   - Performance metrics
   - Error conditions

**Example Usage** (how MCP server will use your tracer):
```python
from agentic_flywheel.integrations import trace_mcp_tool, LangfuseObservation, LangfuseScore

@app.call_tool()
@trace_mcp_tool("flowise_query")
async def handle_flowise_query(name: str, arguments: dict):
    trace_id = get_current_trace_id()  # From decorator context

    # Classify intent
    intent = classify_intent(arguments["question"])
    await LangfuseObservation.add_intent_classification(trace_id, intent, 0.95)

    # Select flow
    flow = select_flow(intent)
    await LangfuseObservation.add_flow_selection(trace_id, flow.id, flow.name, "flowise")

    # Execute
    start = time.time()
    result = await execute_flow(flow, arguments["question"])
    duration = time.time() - start

    await LangfuseObservation.add_execution(trace_id, arguments["question"], result, duration)
    await LangfuseScore.add_latency_score(trace_id, duration * 1000)

    return result
```

---

## Trace Structure to Create

For a typical query execution, your tracer should create this structure in Langfuse:

```
Trace: "flowise_query: What is structural tension?"
├─ Observation: Intent Classification
│  └─ Output: "creative-orientation" (confidence: 0.95)
├─ Observation: Flow Selection
│  └─ Output: "csv2507 - Creative Orientation" (backend: flowise)
├─ Observation: Flow Execution
│  ├─ Input: "What is structural tension?"
│  ├─ Output: "Structural tension is..."
│  └─ Duration: 1.2s
├─ Score: Quality (0.9) - "Response addresses core concept"
├─ Score: Latency (1200ms) - Performance metric
└─ Score: Success (1.0) - Execution completed
```

---

## Resources Available

### Code References
- `src/agentic_flywheel/mcp_server.py` - MCP tools to instrument
- `src/agentic_flywheel/intelligent_mcp_server.py` - Admin-aware server
- `src/agentic_flywheel/flowise_manager.py` - Flow execution logic

### Documentation
- `__llms/llms-coaia-fuse-guidance.md` - Langfuse tracing patterns
- `__llms/llms-coaiapy-mcp-config-guide.md` - MCP tool usage
- `rispecs/app.spec.md` - Master spec with tracing scenarios

### coaia-mcp Tools You'll Use
```bash
# These tools are available via coaiapy-mcp server
coaia_fuse_trace_create --name "..." --metadata {...}
coaia_fuse_add_observation --trace_id "..." --content {...}
coaia_fuse_score_create --trace_id "..." --name "..." --value 0.9
```

---

## Success Criteria

You'll know you're successful when:
1. ✅ **Transparent tracing** - Decorator adds tracing without modifying tool logic
2. ✅ **Complete archaeology** - All decision points captured in observations
3. ✅ **Fail-safe** - Tracing failures don't impact MCP tool execution
4. ✅ **Performance acceptable** - Tracing adds <100ms overhead
5. ✅ **Hierarchical traces** - Parent/child relationships clear
6. ✅ **Rich metadata** - Scores provide actionable quality insights

---

## Questions to Answer in Your Spec

1. **Trace Lifecycle**: When to create trace (start of MCP tool call)? When to end (after response)?
2. **Observation Granularity**: What level of detail for observations? Too much = noise, too little = gaps
3. **Score Semantics**: What scores are most valuable? Quality, latency, success, cost?
4. **Error Tracing**: How to represent failed executions in Langfuse?
5. **Async Handling**: How to ensure trace operations don't block MCP tool responses?
6. **Configuration**: How users enable/disable tracing? Environment variables? Config file?

**Document your answers** in the spec with reasoning.

---

## Final Notes

**Creative Archaeology**: This tracing enables users to understand their AI interactions over time, identifying patterns and improving quality.

**Structural Tension**: The gap between "ephemeral executions" and "observable journeys" creates natural advancement toward tracing.

**Integration Point**: Your tracer is the bridge between MCP tool execution and Langfuse observability platform.

---

**Ready to Create?** Start with the RISE spec to define the observability outcomes users want, then implement the tracing infrastructure that emerges naturally.

**Orchestrator Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Your Task**: Enabling users to create complete creative archaeology of their AI workflows
**Your Creative Freedom**: Complete

🚀 **Begin when ready!**
