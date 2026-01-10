# RISE Specification: Backend Management MCP Tools

**Component**: Backend Management Tools
**Version**: 1.0
**Created**: 2025-11-18
**Parent Spec**: `rispecs/app.spec.md`
**Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`

---

## 🎨 Desired Outcome Definition

Users want to **manage multi-backend AI infrastructure** with full visibility and control over their distributed workflow platforms.

### **Infrastructure Visibility**
- Real-time status of all backends (Flowise, Langflow, future platforms)
- Health monitoring and diagnostics
- Flow catalog across all platforms
- Performance comparison and benchmarking

### **Operational Control**
- Dynamic backend discovery and registration
- Connection management
- Cross-backend flow execution
- Performance-based optimization recommendations

### **Data-Driven Decisions**
- Latency comparisons
- Success rate tracking
- Throughput analysis
- Actionable optimization insights

---

## 📊 Current Structural Reality

Backend management is **fragmented** - users have no unified view of their multi-backend infrastructure.

### **What Exists**
- ✅ `BackendRegistry` for programmatic backend management
- ✅ `UniversalRouter` with performance tracking
- ✅ Individual backend implementations (Flowise, Langflow)
- ✅ Health check mechanisms

### **What's Missing**
- ❌ No MCP tools for backend management
- ❌ No unified status dashboard
- ❌ No performance comparison interface
- ❌ No backend discovery automation
- ❌ No cross-backend flow catalog

---

## ⚡ Structural Tension

**Current**: Fragmented backend management (programmatic only)
**Desired**: Unified MCP interface for multi-backend visibility and control

This tension drives natural advancement toward comprehensive backend management tools.

---

## 🔧 The 6 Backend Management Tools

### 1. backend_registry_status

**Purpose**: Unified status dashboard for all registered backends

**Desired Outcome**: Users see at-a-glance health of entire infrastructure

**Input Schema**:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Output Structure**:
```json
{
  "total_backends": 2,
  "healthy_count": 2,
  "unhealthy_count": 0,
  "backends": [
    {
      "type": "flowise",
      "name": "Flowise Production",
      "status": "connected",
      "health_score": 0.95,
      "flows_count": 7,
      "last_check": "2025-11-18T10:30:00Z",
      "uptime_percent": 99.2,
      "avg_latency_ms": 1200
    }
  ],
  "summary": {
    "total_flows": 12,
    "avg_health": 0.915,
    "recommendation": "All backends healthy"
  }
}
```

**Integration Points**:
- `BackendRegistry.get_all_backends()`
- `backend.health_check()` for each backend
- `backend.discover_flows()` for flow counts
- Performance metrics from `PerformanceTracker`

---

### 2. backend_discover

**Purpose**: Auto-discover and register backends from configuration

**Desired Outcome**: Users automatically connect to available backends without manual setup

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "config_path": {
      "type": "string",
      "description": "Optional path to backend configuration file"
    },
    "force_rediscover": {
      "type": "boolean",
      "description": "Force rediscovery even if backends already registered",
      "default": false
    }
  }
}
```

**Output Structure**:
```json
{
  "discovered": 2,
  "registered": 2,
  "backends": [
    {
      "type": "flowise",
      "base_url": "http://localhost:3000",
      "status": "registered"
    },
    {
      "type": "langflow",
      "base_url": "http://localhost:7860",
      "status": "registered"
    }
  ],
  "errors": []
}
```

**Integration Points**:
- `BackendRegistry.discover_backends()`
- Environment variable reading
- Configuration file parsing

---

### 3. backend_connect

**Purpose**: Manually connect to specific backend

**Desired Outcome**: Users can add custom backends dynamically

**Input Schema**:
```json
{
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
    },
    "name": {
      "type": "string",
      "description": "Optional custom name for backend"
    }
  },
  "required": ["backend_type", "base_url"]
}
```

**Output Structure**:
```json
{
  "success": true,
  "backend": {
    "type": "flowise",
    "name": "Custom Flowise Instance",
    "base_url": "https://flowise.example.com",
    "status": "connected",
    "flows_discovered": 5
  }
}
```

**Integration Points**:
- `FlowiseBackend(base_url, api_key)` constructor
- `LangflowBackend(base_url, api_key)` constructor
- `BackendRegistry.register_backend()`

---

### 4. backend_list_flows

**Purpose**: Unified flow catalog across all backends

**Desired Outcome**: Users see all available flows in one place with filtering

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "backend_filter": {
      "type": "string",
      "enum": ["all", "flowise", "langflow"],
      "default": "all",
      "description": "Filter by backend type"
    },
    "intent_filter": {
      "type": "string",
      "description": "Filter flows by intent keyword"
    },
    "min_performance_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1,
      "description": "Minimum performance score threshold"
    }
  }
}
```

**Output Structure**:
```json
{
  "total_flows": 12,
  "filtered_count": 8,
  "flows": [
    {
      "id": "csv2507",
      "universal_id": "flowise:csv2507",
      "name": "Creative Orientation",
      "description": "Structural tension guidance",
      "backend": "flowise",
      "backend_url": "http://localhost:3000",
      "intent_keywords": ["creative", "vision", "goal"],
      "performance": {
        "score": 0.85,
        "avg_latency_ms": 1200,
        "success_rate": 0.92,
        "total_executions": 118
      }
    }
  ],
  "summary": {
    "by_backend": {"flowise": 7, "langflow": 5},
    "avg_performance": 0.875
  }
}
```

**Integration Points**:
- `backend.discover_flows()` for each backend
- `PerformanceTracker` for performance data
- Flow filtering and sorting logic

---

### 5. backend_execute_universal

**Purpose**: Execute flow by ID with automatic backend resolution

**Desired Outcome**: Users execute flows without knowing which backend hosts them

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "flow_id": {
      "type": "string",
      "description": "Flow ID (searches across all backends)"
    },
    "input_data": {
      "type": "object",
      "description": "Input data for flow execution"
    },
    "backend_preference": {
      "type": "string",
      "enum": ["auto", "flowise", "langflow"],
      "default": "auto",
      "description": "Backend selection strategy"
    },
    "session_id": {
      "type": "string",
      "description": "Optional session ID for continuity"
    }
  },
  "required": ["flow_id", "input_data"]
}
```

**Output Structure**:
```json
{
  "flow_id": "csv2507",
  "backend_used": "flowise",
  "execution_id": "exec_abc123",
  "result": {
    "response": "Structural tension is..."
  },
  "metadata": {
    "duration_ms": 1234,
    "backend_selection": "auto",
    "fallback_used": false
  }
}
```

**Integration Points**:
- Flow ID resolution across backends
- `backend.execute_flow()` for execution
- Performance tracking
- Session continuity (Redis integration)

---

### 6. backend_performance_compare

**Purpose**: Comparative performance analytics across backends

**Desired Outcome**: Users make data-driven decisions about backend optimization

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "metric": {
      "type": "string",
      "enum": ["latency", "success_rate", "throughput"],
      "default": "latency",
      "description": "Primary metric to compare"
    },
    "time_range": {
      "type": "string",
      "enum": ["1h", "24h", "7d", "30d"],
      "default": "24h",
      "description": "Time range for analysis"
    },
    "intent_filter": {
      "type": "string",
      "description": "Compare performance for specific intent"
    }
  }
}
```

**Output Structure**:
```json
{
  "metric": "latency",
  "time_range": "24h",
  "comparison": [
    {
      "backend": "flowise",
      "backend_type": "flowise",
      "metrics": {
        "avg_latency_ms": 1200,
        "p50_latency_ms": 1100,
        "p95_latency_ms": 2100,
        "p99_latency_ms": 3500
      },
      "total_requests": 156,
      "success_rate": 0.92
    },
    {
      "backend": "langflow",
      "backend_type": "langflow",
      "metrics": {
        "avg_latency_ms": 980,
        "p50_latency_ms": 900,
        "p95_latency_ms": 1800,
        "p99_latency_ms": 2900
      },
      "total_requests": 89,
      "success_rate": 0.88
    }
  ],
  "winner": {
    "backend": "langflow",
    "advantage_percent": 18.3,
    "metric_value": 980
  },
  "recommendation": "Langflow shows 18% better latency for recent queries. Consider routing latency-sensitive flows to Langflow.",
  "trend": "improving"
}
```

**Integration Points**:
- `PerformanceTracker` historical data
- Statistical analysis (percentiles, averages)
- Trend analysis
- Recommendation engine

---

## 🏗️ Implementation Architecture

### Tool Handler Pattern

```python
# src/agentic_flywheel/tools/backend_tools.py

from typing import Any, Dict, List
from ..backends.registry import BackendRegistry
from ..routing import UniversalRouter

async def handle_backend_registry_status(name: str, arguments: dict) -> List:
    """Get status of all registered backends"""
    registry = BackendRegistry()
    await registry.discover_backends()

    backends_info = []
    for backend in registry.get_all_backends():
        health = await backend.health_check()
        flows = await backend.discover_flows()

        backends_info.append({
            "type": backend.backend_type.value,
            "status": "connected" if health else "disconnected",
            "health_score": 1.0 if health else 0.0,
            "flows_count": len(flows)
        })

    return [types.TextContent(
        type="text",
        text=json.dumps({
            "total_backends": len(backends_info),
            "backends": backends_info
        }, indent=2)
    )]
```

### Integration with BackendRegistry

```python
# Centralized backend management
registry = BackendRegistry()

# Auto-discovery from environment
await registry.discover_backends()

# Manual registration
await registry.register_backend(custom_backend)

# Unified access
all_backends = registry.get_all_backends()
flowise_backends = registry.get_backends_by_type(BackendType.FLOWISE)
```

### Performance Tracking Integration

```python
# Access router's performance tracker
router = get_router()
tracker = router.performance_tracker

# Get performance data
score = tracker.get_score("flowise", "creative-orientation")
history = tracker._history.get("flowise:creative-orientation", [])

# Calculate statistics
avg_latency = sum(h['latency_ms'] for h in history) / len(history)
success_rate = sum(1 for h in history if h['success']) / len(history)
```

---

## ✅ Integration Contract

### Requirements

1. **BackendRegistry as Source of Truth**
   - All tools use `BackendRegistry` for backend access
   - No direct backend instantiation in tools

2. **Consistent JSON Structures**
   - Predictable response formats
   - Always include metadata section
   - Error messages in structured format

3. **Graceful Error Handling**
   - Backend unavailability doesn't crash
   - Partial results when some backends fail
   - Clear error messages with remediation hints

4. **Actionable Insights**
   - Not just raw data dumps
   - Include recommendations
   - Highlight trends and patterns

5. **Performance Awareness**
   - Tools should be fast (<500ms typical)
   - Async operations throughout
   - Caching where appropriate

---

## 🧪 Testing Strategy

### Unit Tests (tests/test_backend_tools.py)

```python
@pytest.mark.asyncio
async def test_backend_registry_status():
    """Test registry status tool"""
    with patch('BackendRegistry') as mock_registry:
        # Mock backends
        mock_registry.get_all_backends.return_value = [mock_flowise, mock_langflow]

        result = await handle_backend_registry_status("backend_registry_status", {})

        # Verify structure
        data = json.loads(result[0].text)
        assert "total_backends" in data
        assert len(data["backends"]) == 2
```

**Test Coverage Goals**:
- ✅ All 6 tools have success path tests
- ✅ Error handling tests (backend unavailable)
- ✅ Filtering tests (backend_filter, intent_filter)
- ✅ Performance comparison calculations
- ✅ Empty/partial result handling

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool Response Time | <500ms | Average execution time |
| Error Rate | <1% | Failed tool calls / total |
| Data Completeness | >95% | Fields populated correctly |
| Insight Quality | High | Recommendation relevance |
| Test Coverage | >85% | Lines covered |

---

## 🔗 Related Components

- **BackendRegistry**: Central backend management (`backends/registry.py`)
- **UniversalRouter**: Performance tracking (`routing/router.py`)
- **PerformanceTracker**: Historical metrics (`routing/router.py`)
- **Universal Query**: Uses backend selection logic (`tools/universal_query.py`)

---

## 🚀 Production Deployment

### Environment Variables

```bash
# Backend discovery
FLOWISE_BASE_URL=http://localhost:3000
FLOWISE_API_KEY=your_key_here

LANGFLOW_BASE_URL=http://localhost:7860
LANGFLOW_API_KEY=your_key_here
```

### MCP Server Integration

```python
# In universal_mcp_server.py
from agentic_flywheel.tools.backend_tools import (
    handle_backend_registry_status,
    handle_backend_discover,
    handle_backend_connect,
    handle_backend_list_flows,
    handle_backend_execute_universal,
    handle_backend_performance_compare
)

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    handlers = {
        "backend_registry_status": handle_backend_registry_status,
        "backend_discover": handle_backend_discover,
        "backend_connect": handle_backend_connect,
        "backend_list_flows": handle_backend_list_flows,
        "backend_execute_universal": handle_backend_execute_universal,
        "backend_performance_compare": handle_backend_performance_compare
    }

    handler = handlers.get(name)
    if handler:
        return await handler(name, arguments)
```

---

## 🎯 Future Enhancements

Potential improvements (not blocking production):

1. **Backend Health Alerts**: Proactive notifications
2. **Auto-Scaling Integration**: Dynamic backend provisioning
3. **Cost Analysis**: Track API usage and costs
4. **A/B Testing**: Compare flow versions across backends
5. **Custom Metrics**: User-defined performance indicators

---

**Specification Complete** ✅
**Ready for**: Implementation → Testing → Production Deployment
