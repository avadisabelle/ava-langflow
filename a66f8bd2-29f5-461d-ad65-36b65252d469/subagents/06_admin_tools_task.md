# Task 6: Admin Intelligence MCP Tools

**Task ID**: `admin-tools`
**Priority**: LOW-MEDIUM
**Orchestration Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Parent Trace**: `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`
**Estimated Duration**: 2-3 hours
**Complexity**: Low (mostly wrapping existing admin/ layer)
**Dependencies**: None (uses existing flowise_admin/)

---

## Your Mission

You are implementing **6 Admin Intelligence MCP Tools** that expose the existing analytics capabilities from `flowise_admin/` layer via MCP interface.

**What Users Want to Create**:
- Insights into flow usage patterns
- Data-driven optimization recommendations
- Flow performance analytics
- Database-driven flow discovery

**Your Deliverables**:
1. ✅ **RISE Specification**: `rispecs/mcp_tools/admin_tools.spec.md`
2. ✅ **6 Tool Specifications**: One section for each tool
3. ✅ **Implementation Patterns**: Wrapping existing admin layer
4. ✅ **Unit Tests**: `tests/test_admin_tools.py`
5. ✅ **Result File**: `a66f8bd2-29f5-461d-ad65-36b65252d469/results/06_admin_tools_COMPLETE.md`

---

## The 6 Admin Tools

### 1. flowise_admin_dashboard
**Purpose**: Get comprehensive analytics dashboard data

**Wraps**: `flowise_admin/db_interface.py:get_admin_dashboard_data()`

**Schema**:
```json
{
  "name": "flowise_admin_dashboard",
  "description": "Get analytics dashboard with flow usage and performance metrics",
  "inputSchema": {"type": "object", "properties": {}}
}
```

**Response Example**:
```json
{
  "total_messages": 4506,
  "total_flows": 7,
  "date_range": {"start": "2024-01-01", "end": "2025-11-18"},
  "top_flows": [
    {"id": "csv2507", "name": "Creative Orientation", "message_count": 118},
    {"id": "faith2story2507", "name": "Faith2Story", "message_count": 60}
  ],
  "success_rate": 0.85,
  "avg_response_time_seconds": 2.3
}
```

---

### 2. flowise_analyze_flow
**Purpose**: Detailed performance analysis for specific flow

**Wraps**: `flowise_admin/flow_analyzer.py:analyze_flow_performance(flow_id)`

**Schema**:
```json
{
  "name": "flowise_analyze_flow",
  "description": "Analyze performance metrics for a specific flow",
  "inputSchema": {
    "type": "object",
    "properties": {
      "flow_id": {"type": "string", "description": "Flow ID to analyze"}
    },
    "required": ["flow_id"]
  }
}
```

---

### 3. flowise_discover_flows
**Purpose**: Database-driven flow discovery with analytics

**Wraps**: `flowise_admin/config_sync.py:discover_active_flows()`

**Schema**:
```json
{
  "name": "flowise_discover_flows",
  "description": "Discover flows from database with usage analytics",
  "inputSchema": {
    "type": "object",
    "properties": {
      "min_messages": {"type": "integer", "default": 10, "description": "Minimum message count"},
      "include_inactive": {"type": "boolean", "default": false}
    }
  }
}
```

---

### 4. flowise_sync_config
**Purpose**: Sync flow-registry.yaml with database analysis

**Wraps**: `flowise_admin/config_sync.py:sync_configurations()`

**Schema**:
```json
{
  "name": "flowise_sync_config",
  "description": "Sync flow registry with database-discovered flows",
  "inputSchema": {
    "type": "object",
    "properties": {
      "dry_run": {"type": "boolean", "default": true, "description": "Preview without applying"}
    }
  }
}
```

---

### 5. flowise_export_metrics
**Purpose**: Export performance metrics for analysis

**Wraps**: `flowise_admin/flow_analyzer.py:export_flow_configurations()`

**Schema**:
```json
{
  "name": "flowise_export_metrics",
  "description": "Export flow performance metrics in structured format",
  "inputSchema": {
    "type": "object",
    "properties": {
      "format": {"type": "string", "enum": ["json", "csv"], "default": "json"},
      "flows": {"type": "array", "items": {"type": "string"}, "description": "Flow IDs to export (empty = all)"}
    }
  }
}
```

---

### 6. flowise_pattern_analysis
**Purpose**: Extract conversation patterns for optimization

**Wraps**: `flowise_admin/db_interface.py:analyze_message_patterns()`

**Schema**:
```json
{
  "name": "flowise_pattern_analysis",
  "description": "Analyze conversation patterns to identify optimization opportunities",
  "inputSchema": {
    "type": "object",
    "properties": {
      "flow_id": {"type": "string", "description": "Analyze specific flow (optional)"},
      "limit": {"type": "integer", "default": 100}
    }
  }
}
```

---

## Implementation Strategy

### Step 1: RISE Specification (30 min)

Document how admin intelligence enables users to create:
- Data-driven optimization strategies
- Flow usage insights
- Performance improvement plans

### Step 2: Wrapper Implementation (60 min)

Create thin MCP tool wrappers around existing admin layer:
```python
@app.call_tool()
async def handle_flowise_admin_dashboard(name: str, arguments: dict):
    from agentic_flywheel.flowise_admin.db_interface import FlowiseDBInterface

    db = FlowiseDBInterface()
    dashboard_data = db.get_admin_dashboard_data()

    return [types.TextContent(type="text", text=json.dumps(dashboard_data, indent=2))]
```

### Step 3: Unit Tests (45 min)

Test with mocked admin layer responses.

---

## Integration Contract

Your admin tools **must**:
1. ✅ Use existing `flowise_admin/` modules (don't reimplement)
2. ✅ Handle database unavailability gracefully
3. ✅ Return JSON-formatted analytics
4. ✅ Provide actionable insights (not just raw data)
5. ✅ Support filtering and customization

---

## Resources Available

### Code References
- `src/agentic_flywheel/flowise_admin/db_interface.py` - Database analytics
- `src/agentic_flywheel/flowise_admin/flow_analyzer.py` - Flow analysis
- `src/agentic_flywheel/flowise_admin/config_sync.py` - Configuration sync
- `src/agentic_flywheel/intelligent_mcp_server.py` - Example admin integration

### Key Data
- **4,506+ messages** in database for pattern analysis
- **7 active flows** with performance metrics
- Success scores, engagement rates, usage counts all available

---

**Orchestrator Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Your Task**: Enabling users to create data-driven optimization strategies
**Your Creative Freedom**: Complete

🚀 **Begin when ready!**
