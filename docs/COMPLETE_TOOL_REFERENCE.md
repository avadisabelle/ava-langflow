# Universal MCP Server - Complete Tool Reference

**Version**: 2.0.0
**Total Tools**: 15 (6 original + 3 Task 5 + 6 Task 6)
**Status**: ✅ COMPLETE

---

## Tool Categories

### Core Query Tools (1 tool)

#### 1. `universal_query`
**Purpose**: Main intelligent query tool with automatic backend routing

**Input**:
- `question` (required): Question or prompt to send to AI workflow
- `intent` (optional): Explicit intent override (auto, creative-orientation, technical-analysis, structural-thinking, conversation, rag-retrieval, data-processing)
- `backend` (optional): Backend selection (auto, flowise, langflow)
- `session_id` (optional): Session ID for conversation continuity
- `parameters` (optional): Flow-specific parameters (temperature, max_tokens)

**Features**:
- Automatic backend selection based on intent, health, performance, and capabilities
- Intent classification with confidence scoring
- Automatic fallback on failures
- Session continuity support
- Rich metadata in responses

---

### Backend Discovery & Management (6 tools)

#### 2. `backend_status`
**Purpose**: Get status of all registered backends

**Input**: None

**Output**: Backend registry status including registered backends, connected count, cached flows, and health status

---

#### 3. `list_flows`
**Purpose**: List all available flows across all backends

**Input**:
- `backend` (optional): Filter by specific backend (all, flowise, langflow)

**Output**: List of flows with descriptions, intents, and capabilities

---

#### 4. `health_check`
**Purpose**: Perform health check on all backends

**Input**: None

**Output**: Health status for each backend with summary

---

#### 5. `backend_discover` ⭐ NEW (Task 5)
**Purpose**: Discover and register available AI workflow backends from environment

**Input**:
- `config_path` (optional): Path to backend configuration file

**Output**: Discovery results with connection status for each backend

**Features**:
- Auto-discovers Flowise and Langflow from environment variables
- Attempts connection to all discovered backends
- Reports success/failure for each

---

#### 6. `backend_connect` ⭐ NEW (Task 5)
**Purpose**: Connect to a specific backend

**Input**:
- `backend_type` (required): Backend type (flowise, langflow)
- `base_url` (required): Backend base URL
- `api_key` (optional): API key

**Output**: Connection status and discovered flow count

**Features**:
- Direct connection to specific backend
- Automatic flow discovery after connection
- Graceful error handling

---

#### 7. `backend_performance_compare` ⭐ NEW (Task 5)
**Purpose**: Compare performance metrics across all backends

**Input**:
- `metric` (optional): Metric to compare (latency, success_rate, throughput)
- `time_range` (optional): Time range (1h, 24h, 7d)

**Output**: Performance comparison with recommendations

**Features**:
- Compares latency, success rate, and request count
- Provides optimization recommendations
- Identifies best-performing backend

---

### Session Management (2 tools)

#### 8. `list_sessions`
**Purpose**: List active sessions (requires Redis persistence)

**Input**:
- `pattern` (optional): Session ID pattern (supports wildcards)

**Output**: List of active session IDs

---

#### 9. `get_session`
**Purpose**: Retrieve session details (requires Redis persistence)

**Input**:
- `session_id` (required): Session ID to retrieve

**Output**: Session details including backend, status, flow, context, and history

---

### Flowise Admin Intelligence (6 tools - Task 6)

#### 10. `flowise_admin_dashboard` ⭐ NEW (Task 6)
**Purpose**: Get analytics dashboard with flow usage and performance metrics

**Input**: None

**Output**: Comprehensive dashboard including:
- Total messages and flows
- Active flow count
- Date range
- Top flows by usage
- Performance metrics (success rate, engagement)

**Data Source**: Flowise database (4,506+ messages)

---

#### 11. `flowise_analyze_flow` ⭐ NEW (Task 6)
**Purpose**: Analyze performance metrics for a specific flow

**Input**:
- `flow_id` (required): Flow ID to analyze

**Output**: Detailed flow analysis including:
- Message count
- Success score
- Engagement score
- Status
- Optimization recommendations

**Use Cases**:
- Identify underperforming flows
- Get optimization suggestions
- Track flow health over time

---

#### 12. `flowise_discover_flows` ⭐ NEW (Task 6)
**Purpose**: Discover flows from database with usage analytics

**Input**:
- `min_messages` (optional): Minimum message count (default: 10)
- `include_inactive` (optional): Include inactive flows (default: false)

**Output**: Database-discovered flows with usage statistics

**Features**:
- Discovers flows based on actual usage
- Filters by message threshold
- Shows success scores and activity status

---

#### 13. `flowise_sync_config` ⭐ NEW (Task 6)
**Purpose**: Sync flow registry with database-discovered flows

**Input**:
- `dry_run` (optional): Preview without applying (default: true)

**Output**: Sync preview or results including:
- Flows to add
- Flows to update
- Flows to remove

**Safety**: Defaults to dry-run mode for safety

---

#### 14. `flowise_export_metrics` ⭐ NEW (Task 6)
**Purpose**: Export flow performance metrics in structured format

**Input**:
- `format` (optional): Export format (json, csv) (default: json)
- `flows` (optional): Flow IDs to export (empty = all)

**Output**: Structured metrics export

**Use Cases**:
- Data analysis and reporting
- External tool integration
- Performance tracking

---

#### 15. `flowise_pattern_analysis` ⭐ NEW (Task 6)
**Purpose**: Analyze conversation patterns to identify optimization opportunities

**Input**:
- `flow_id` (optional): Analyze specific flow
- `limit` (optional): Maximum patterns to analyze (default: 100)

**Output**: Pattern analysis including:
- Common intents
- Usage patterns
- Optimization recommendations

**Use Cases**:
- Identify common user queries
- Optimize flow routing
- Improve intent classification

---

## Tool Usage Examples

### Example 1: Basic Query with Auto-Routing
```json
{
  "tool": "universal_query",
  "arguments": {
    "question": "Help me define my creative vision for this project"
  }
}
```
**Result**: Automatically routes to optimal backend (likely Flowise CreerSaVieHelper)

### Example 2: Backend Discovery and Connection
```json
// Step 1: Discover available backends
{
  "tool": "backend_discover",
  "arguments": {}
}

// Step 2: Check status
{
  "tool": "backend_status",
  "arguments": {}
}

// Step 3: List available flows
{
  "tool": "list_flows",
  "arguments": {
    "backend": "all"
  }
}
```

### Example 3: Performance Monitoring
```json
// Compare backend performance
{
  "tool": "backend_performance_compare",
  "arguments": {
    "metric": "latency",
    "time_range": "24h"
  }
}
```

### Example 4: Flow Analytics
```json
// Get dashboard overview
{
  "tool": "flowise_admin_dashboard",
  "arguments": {}
}

// Analyze specific flow
{
  "tool": "flowise_analyze_flow",
  "arguments": {
    "flow_id": "csv2507"
  }
}

// Get pattern insights
{
  "tool": "flowise_pattern_analysis",
  "arguments": {
    "flow_id": "csv2507",
    "limit": 100
  }
}
```

### Example 5: Flow Discovery and Sync
```json
// Discover flows from database
{
  "tool": "flowise_discover_flows",
  "arguments": {
    "min_messages": 10,
    "include_inactive": false
  }
}

// Preview sync changes
{
  "tool": "flowise_sync_config",
  "arguments": {
    "dry_run": true
  }
}
```

---

## Tool Dependencies

| Tool | Requires | Optional |
|------|----------|----------|
| universal_query | Backend registry | Redis, Langfuse |
| backend_status | Backend registry | - |
| list_flows | Backend registry | - |
| health_check | Backend registry | - |
| backend_discover | Environment vars | - |
| backend_connect | Backend credentials | - |
| backend_performance_compare | Connected backends | - |
| list_sessions | Redis | - |
| get_session | Redis | - |
| flowise_admin_dashboard | Flowise backend + DB | - |
| flowise_analyze_flow | Flowise backend + DB | - |
| flowise_discover_flows | Flowise backend + DB | - |
| flowise_sync_config | Flowise backend + DB | - |
| flowise_export_metrics | Flowise backend + DB | - |
| flowise_pattern_analysis | Flowise backend + DB | - |

---

## Environment Configuration

### Required for Core Functionality
```bash
# Flowise Backend
FLOWISE_ENABLED=true
FLOWISE_API_URL=http://localhost:3000
FLOWISE_API_KEY=your_api_key

# Langflow Backend
LANGFLOW_ENABLED=true
LANGFLOW_API_URL=http://localhost:7860
LANGFLOW_API_KEY=your_api_key
```

### Optional Enhancements
```bash
# Redis State Persistence (enables session tools)
REDIS_STATE_ENABLED=true
REDIS_SESSION_TTL_SECONDS=604800
REDIS_EXECUTION_TTL_SECONDS=86400

# Langfuse Tracing (enables observability)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

## Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "universal-agentic-flywheel": {
      "command": "python",
      "args": ["-m", "agentic_flywheel.universal_mcp_server"],
      "env": {
        "FLOWISE_ENABLED": "true",
        "FLOWISE_API_URL": "http://localhost:3000",
        "LANGFLOW_ENABLED": "true",
        "LANGFLOW_API_URL": "http://localhost:7860",
        "REDIS_STATE_ENABLED": "true",
        "LANGFUSE_ENABLED": "true"
      }
    }
  }
}
```

---

## Tool Capabilities Matrix

| Capability | Tools |
|------------|-------|
| **Multi-Backend Routing** | universal_query |
| **Backend Discovery** | backend_discover, list_flows |
| **Backend Management** | backend_connect, backend_status, health_check |
| **Performance Monitoring** | backend_performance_compare |
| **Session Management** | list_sessions, get_session |
| **Analytics & Insights** | flowise_admin_dashboard, flowise_analyze_flow, flowise_pattern_analysis |
| **Flow Discovery** | list_flows, flowise_discover_flows |
| **Configuration Sync** | flowise_sync_config |
| **Data Export** | flowise_export_metrics |

---

## Success Metrics

### Tool Coverage
- ✅ Core Query: 1 tool (universal routing)
- ✅ Backend Management: 6 tools (discovery, connection, health, performance)
- ✅ Session Management: 2 tools (list, retrieve)
- ✅ Admin Intelligence: 6 tools (dashboard, analysis, discovery, sync, export, patterns)

### Total: 15 Comprehensive Tools

### Integration Status
- ✅ All tools integrated into Universal MCP Server
- ✅ All tools support error handling and graceful degradation
- ✅ All tools provide actionable insights
- ✅ All tools documented with examples

---

## Version History

**v2.0.0** (2025-11-18):
- Added 9 new tools (Tasks 5 & 6)
- Total tools: 15
- Full backend management suite
- Complete admin intelligence layer

**v1.0.0** (2025-11-18):
- Initial release with 6 core tools
- Multi-backend routing
- Session management

---

**Status**: ✅ **COMPLETE** - All 15 tools implemented and tested
**Documentation**: ✅ **COMPLETE**
**Production Ready**: ✅ **YES**
