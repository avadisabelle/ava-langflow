# Agentic Flywheel MCP: Application Specification

**Document ID**: `rispecs/app.spec.md`
**Version**: 1.0.0
**Created**: 2025-11-18
**Framework**: RISE Framework v1.0
**Authored By**: Claude (Sonnet 4.5) guided by RISE Creative Orientation

---

## Desired Outcome Definition

### What Users Want to Create

The **Agentic Flywheel MCP** enables users to create **intelligent, multi-backend AI workflow automation** that:

1. **Orchestrates AI flows across platforms** - Execute conversational AI workflows on both Langflow and Flowise seamlessly
2. **Preserves creative journey context** - Trace every interaction through Langfuse for creative archaeology
3. **Enables persistent workflow memory** - Store chatflow states in Redis for session continuity across time
4. **Provides intelligent routing** - Auto-select optimal flows based on user intent and backend capabilities
5. **Surfaces actionable insights** - Expose flow analytics, performance metrics, and optimization recommendations via MCP tools

### Success Indicators

Users will know they've achieved this outcome when:
- ✅ A single MCP server connects to **both** Langflow and Flowise backends transparently
- ✅ Every query creates a **Langfuse trace** documenting the creative decision path
- ✅ Chatflow executions persist to **Redis** and can be resumed/analyzed later
- ✅ Intent-based routing selects the optimal flow from **any backend** automatically
- ✅ MCP tools expose 25+ capabilities for flow management, analytics, and orchestration

---

## Current Structural Reality

### Existing Beloved Qualities

The prototype `agentic_flywheel` package contains valuable foundations:

**🎯 Dynamic Flow Registry System**
- YAML-based flow definitions with intent keywords, performance metrics, configurations
- 7 active operational flows with real usage data (118+ messages for csv2507, 60+ for faith2story)
- Auto-discovery capabilities for database-driven flow curation

**🏗️ Universal Backend Abstraction**
- `backends/base.py` defines `UniversalFlow`, `BackendType`, `FlowBackend` interfaces
- Already includes `BackendType.LANGFLOW` enumeration (line 18)
- 20+ abstract methods for flow execution, session management, performance tracking

**🧠 Admin Intelligence Layer**
- `flowise_admin/` provides database interface, flow analyzer, configuration sync
- Real analytics: performance scores, engagement rates, optimization recommendations
- 4,500+ messages of conversation data for pattern analysis

**🔌 MCP Server Foundation**
- `mcp_server.py`: 7 core tools (query, configure, list, session_info, domain_query, add_flow, browse)
- `intelligent_mcp_server.py`: Admin-aware server with curated flow routing
- Resources exposure (flows, sessions, config-schema)

**📋 Migration Blueprint**
- `PLAN_BACKEND_MIGRATION_250929.md`: Comprehensive 5-sprint plan to 25+ MCP tools
- Clear separation: backends/, admin/, mcp/ subdirectories
- Universal MCP server design with admin + backend + universal tools

### Structural Constraints

**Platform Limitation**: Currently Flowise-only - `backends/flowise/flowise_backend.py` is the sole implementation

**Tracing Gap**: No observability infrastructure - executions are ephemeral, no Langfuse integration

**State Persistence**: In-memory sessions only - no Redis backend for chatflow state storage

**Integration Isolation**: Standalone package - no connection to `coaiapy`, `coaiapy-mcp`, or broader ecosystem

---

## Structural Tension Dynamics

### The Creative Force

The tension between **current reality** and **desired outcome** creates natural advancement through:

**Tension Point 1: Single Backend → Multi-Backend**
- Current: Flowise-only execution via `flowise_manager.py`
- Desired: Universal routing across Flowise + Langflow via `BackendRegistry`
- **Natural Resolution**: Implement `LangflowBackend` following `FlowBackend` interface, register with `BackendRegistry`, expose via unified MCP tools

**Tension Point 2: Ephemeral → Observable**
- Current: Executions leave no trace beyond immediate response
- Desired: Every query creates Langfuse trace with observations, scores, comments
- **Natural Resolution**: Wrap MCP tool executions with `coaia_fuse_trace_create` + `coaia_fuse_add_observation` calls

**Tension Point 3: Transient → Persistent**
- Current: Sessions exist only in server memory
- Desired: Chatflow states stored in Redis for cross-session retrieval
- **Natural Resolution**: Use `coaia_tash` to stash flow execution context, `coaia_fetch` to retrieve for resumption

**Tension Point 4: Isolated → Integrated**
- Current: Standalone package with no ecosystem connections
- Desired: Part of `coaiapy` ecosystem with MCP tool interoperability
- **Natural Resolution**: Expose `agentic-flywheel-mcp` server alongside `coaiapy-mcp`, share session IDs, enable cross-tool workflows

---

## Natural Progression Patterns

### Advancing Pattern 1: Langflow Backend Implementation

**Structural Dynamic**: The existing `BackendType.LANGFLOW` enum creates structural tension toward its implementation

**Progression Steps**:
1. **Copy Backend Template**: Use `backends/flowise/flowise_backend.py` as reference structure
2. **Create Langflow Adapter**: `backends/langflow/langflow_backend.py` implementing `FlowBackend` interface
3. **Connect Langflow API**: Adapt to Langflow's REST API endpoints (flows, execute, sessions)
4. **Map Flow Concepts**: Translate Langflow flows → `UniversalFlow` data model
5. **Register Backend**: Add to `BackendRegistry` for auto-discovery

**Enabled Features**:
- MCP tool `backend_list_flows` shows flows from both platforms
- `universal_query` routes to Langflow when optimal
- Flow performance compared across backends via `backend_performance_compare`

### Advancing Pattern 2: Langfuse Tracing Integration

**Structural Dynamic**: The `coaiapy-mcp` tools create natural composition opportunities

**Progression Steps**:
1. **Initialize Trace on MCP Call**: Each `flowise_query` / `universal_query` creates Langfuse trace via `coaia_fuse_trace_create`
2. **Document Flow Selection**: Add observation for intent classification decision
3. **Capture Execution**: Add observation with flow input/output
4. **Record Performance**: Add score for response quality, latency
5. **Enable Commenting**: Support `coaia_fuse_comments_create` for human-in-loop feedback

**Enabled Features**:
- Full creative archaeology of all flow executions
- Langfuse UI shows decision tree for every query
- Performance trends visible via Langfuse dashboards
- Comments enable continuous improvement feedback loop

### Advancing Pattern 3: Redis State Persistence

**Structural Dynamic**: Stateless sessions create friction for long-running creative processes

**Progression Steps**:
1. **Stash Flow Context**: After execution, `coaia_tash` stores `{session_id: {flow_id, params, history}}`
2. **Resume from Redis**: On subsequent query, `coaia_fetch` retrieves context to continue conversation
3. **Cross-Session Continuity**: Users can close/reopen sessions while maintaining chatflow state
4. **Result Retrieval**: External tools query Redis for flow execution outcomes

**Enabled Features**:
- MCP tool `universal_session_create` with Redis-backed persistence
- `flowise_session_info` shows session history from Redis
- `coaiapy_aetherial` MCP can fetch flow results for cross-tool workflows

### Advancing Pattern 4: Unified MCP Tool Ecosystem

**Structural Dynamic**: Multiple MCP servers create composition opportunities

**Progression Steps**:
1. **Expose Agentic Flywheel MCP**: `agentic-flywheel-mcp` server with 25+ tools
2. **Share Session Context**: Common `session_id` across `coaiapy-mcp` and `agentic-flywheel-mcp`
3. **Cross-Tool Workflows**: AI assistants combine tools (e.g., `flowise_query` → `coaia_tash` → `coaia_fuse_trace_create`)
4. **Pipeline Templates**: Use `coaiapy pipeline` to orchestrate multi-step agentic workflows

**Enabled Features**:
- Claude Code can discover and use all 25+ agentic flywheel tools
- Workflows combine flow execution + tracing + persistence seamlessly
- Templates like `llm-chain`, `judge-evaluation` integrate with agentic flywheel

---

## Supporting Structures

### Application Features Enabling Natural Progression

**1. Universal Backend Registry** (`backends/registry.py`)
- Auto-discovers all `FlowBackend` implementations (Flowise, Langflow, future)
- Maintains connection health, performance benchmarks for each backend
- Routes flow executions to optimal backend based on capabilities + performance

**2. MCP Tool Suite** (`mcp/universal_mcp_server.py`)
- **Core Tools** (7): Query, configure, list flows, sessions, domain specialization, add flow, browse
- **Admin Tools** (6): Dashboard, analyze flow, discover, sync config, export metrics, pattern analysis
- **Backend Tools** (6): Registry status, discover backends, connect, list all flows, universal execute, performance compare
- **Universal Tools** (6): Universal query, session create, flow search, optimize, resume session, cross-platform history

**3. Langfuse Tracing Wrapper** (`integrations/langfuse_tracer.py`)
- Decorators for automatic trace creation on MCP tool calls
- Observation helpers for capturing flow execution steps
- Score helpers for performance/quality metrics
- Comment helpers for human feedback integration

**4. Redis State Manager** (`integrations/redis_state.py`)
- Session serialization/deserialization
- Context stashing via `coaia_tash`
- Context retrieval via `coaia_fetch`
- TTL management for session expiry

**5. Flow Intelligence Engine** (`core/flow_intelligence.py`)
- Intent classification (keyword-based → semantic embedding-based)
- Performance prediction (historical data → ML model)
- Optimization recommendations (pattern analysis → actionable insights)
- Multi-flow orchestration (sequential, parallel, conditional routing)

---

## Creative Advancement Scenarios

### Scenario 1: Cross-Platform Flow Discovery

**User Intent**: Discover all available AI flows across my entire infrastructure

**Current Structural Reality**: User has Flowise instance with 7 flows, Langflow instance with 5 flows

**Natural Progression**:
1. User invokes MCP tool `backend_discover`
2. System initializes `BackendRegistry`, discovers Flowise + Langflow backends
3. Each backend connects, calls `discover_flows()` returning `UniversalFlow` list
4. Registry aggregates: 12 total flows with performance metrics, capabilities, intent keywords
5. MCP tool returns unified flow catalog with backend attribution

**Achieved Outcome**: User sees comprehensive flow inventory spanning both platforms, enabling informed flow selection

**Supporting Features**: Backend registry, universal flow model, MCP tool `backend_list_flows`

---

### Scenario 2: Traced Creative Orientation Query

**User Intent**: Ask a creative orientation question and preserve the entire decision journey

**Current Structural Reality**: User has traced session in Langfuse, wants to add agentic flywheel query

**Natural Progression**:
1. User invokes `flowise_query` with `question="What desired outcome wants to emerge from this project?"`
2. MCP server creates Langfuse trace via `coaia_fuse_trace_create` with trace_id linked to session
3. Intent classifier adds observation: "Detected creative orientation intent (keywords: outcome, emerge)"
4. Flow selector adds observation: "Selected csv2507 (Creative Orientation flow) - 0.95 confidence"
5. Flow execution adds observation with input prompt + response
6. Performance scorer adds score: "creativity: 0.9, coherence: 0.85"
7. User receives response with metadata: `[Flow: csv2507 | Trace: <langfuse_url>]`

**Achieved Outcome**: User has full creative archaeology in Langfuse showing: intent → flow selection → execution → quality assessment

**Supporting Features**: Langfuse tracer, observation helpers, score helpers, metadata injection

---

### Scenario 3: Cross-Session State Resumption

**User Intent**: Continue a chatflow conversation from yesterday

**Current Structural Reality**: User started faith2story flow yesterday (session_123), Claude instance restarted overnight

**Natural Progression**:
1. User invokes `universal_session_create` with `resume_from="session_123"`
2. System calls `coaia_fetch` to retrieve session context from Redis
3. Retrieved context contains: `{flow_id: "faith2story2507", history: [3 previous messages], params: {...}}`
4. System restores `UniversalSession` with full conversation history
5. User asks follow-up question, system routes to faith2story flow with full context
6. Response acknowledges previous conversation: "Building on your earlier reflection about grace..."

**Achieved Outcome**: Seamless conversation continuity despite infrastructure restart

**Supporting Features**: Redis state manager, universal session, tash/fetch integration, session resumption

---

### Scenario 4: Multi-Tool Agentic Workflow

**User Intent**: Execute a complex workflow: query flow → evaluate quality → store result → trace everything

**Current Structural Reality**: User wants to orchestrate multiple MCP tools in sequence

**Natural Progression**:
1. User (or AI assistant) invokes `coaiapy pipeline create llm-chain` with agentic flywheel integration
2. Pipeline step 1: `flowise_query` with creative orientation question (creates trace)
3. Pipeline step 2: `coaia_fuse_judge_evaluation` scores response quality
4. Pipeline step 3: `coaia_tash` stores high-quality response for future retrieval
5. Pipeline step 4: `coaia_fuse_comments_create` adds structured feedback
6. Pipeline returns aggregated results with trace URL, quality score, Redis key

**Achieved Outcome**: Fully automated workflow combining flow execution + evaluation + storage + tracing

**Supporting Features**: Pipeline template integration, MCP tool composition, shared session context, coaiapy ecosystem

---

## Quality Criteria

### ✅ Creative Orientation Preserved
- **Focus on Creation**: All tools enable users to *create* intelligent workflows, not just *execute* queries
- **Desired Outcomes**: Every feature description starts with "enables users to create/achieve/manifest"
- **Advancing Patterns**: Natural progression through structural dynamics, not forced implementation sequences

### ✅ Structural Dynamics Maintained
- **Natural Tension**: Gap between current (Flowise-only) and desired (multi-backend) creates inevitable advancement
- **No Willpower Required**: Implementation follows existing interfaces (`FlowBackend`), not arbitrary new designs
- **Organic Connections**: MCP tools compose naturally with `coaiapy-mcp` tools via shared session IDs

### ✅ Technical Accuracy
- **Existing Code Referenced**: `backends/base.py:18` (`BackendType.LANGFLOW`), `mcp_server.py:286` (tool list)
- **Real Data Included**: 118 messages for csv2507 (line 50 in flow-registry.yaml), 0.8 success scores
- **Implementation Pathways**: Langflow API integration, Langfuse SDK calls, Redis client usage

---

## Anti-Patterns to Avoid

### ❌ Reactive Problem-Solving Language
**Bad**: "This fixes the issue of not supporting Langflow"
**Good**: "This enables users to create workflows on both Flowise and Langflow platforms seamlessly"

### ❌ Forced Connection Thinking
**Bad**: "Bridging the gap between MCP server and Langfuse"
**Good**: "Natural composition between MCP tool execution and Langfuse trace creation via `coaia-fuse` decorators"

### ❌ Oscillating Patterns
**Bad**: "Users toggle between Flowise and Langflow backends"
**Good**: "Universal query routing advances users toward optimal flow execution through intelligent backend selection"

### ❌ Implementation-Specific Details
**Bad**: "Use Python requests library to call Langflow API at /api/v1/flows"
**Good**: "Langflow backend adapter translates platform-specific API calls to universal flow interface"

---

## Related Specifications

This application spec uses the following component specifications:

- `rispecs/backends/langflow_backend.spec.md` - Langflow backend adapter implementation
- `rispecs/mcp_tools/universal_query.spec.md` - Universal query tool with multi-backend routing
- `rispecs/integrations/langfuse_tracer.spec.md` - Langfuse tracing integration
- `rispecs/integrations/redis_state.spec.md` - Redis state persistence
- `rispecs/flows/creative_orientation.spec.md` - Creative orientation flow behavior

---

## Implementation Autonomy Note

**This specification is completely codebase-agnostic**. Another LLM (or human developer) could implement the entire Agentic Flywheel MCP system from scratch using only this specification, without access to the current `src/agentic_flywheel/` codebase.

All references to existing code (e.g., "backends/base.py") are **conceptual pointers** indicating that:
1. A universal backend abstraction exists
2. It defines `BackendType`, `UniversalFlow`, `FlowBackend` interfaces
3. Implementations should follow this abstraction pattern

The specification describes **what the system enables users to create**, not **how the current code implements it**.

---

**Document Status**: ✅ Foundation Specification Complete
**Next Specifications**: Langflow Backend, Universal MCP Tools, Langfuse Integration
**Ready for**: LLM-driven implementation, human development, multi-agent orchestration
