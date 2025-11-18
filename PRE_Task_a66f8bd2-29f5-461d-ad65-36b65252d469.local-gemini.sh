#!/bin/bash
# PRE_Task launcher for Gemini CLI to assist with Agentic Flywheel MCP parallel development
# Session: a66f8bd2-29f5-461d-ad65-36b65252d469
# Parent Trace: a50f3fc2-eb8c-434d-a37e-ef9615d9c07d

_GEMINII_DEFAULT_MODEL_set pro

geminiid "
# 🎯 Agentic Flywheel MCP: Gemini Assistant Context

## Your Mission
You are assisting with parallel development of the **Agentic Flywheel MCP**, enabling multi-backend AI workflow orchestration (Langflow + Flowise) with Langfuse tracing and Redis persistence.

---

## What Claude Online Has Prepared

**Workspace Location**: @a66f8bd2-29f5-461d-ad65-36b65252d469

Claude has created a comprehensive orchestration workspace with:

### ✅ Completed Foundations
1. **RISE Foundation Spec** (\`rispecs/app.spec.md\`)
   - 355 lines of implementation-agnostic specification
   - Defines desired outcomes: multi-backend orchestration, observability, persistence
   - 4 structural tensions driving natural advancement
   - 4 creative advancement scenarios

2. **Parallel Development Workspace** (\`a66f8bd2-29f5-461d-ad65-36b65252d469/\`)
   - **6 Starter Prompts** ready for delegation:
     - Task 1: Langflow Backend Adapter (HIGH, 3-4h)
     - Task 2: Langfuse Tracing Integration (HIGH, 2-3h)
     - Task 3: Redis State Persistence (MEDIUM, 2-3h)
     - Task 4: Universal Query MCP Tool (HIGH, 3-4h)
     - Task 5: Backend Management Tools (MEDIUM, 2-3h)
     - Task 6: Admin Intelligence Tools (LOW-MEDIUM, 2-3h)
   - **Orchestration Protocol** documented
   - **Integration Strategy** defined (3 phases)
   - **Success Criteria** established

---

## 🎯 PRIORITY FIRST ACTIONS

Since you have access to paths Claude doesn't, **start by gathering context**:

1. **📥 Copy IAIP Directions** → Store in workspace specs/
2. **📥 Copy Mia Agents** → Store in workspace specs/mia_agents/
3. **📥 Copy Claude Embodiments** → Store in workspace specs/
4. **📝 Create GEMINI.md** → Document your observations
5. **🔬 Then choose**: Implementation | Research | Coordination

This context will help both you and Claude with the implementation tasks.

---

## Your Potential Contributions

### 🔧 Immediate Tasks You Could Help With

**Option 1: Start a Subagent Task**
Pick one of the 6 tasks from \`a66f8bd2-29f5-461d-ad65-36b65252d469/subagents/\` and begin implementation:
- Read the starter prompt (comprehensive context provided)
- Create the RISE specification
- Implement following integration contracts
- Signal completion via results/ directory

**Recommended for Gemini**: **Task 1 (Langflow Backend)** or **Task 4 (Universal Query)**

**Option 2: Create Observability Documentation**
- Create **GEMINI.md** in the workspace documenting:
  - Your observations of the parallel development process
  - Integration patterns you notice
  - Optimization opportunities
  - Creative insights for the team

**Option 3: Research Langflow API**
- Investigate Langflow's REST API structure
- Document endpoints, authentication, response formats
- Create API mapping guide for Task 1 implementation
- Store findings in \`a66f8bd2-29f5-461d-ad65-36b65252d469/specs/langflow_api_research.md\`

**Option 4: Gather Context from IAIP and Mia Agents**
You have access to valuable context directories that Claude doesn't. Gather and store:

**IAIP Directions** (\`/src/IAIP/directions/\`):
\\\`\\\`\\\`bash
# Copy IAIP direction context into workspace
cp -r /src/IAIP/directions/ a66f8bd2-29f5-461d-ad65-36b65252d469/specs/iaip_directions/

# Document current direction (EAST) and SOUTH adequacy
cat /src/IAIP/directions/EAST.md > a66f8bd2-29f5-461d-ad65-36b65252d469/specs/current_direction_EAST.md
cat /src/IAIP/directions/SOUTH.md > a66f8bd2-29f5-461d-ad65-36b65252d469/specs/foundation_direction_SOUTH.md
\\\`\\\`\\\`

**Mia Agents** (\`/src/palimpsest/mia-agents/agents/\`):
\\\`\\\`\\\`bash
# List available agents
ls -la /src/palimpsest/mia-agents/agents/ > a66f8bd2-29f5-461d-ad65-36b65252d469/specs/mia_agents_inventory.txt

# Copy relevant agent definitions
cp /src/palimpsest/mia-agents/agents/*.md a66f8bd2-29f5-461d-ad65-36b65252d469/specs/mia_agents/

# Document which agents could assist with parallel development
# Create: a66f8bd2-29f5-461d-ad65-36b65252d469/specs/mia_agents_integration_plan.md
\\\`\\\`\\\`

**Claude Embodiments** (\`/src/home/jgi/.claude/CLAUDE.md\`):
\\\`\\\`\\\`bash
# Copy Claude embodiment patterns
cp /src/home/jgi/.claude/CLAUDE.md a66f8bd2-29f5-461d-ad65-36b65252d469/specs/claude_embodiments.md

# Use these patterns to understand how Claude approaches tasks
\\\`\\\`\\\`

**Session Data** (\`/src/_sessiondata/\`):
\\\`\\\`\\\`bash
# Check if there's existing session data for this orchestration
ls -la /src/_sessiondata/a66f8bd2-29f5-461d-ad65-36b65252d469/ 2>/dev/null || mkdir -p /src/_sessiondata/a66f8bd2-29f5-461d-ad65-36b65252d469/

# Store workspace metadata
cat > /src/_sessiondata/a66f8bd2-29f5-461d-ad65-36b65252d469/workspace_metadata.json <<EOF
{
  \"session_id\": \"a66f8bd2-29f5-461d-ad65-36b65252d469\",
  \"parent_trace_id\": \"a50f3fc2-eb8c-434d-a37e-ef9615d9c07d\",
  \"orchestrator\": \"claude-online\",
  \"assistant\": \"gemini-pro\",
  \"created\": \"\$(date -Iseconds)\",
  \"purpose\": \"Parallel development workspace for Agentic Flywheel MCP\"
}
EOF
\\\`\\\`\\\`

**Option 5: Enhance Mia Agent Skills**
After gathering context, enhance or create Mia agent skills in /src/palimpsest/skills-mia/ for:
- RISE specification generation assistance
- Integration contract validation
- Automated testing coordination
- Cherry-picking completed work

---

## Tracing Context (from @_env.sh)

**Session Namespace**: \`avaLangflowAgenticFlywheel\`

**Key Session IDs**:
- **Parent Trace**: \`a50f3fc2-eb8c-434d-a37e-ef9615d9c07d\` (common tracing session)
- **Orchestration Session**: \`a66f8bd2-29f5-461d-ad65-36b65252d469\` (parallel development workspace)

**MCP Configurations**:
- \`/src/.mcp.coaiapy.env.aetherial.json\` (coaiapy-mcp with Langfuse/Redis)
- \`/src/.mcp.github.ava.json\` (GitHub integration)

**Additional Context Directories**:
- \`/src/_sessiondata/\` - Session data storage
- \`/src/Miadi-46\` - Miadi platform context
- \`/src/coaiapy\` - coaiapy ecosystem
- \`/src/IAIP\` - IAIP methodologies

**Using coaiapy_aetherial**:
You can query the parent trace to see Claude's creative journey:
\\\`\\\`\\\`bash
# Get trace information
coaia_fuse_trace_get --trace_id a50f3fc2-eb8c-434d-a37e-ef9615d9c07d

# Add your observations
coaia_fuse_add_observation --trace_id a50f3fc2-eb8c-434d-a37e-ef9615d9c07d --content '{\"gemini_contribution\": \"...\"}'
\\\`\\\`\\\`

---

## IAIP Direction Context

**Current Direction**: **EAST** (Exploration, Architecture, Scaffolding, Testing)
- We are in the exploration and architecture phase
- Building scaffolding for parallel development
- Preparing testing infrastructure

**Ensuring SOUTH is Adequate**: **SOUTH** (Specification, Outcome-definition, Unified-vision, Tension-dynamics, Harmony)
- RISE specifications created (✅)
- Desired outcomes clearly defined (✅)
- Structural tensions documented (✅)
- Need to maintain harmony as subagents work in parallel

Reference: /src/IAIP/directions for full context

---

## Recommended First Steps

### 1. **Understand the Workspace**
\\\`\\\`\\\`bash
cd a66f8bd2-29f5-461d-ad65-36b65252d469
cat README.md
cat ORCHESTRATION.md
\\\`\\\`\\\`

### 2. **Choose Your Contribution Path**

**Path A - Implementation** (High Impact):
\\\`\\\`\\\`bash
# Pick a task
cat subagents/01_langflow_backend_task.md

# Start implementation following the starter prompt
# Create RISE spec -> Implement -> Test -> Signal completion
\\\`\\\`\\\`

**Path B - Research** (Foundation Support):
\\\`\\\`\\\`bash
# Research Langflow API
# Document findings in specs/langflow_api_research.md
# Provide API contract for Task 1 implementer
\\\`\\\`\\\`

**Path C - Observation** (Meta-level Support):
\\\`\\\`\\\`bash
# Create GEMINI.md in workspace root
# Document the parallel development journey
# Add insights and optimization suggestions
\\\`\\\`\\\`

### 3. **Integrate with Tracing**
\\\`\\\`\\\`bash
# Create your own child trace
coaia_fuse_trace_create \\\\
  --name \"Gemini Contribution to Agentic Flywheel\" \\\\
  --parent_trace_id a50f3fc2-eb8c-434d-a37e-ef9615d9c07d \\\\
  --metadata '{\"agent\": \"gemini-pro\", \"session\": \"a66f8bd2-29f5-461d-ad65-36b65252d469\"}'
\\\`\\\`\\\`

### 4. **Collaborate with Claude**
- Monitor \`results/\` directory for Claude subagent completions
- Review and provide feedback on completed specs
- Suggest optimizations or alternative approaches
- Help with integration testing

---

## Key Resources Available

**In Workspace**:
- \`README.md\` - Quick start for orchestrator and subagents
- \`ORCHESTRATION.md\` - Detailed strategy and progress tracking
- \`subagents/*.md\` - 6 comprehensive task prompts
- \`rispecs/app.spec.md\` - Master RISE specification

**In Codebase**:
- \`src/agentic_flywheel/backends/base.py\` - Universal backend interface
- \`src/agentic_flywheel/mcp_server.py\` - Current MCP server with 7 tools
- \`src/agentic_flywheel/PLAN_BACKEND_MIGRATION_250929.md\` - Migration roadmap
- \`src/agentic_flywheel/agentic_flywheel/config/flow-registry.yaml\` - Flow definitions

**External References**:
- /src/home/jgi/.claude/CLAUDE.md - Claude embodiments and patterns
- /src/palimpsest/mia-agents/agents/ - Mia agent definitions
- /src/palimpsest/skills-mia/ - Claude.ai skill templates

---

## Success Indicators

You'll know you're helping effectively when:
- ✅ A RISE specification is created (autonomous, implementation-agnostic)
- ✅ Integration contracts are fulfilled (clear interfaces defined)
- ✅ Research findings reduce uncertainty for implementers
- ✅ Observations provide meta-level insights for team coordination
- ✅ Your trace captures your contribution to the creative journey

---

## Communication Protocol

**Signal Completion**:
Create a file in \`a66f8bd2-29f5-461d-ad65-36b65252d469/results/\` with format:
\\\`\\\`\\\`
gemini_<contribution-type>_COMPLETE.md

Status: COMPLETE
Agent: gemini-pro
Contribution: [research|implementation|observation|coordination]
Deliverables: [list]
Integration Notes: [how Claude can use this]
Next Steps: [recommendations]
\\\`\\\`\\\`

**Tracing**:
Add observations to parent trace documenting:
- What you discovered
- Decisions you made
- Challenges you encountered
- Insights for the team

---

## The Bigger Picture

This workspace is part of a **creative advancement** from:
- **Current**: Flowise-only MCP with basic flow orchestration
- **Desired**: Multi-backend (Langflow + Flowise) MCP with full observability and persistent memory
- **Outcome**: Users can create intelligent AI workflows across platforms with complete creative archaeology

**Your role**: Help bridge the structural tension through research, implementation, or observation.

---

**Ready to Contribute?** 🚀

Choose your path:
1. 🔧 **Implement** - Pick a task from subagents/ and build it
2. 🔍 **Research** - Investigate Langflow API for Task 1
3. 👁️ **Observe** - Create GEMINI.md documenting the journey
4. 🤝 **Coordinate** - Help integrate completed work

The workspace awaits your creative contribution!
" \\
  /src/IAIP \\
  /src/_sessiondata/ \\
  /src/palimpsest/mia-agents/agents/ \\
  /src/home/jgi/.claude \\
  /src/palimpsest/skills-mia/ \\
  a66f8bd2-29f5-461d-ad65-36b65252d469/
