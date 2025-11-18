# Agentic Flywheel MCP: Parallel Development Workspace

**Session ID**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Parent Trace**: `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`
**Created**: 2025-11-18
**Status**: 🌱 **READY FOR SUBAGENT DELEGATION**

---

## What This Workspace Contains

This workspace orchestrates **parallel development** of the Agentic Flywheel MCP, enabling it to work with both **Langflow** and **Flowise** platforms, with **Langfuse tracing** and **Redis persistence**.

### 📁 Directory Structure

```
a66f8bd2-29f5-461d-ad65-36b65252d469/
├── README.md                    # This file
├── ORCHESTRATION.md             # Orchestration strategy and progress tracking
├── subagents/                   # Starter prompts for each task
│   ├── 01_langflow_backend_task.md        # Langflow backend adapter
│   ├── 02_langfuse_tracer_task.md         # Langfuse tracing integration
│   ├── 03_redis_state_task.md             # Redis state persistence
│   ├── 04_universal_query_task.md         # Universal query MCP tool
│   ├── 05_backend_tools_task.md           # 6 backend management tools
│   └── 06_admin_tools_task.md             # 6 admin intelligence tools
├── results/                     # Completion signals from subagents
│   └── (subagents create files here when done)
├── integration/                 # Cherry-picked work ready for merge
│   └── (orchestrator places reviewed code here)
└── specs/                       # Gathered specifications
    └── (orchestrator collects completed specs here)
```

---

## How to Use This Workspace

### For the Orchestrator (Current Session)

**Your Role**: Coordinate parallel development, review results, integrate code

**Workflow**:
1. ✅ **Launch subagents** - Start new Claude sessions with task prompts
2. 🔄 **Monitor progress** - Check `results/` directory for completion signals
3. 👁️ **Review work** - Read specs and code from completed tasks
4. 🍒 **Cherry-pick** - Merge reviewed work into main branch
5. 📊 **Update tracking** - Update `ORCHESTRATION.md` progress table
6. 🔗 **Trace everything** - Add observations to Langfuse parent trace

**Commands to Launch Subagents**:
```bash
# In new terminal/session, launch Claude with task prompt:
claude --session-id <new-session-id> < subagents/01_langflow_backend_task.md

# Or manually copy/paste task prompt into new Claude session
```

---

### For Subagents (New Claude Sessions)

**Your Role**: Implement your assigned component following RISE principles

**Workflow**:
1. 📖 **Read your task prompt** - In `subagents/<task-id>_task.md`
2. 🎯 **Create RISE spec** - Define desired outcomes and structural dynamics
3. 💻 **Implement** - Write code following integration contract
4. ✅ **Test** - Write and run unit tests
5. 📝 **Document completion** - Create result file in `results/` directory
6. 📤 **Signal orchestrator** - Result file is your completion signal

**Completion Signal Format**:
```bash
# Create this file when done:
results/<task-id>_COMPLETE.md

# With status:
Status: COMPLETE / BLOCKED / NEEDS_REVIEW

# And integration notes for orchestrator
```

---

## The 6 Parallel Tasks

### Task 1: Langflow Backend Adapter
**Priority**: HIGH | **Complexity**: Medium | **Duration**: 3-4 hours

**Deliverables**:
- RISE spec for Langflow integration
- `LangflowBackend` class implementing `FlowBackend` interface
- Unit tests with 80%+ coverage

**Why It Matters**: Enables multi-backend orchestration (Langflow + Flowise)

**Starter Prompt**: `subagents/01_langflow_backend_task.md`

---

### Task 2: Langfuse Tracing Integration
**Priority**: HIGH | **Complexity**: Medium | **Duration**: 2-3 hours

**Deliverables**:
- RISE spec for observability
- Tracer decorators and observation helpers
- Integration with coaia-mcp tools

**Why It Matters**: Enables complete creative archaeology of all workflows

**Starter Prompt**: `subagents/02_langfuse_tracer_task.md`

---

### Task 3: Redis State Persistence
**Priority**: MEDIUM | **Complexity**: Low-Medium | **Duration**: 2-3 hours

**Deliverables**:
- RISE spec for persistent memory
- Session state manager using coaia_tash/fetch
- TTL and key management

**Why It Matters**: Enables cross-session conversation continuity

**Starter Prompt**: `subagents/03_redis_state_task.md`

---

### Task 4: Universal Query MCP Tool
**Priority**: HIGH | **Complexity**: Medium-High | **Duration**: 3-4 hours

**Deliverables**:
- RISE spec for universal querying
- Intelligent routing algorithm
- MCP tool implementation pattern

**Why It Matters**: Primary user-facing interface for multi-backend queries

**Starter Prompt**: `subagents/04_universal_query_task.md`

---

### Task 5: Backend Management Tools
**Priority**: MEDIUM | **Complexity**: Low-Medium | **Duration**: 2-3 hours

**Deliverables**:
- RISE spec for 6 backend tools
- Tool schemas and implementation patterns
- Registry integration

**Why It Matters**: Enables users to manage multi-backend infrastructure

**Starter Prompt**: `subagents/05_backend_tools_task.md`

---

### Task 6: Admin Intelligence Tools
**Priority**: LOW-MEDIUM | **Complexity**: Low | **Duration**: 2-3 hours

**Deliverables**:
- RISE spec for 6 admin tools
- MCP wrappers around existing flowise_admin/ layer
- Analytics and insights exposure

**Why It Matters**: Exposes existing analytics via MCP interface

**Starter Prompt**: `subagents/06_admin_tools_task.md`

---

## Integration Strategy

### Phase 1: Foundation (Tasks 1-3)
**Can Run in Parallel**: Yes (all independent)

**Integration Order**:
1. Langflow Backend (enables multi-backend)
2. Langfuse Tracer (enables observability)
3. Redis State (enables persistence)

**Estimated Time**: 3-4 hours parallel (9-12 hours serial)

---

### Phase 2: Core Tools (Task 4)
**Depends On**: Task 1 (Langflow backend)

**Can Use Mocks**: Yes, initially

**Estimated Time**: 3-4 hours

---

### Phase 3: Enhanced Tools (Tasks 5-6)
**Depends On**: Phase 1 complete

**Can Run in Parallel**: Yes (independent)

**Estimated Time**: 2-3 hours parallel (4-6 hours serial)

---

## Success Metrics

### Individual Task Success
- ✅ RISE specification complete and autonomous
- ✅ Implementation follows structural dynamics
- ✅ Unit tests pass with >80% coverage
- ✅ Integration contract fulfilled
- ✅ Result file created with clear notes

### Overall Integration Success
- ✅ All 6 tasks completed
- ✅ End-to-end tests pass (4 creative advancement scenarios)
- ✅ Langflow backend routes queries successfully
- ✅ Langfuse traces capture full execution paths
- ✅ Redis state persists across sessions
- ✅ 25+ MCP tools operational

---

## Communication Protocol

### Orchestrator → Subagent
**Channel**: Task prompt file in `subagents/`
**Format**: Comprehensive markdown with context, contracts, resources

### Subagent → Orchestrator
**Channel**: Result file in `results/`
**Format**: Status, deliverables checklist, integration notes

### Cross-Subagent Communication
**Channel**: None (intentionally isolated)
**Note**: Dependencies handled by orchestrator integration phases

---

## Tracing Hierarchy

```
Parent: a50f3fc2-eb8c-434d-a37e-ef9615d9c07d
└─ Orchestration: a66f8bd2-29f5-461d-ad65-36b65252d469
   ├─ Task 1: Langflow Backend (subagent creates child trace)
   ├─ Task 2: Langfuse Tracer (subagent creates child trace)
   ├─ Task 3: Redis State (subagent creates child trace)
   ├─ Task 4: Universal Query (subagent creates child trace)
   ├─ Task 5: Backend Tools (subagent creates child trace)
   └─ Task 6: Admin Tools (subagent creates child trace)
```

Each subagent should create their own Langfuse trace as a child of the orchestration session for complete creative archaeology.

---

## Quick Start for Orchestrator

**Step 1**: Launch subagent sessions
```bash
# Option A: Sequential launch
for task in subagents/*.md; do
  echo "Launch new Claude session with: $task"
  # Start new session, paste task content
done

# Option B: Parallel launch (recommended)
# Start 6 Claude sessions, assign one task each
```

**Step 2**: Monitor progress
```bash
# Watch for completion signals
watch -n 30 'ls -l results/'

# Or check periodically
ls results/*_COMPLETE.md
```

**Step 3**: Review and integrate
```bash
# For each completed task:
1. Read results/<task-id>_COMPLETE.md
2. Review code and specs
3. Run tests
4. Cherry-pick to integration/
5. Update ORCHESTRATION.md progress
6. Add Langfuse observation
```

---

## Quick Start for Subagents

**Step 1**: Read your assigned task
```bash
# Your orchestrator will give you one of:
subagents/01_langflow_backend_task.md    # Langflow backend
subagents/02_langfuse_tracer_task.md     # Tracing
subagents/03_redis_state_task.md         # Persistence
subagents/04_universal_query_task.md     # Universal query
subagents/05_backend_tools_task.md       # Backend tools
subagents/06_admin_tools_task.md         # Admin tools
```

**Step 2**: Create your RISE spec
```bash
# Start with specification following RISE principles
# Document in rispecs/<component>/<name>.spec.md
```

**Step 3**: Implement following contracts
```bash
# Your task prompt contains:
- Integration contracts (what you must provide)
- Example usage (how orchestrator will use your code)
- Resources available (what you can read/use)
```

**Step 4**: Test thoroughly
```bash
# Write unit tests with >80% coverage
pytest tests/test_<your_component>.py -v --cov
```

**Step 5**: Signal completion
```bash
# Create result file
results/<task-id>_COMPLETE.md

# With:
- Status: COMPLETE
- Deliverables checklist (all ✅)
- Integration notes
- Any known issues
```

---

## FAQs

**Q: Can subagents talk to each other?**
A: No - intentionally isolated for parallel execution. Orchestrator handles dependencies.

**Q: What if my task is blocked on another task?**
A: Mark status as `BLOCKED` in result file, describe dependency, orchestrator will handle.

**Q: Can I modify existing code?**
A: Only your assigned component. Integration contracts define boundaries.

**Q: How do I test without real Langflow/Redis/Langfuse?**
A: Use mocks! Your task prompt includes mock guidance.

**Q: What if I disagree with the task approach?**
A: Document alternative in your RISE spec with reasoning. RISE principles allow creative freedom.

**Q: How detailed should my RISE spec be?**
A: Detailed enough that another LLM could implement from your spec alone (implementation-agnostic).

---

## Resources

### Documentation
- `rispecs/app.spec.md` - Master RISE specification
- `__llms/llms-rise-framework.txt` - RISE framework principles
- `__llms/llms-coaia-fuse-guidance.md` - Langfuse tracing patterns
- `__llms/llms-coaiapy-cli-guide.md` - coaiapy tool usage

### Code References
- `src/agentic_flywheel/` - Current codebase
- `src/agentic_flywheel/backends/base.py` - Universal backend interface
- `src/agentic_flywheel/PLAN_BACKEND_MIGRATION_250929.md` - Migration roadmap

---

## Status Summary

**Workspace**: ✅ Ready
**Task Prompts**: ✅ All 6 created
**Subagents**: 🌱 Awaiting launch
**Progress**: 0/6 tasks complete

**Next Action**: Launch subagent sessions with task prompts

---

**Orchestrator**: Standing by for subagent completion signals
**Creative Journey**: Let the structural dynamics guide implementation
**Outcome**: Multi-backend AI workflow orchestration with full observability

🚀 **Ready for parallel development!**
