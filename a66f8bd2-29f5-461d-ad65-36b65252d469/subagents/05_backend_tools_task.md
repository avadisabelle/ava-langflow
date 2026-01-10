# Task 5: Backend Management MCP Tools

**Task ID**: `backend-tools`
**Priority**: MEDIUM
**Orchestration Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Parent Trace**: `a50f3fc2-eb8c-434d-a37e-ef9615d9c07d`
**Estimated Duration**: 2-3 hours
**Complexity**: Low-Medium
**Dependencies**: Langflow backend implementation

---

## Your Mission

You are implementing **6 Backend Management MCP Tools** that enable users to discover, monitor, and manage multiple AI workflow backends.

**What Users Want to Create**:
- Visibility into all available backends (Flowise, Langflow, future platforms)
- Health monitoring across platforms
- Performance comparison for optimization
- Backend discovery and connection management

**Your Deliverables**:
1. ✅ **RISE Specification**: `rispecs/mcp_tools/backend_tools.spec.md`
2. ✅ **6 Tool Specifications**: One section for each tool
3. ✅ **Implementation Patterns**: Integration into `universal_mcp_server.py`
4. ✅ **Unit Tests**: `tests/test_backend_tools.py`
5. ✅ **Result File**: `a66f8bd2-29f5-461d-ad65-36b65252d469/results/05_backend_tools_COMPLETE.md`

---

## The 6 Backend Tools

### 1. backend_registry_status
**Purpose**: Show status of all registered backends

**Schema**:
```json
{
  "name": "backend_registry_status",
  "description": "Get status of all registered AI workflow backends",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

**Response Example**:
```json
{
  "total_backends": 2,
  "backends": [
    {
      "type": "flowise",
      "name": "Flowise Production",
      "status": "connected",
      "health_score": 0.95,
      "flows_count": 7,
      "last_check": "2025-11-18T10:30:00Z"
    },
    {
      "type": "langflow",
      "name": "Langflow Dev",
      "status": "connected",
      "health_score": 0.88,
      "flows_count": 5,
      "last_check": "2025-11-18T10:30:00Z"
    }
  ]
}
```

---

### 2. backend_discover
**Purpose**: Auto-discover available backends from configuration

**Schema**:
```json
{
  "name": "backend_discover",
  "description": "Discover and register available AI workflow backends",
  "inputSchema": {
    "type": "object",
    "properties": {
      "config_path": {
        "type": "string",
        "description": "Optional path to backend configuration file"
      }
    }
  }
}
```

---

### 3. backend_connect
**Purpose**: Establish connection to specific backend

**Schema**:
```json
{
  "name": "backend_connect",
  "description": "Connect to a specific backend",
  "inputSchema": {
    "type": "object",
    "properties": {
      "backend_type": {
        "type": "string",
        "enum": ["flowise", "langflow"],
        "description": "Backend type to connect"
      },
      "base_url": {
        "type": "string",
        "description": "Backend base URL"
      },
      "api_key": {
        "type": "string",
        "description": "Optional API key"
      }
    },
    "required": ["backend_type", "base_url"]
  }
}
```

---

### 4. backend_list_flows
**Purpose**: List all flows across all backends

**Schema**:
```json
{
  "name": "backend_list_flows",
  "description": "List flows from all connected backends",
  "inputSchema": {
    "type": "object",
    "properties": {
      "backend_filter": {
        "type": "string",
        "enum": ["all", "flowise", "langflow"],
        "default": "all"
      },
      "intent_filter": {
        "type": "string",
        "description": "Filter flows by intent keyword"
      }
    }
  }
}
```

**Response Example**:
```json
{
  "total_flows": 12,
  "flows": [
    {
      "id": "csv2507",
      "name": "Creative Orientation",
      "backend": "flowise",
      "intent_keywords": ["creative", "vision", "goal"],
      "performance_score": 0.85
    },
    {
      "id": "langflow_001",
      "name": "Technical Analysis",
      "backend": "langflow",
      "intent_keywords": ["code", "technical"],
      "performance_score": 0.90
    }
  ]
}
```

---

### 5. backend_execute_universal
**Purpose**: Execute flow with backend auto-selection (similar to universal_query but more explicit)

**Schema**:
```json
{
  "name": "backend_execute_universal",
  "description": "Execute flow with intelligent backend selection",
  "inputSchema": {
    "type": "object",
    "properties": {
      "flow_id": {
        "type": "string",
        "description": "Flow ID to execute (searches across backends)"
      },
      "input_data": {
        "type": "object",
        "description": "Input data for flow"
      },
      "backend_preference": {
        "type": "string",
        "enum": ["auto", "flowise", "langflow"]
      }
    },
    "required": ["flow_id", "input_data"]
  }
}
```

---

### 6. backend_performance_compare
**Purpose**: Compare performance metrics across backends

**Schema**:
```json
{
  "name": "backend_performance_compare",
  "description": "Compare performance metrics across all backends",
  "inputSchema": {
    "type": "object",
    "properties": {
      "metric": {
        "type": "string",
        "enum": ["latency", "success_rate", "throughput"],
        "default": "latency"
      },
      "time_range": {
        "type": "string",
        "enum": ["1h", "24h", "7d"],
        "default": "24h"
      }
    }
  }
}
```

**Response Example**:
```json
{
  "metric": "latency",
  "time_range": "24h",
  "comparison": [
    {
      "backend": "flowise",
      "avg_latency_ms": 1200,
      "p95_latency_ms": 2100,
      "total_requests": 156
    },
    {
      "backend": "langflow",
      "avg_latency_ms": 980,
      "p95_latency_ms": 1800,
      "total_requests": 89
    }
  ],
  "recommendation": "Langflow shows 18% better latency for recent queries"
}
```

---

## Implementation Strategy

### Step 1: RISE Specification (45 min)

Create comprehensive spec covering:
- Desired outcomes for each tool
- Backend registry integration patterns
- Performance tracking methodology
- Error handling strategies

### Step 2: Tool Implementation Patterns (90 min)

Document how each tool integrates with:
- `BackendRegistry` for discovery and management
- `UniversalPerformanceMetrics` for analytics
- Error handling and fallback logic

### Step 3: Unit Tests (45 min)

Test coverage for all 6 tools with mocked backends.

---

## Integration Contract

Your backend tools **must**:
1. ✅ Use `BackendRegistry` as single source of truth
2. ✅ Return consistent JSON structures
3. ✅ Handle backend unavailability gracefully
4. ✅ Provide actionable insights (not just raw data)
5. ✅ Support filtering and customization
6. ✅ Include performance recommendations

---

**Orchestrator Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`
**Your Task**: Enabling users to manage multi-backend AI infrastructure
**Your Creative Freedom**: Complete

🚀 **Begin when ready!**
