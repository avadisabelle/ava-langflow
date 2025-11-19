# RISE Specification: Admin Intelligence MCP Tools

**Component**: Admin Intelligence Tools
**Version**: 1.0
**Created**: 2025-11-18
**Parent Spec**: `rispecs/app.spec.md`
**Session**: `a66f8bd2-29f5-461d-ad65-36b65252d469`

---

## 🎨 Desired Outcome Definition

Users want to create **data-driven optimization strategies** using insights from their AI workflow usage patterns.

### **Usage Analytics**
- Flow performance metrics from real usage
- Conversation pattern analysis
- Success rate tracking
- Response time insights

### **Intelligent Optimization**
- Data-driven flow recommendations
- Performance improvement opportunities
- Usage-based flow discovery
- Configuration sync with reality

### **Creative Archaeology**
- Understanding what works (high engagement flows)
- Identifying what doesn't (low success rates)
- Pattern recognition in conversations
- Continuous improvement feedback loop

---

## 📊 Current Structural Reality

Admin intelligence is **isolated** - powerful analytics exist but aren't accessible via MCP.

### **What Exists**
- ✅ `flowise_admin/` comprehensive analytics layer
- ✅ Database with 4,506+ messages for analysis
- ✅ Flow performance metrics
- ✅ Configuration sync capabilities
- ✅ Pattern analysis algorithms

### **What's Missing**
- ❌ No MCP interface to admin intelligence
- ❌ Analytics locked in direct DB access only
- ❌ No tool-based workflow optimization
- ❌ Insights not exposed to AI agents

---

## ⚡ Structural Tension

**Current**: Analytics exist but require direct database access
**Desired**: Admin intelligence accessible via MCP tools for AI-driven optimization

This tension drives natural advancement toward MCP-enabled admin intelligence.

---

## 🔧 The 6 Admin Intelligence Tools

### 1. flowise_admin_dashboard

**Purpose**: Comprehensive analytics dashboard

**Desired Outcome**: Users get overview of entire system performance

**Wraps**: `flowise_admin/db_interface.py:get_admin_dashboard_data()`

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
  "total_messages": 4506,
  "total_flows": 7,
  "date_range": {
    "start": "2024-01-01",
    "end": "2025-11-18"
  },
  "top_flows": [
    {
      "id": "csv2507",
      "name": "Creative Orientation",
      "message_count": 118,
      "avg_success_score": 0.92,
      "avg_engagement": 0.88
    }
  ],
  "overall_metrics": {
    "success_rate": 0.85,
    "avg_response_time_seconds": 2.3,
    "total_sessions": 342
  },
  "recommendations": [
    "Creative Orientation shows high engagement - consider expanding similar flows",
    "3 flows show low usage - review relevance or discoverability"
  ]
}
```

**Integration**: Direct call to `FlowiseDBInterface().get_admin_dashboard_data()`

---

### 2. flowise_analyze_flow

**Purpose**: Detailed performance analysis for specific flow

**Desired Outcome**: Users understand individual flow performance deeply

**Wraps**: `flowise_admin/flow_analyzer.py:analyze_flow_performance(flow_id)`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "flow_id": {
      "type": "string",
      "description": "Flow ID to analyze (e.g., 'csv2507')"
    },
    "include_samples": {
      "type": "boolean",
      "default": false,
      "description": "Include sample conversations"
    }
  },
  "required": ["flow_id"]
}
```

**Output Structure**:
```json
{
  "flow_id": "csv2507",
  "flow_name": "Creative Orientation",
  "total_messages": 118,
  "date_range": {"start": "2024-01-15", "end": "2025-11-18"},
  "performance": {
    "avg_success_score": 0.92,
    "avg_engagement": 0.88,
    "avg_response_time_seconds": 2.1,
    "success_rate": 0.95
  },
  "patterns": {
    "common_questions": [
      "What is structural tension?",
      "How do I create desired outcomes?"
    ],
    "peak_usage_hours": [14, 15, 16],
    "avg_conversation_length": 3.2
  },
  "optimization_suggestions": [
    "Response time is excellent (2.1s avg)",
    "High success score suggests strong flow design",
    "Consider caching for frequently asked questions"
  ]
}
```

**Integration**: `FlowAnalyzer().analyze_flow_performance(flow_id)`

---

### 3. flowise_discover_flows

**Purpose**: Database-driven flow discovery with usage analytics

**Desired Outcome**: Users discover active flows based on actual usage

**Wraps**: `flowise_admin/config_sync.py:discover_active_flows()`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "min_messages": {
      "type": "integer",
      "default": 10,
      "description": "Minimum message count to consider flow active"
    },
    "include_inactive": {
      "type": "boolean",
      "default": false,
      "description": "Include flows with low usage"
    },
    "sort_by": {
      "type": "string",
      "enum": ["usage", "success_rate", "engagement", "recent"],
      "default": "usage"
    }
  }
}
```

**Output Structure**:
```json
{
  "discovered_flows": 7,
  "active_flows": 5,
  "inactive_flows": 2,
  "flows": [
    {
      "id": "csv2507",
      "name": "Creative Orientation",
      "message_count": 118,
      "success_score": 0.92,
      "last_used": "2025-11-18T10:00:00Z",
      "status": "active"
    }
  ],
  "recommendations": {
    "high_performers": ["csv2507", "faith2story2507"],
    "needs_attention": ["low_usage_flow"],
    "suggested_removals": []
  }
}
```

**Integration**: `ConfigSync().discover_active_flows(min_messages)`

---

### 4. flowise_sync_config

**Purpose**: Sync flow-registry.yaml with database reality

**Desired Outcome**: Configuration reflects actual usage patterns

**Wraps**: `flowise_admin/config_sync.py:sync_configurations()`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "dry_run": {
      "type": "boolean",
      "default": true,
      "description": "Preview changes without applying"
    },
    "auto_add_flows": {
      "type": "boolean",
      "default": false,
      "description": "Automatically add discovered flows"
    },
    "remove_inactive": {
      "type": "boolean",
      "default": false,
      "description": "Remove flows with zero usage"
    }
  }
}
```

**Output Structure**:
```json
{
  "dry_run": true,
  "changes_detected": 3,
  "changes": [
    {
      "type": "add",
      "flow_id": "new_flow_123",
      "reason": "High usage (45 messages) but not in registry"
    },
    {
      "type": "update",
      "flow_id": "csv2507",
      "field": "description",
      "reason": "Database description more detailed"
    },
    {
      "type": "remove",
      "flow_id": "unused_flow",
      "reason": "Zero usage in 90 days"
    }
  ],
  "applied": false,
  "backup_created": false
}
```

**Integration**: `ConfigSync().sync_configurations(dry_run, auto_add, remove_inactive)`

---

### 5. flowise_export_metrics

**Purpose**: Export performance metrics for external analysis

**Desired Outcome**: Users analyze data in preferred tools (Excel, Tableau, etc.)

**Wraps**: `flowise_admin/flow_analyzer.py:export_flow_configurations()`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "format": {
      "type": "string",
      "enum": ["json", "csv"],
      "default": "json"
    },
    "flows": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Flow IDs to export (empty = all)"
    },
    "include_messages": {
      "type": "boolean",
      "default": false,
      "description": "Include raw message data"
    }
  }
}
```

**Output Structure (JSON)**:
```json
{
  "export_date": "2025-11-18T12:00:00Z",
  "format": "json",
  "flows_included": 7,
  "data": [
    {
      "flow_id": "csv2507",
      "flow_name": "Creative Orientation",
      "total_messages": 118,
      "avg_success_score": 0.92,
      "avg_engagement": 0.88,
      "first_message": "2024-01-15",
      "last_message": "2025-11-18"
    }
  ]
}
```

**Output Structure (CSV)**:
```csv
flow_id,flow_name,total_messages,avg_success_score,avg_engagement,first_message,last_message
csv2507,Creative Orientation,118,0.92,0.88,2024-01-15,2025-11-18
```

**Integration**: `FlowAnalyzer().export_flow_configurations(format, flows, include_messages)`

---

### 6. flowise_pattern_analysis

**Purpose**: Extract conversation patterns for optimization

**Desired Outcome**: Users discover patterns to improve flows

**Wraps**: `flowise_admin/db_interface.py:analyze_message_patterns()`

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "flow_id": {
      "type": "string",
      "description": "Analyze specific flow (optional, omit for all flows)"
    },
    "limit": {
      "type": "integer",
      "default": 100,
      "description": "Maximum messages to analyze"
    },
    "pattern_type": {
      "type": "string",
      "enum": ["question_types", "success_factors", "failure_modes", "all"],
      "default": "all"
    }
  }
}
```

**Output Structure**:
```json
{
  "analyzed_messages": 100,
  "flow_id": "csv2507",
  "patterns": {
    "question_types": {
      "definition_seeking": 45,
      "how_to": 32,
      "example_request": 18,
      "clarification": 5
    },
    "success_factors": [
      "Questions about 'structural tension' have 95% success rate",
      "Follow-up questions show high engagement (0.92 avg)",
      "Example requests correlate with positive feedback"
    ],
    "failure_modes": [
      "Vague questions result in lower success (0.65 avg)",
      "Multi-part questions show confusion patterns"
    ],
    "temporal_patterns": {
      "peak_hours": [14, 15, 16],
      "day_of_week_distribution": {"Mon": 18, "Tue": 22, "Wed": 15}
    }
  },
  "recommendations": [
    "Add examples to flow prompt for better clarity",
    "Create FAQ for common definition questions",
    "Consider breaking multi-part questions into steps"
  ]
}
```

**Integration**: `FlowiseDBInterface().analyze_message_patterns(flow_id, limit, pattern_type)`

---

## 🏗️ Implementation Architecture

### Wrapper Pattern

```python
# src/agentic_flywheel/tools/admin_tools.py

from ..flowise_admin.db_interface import FlowiseDBInterface
from ..flowise_admin.flow_analyzer import FlowAnalyzer
from ..flowise_admin.config_sync import ConfigSync

async def handle_flowise_admin_dashboard(name: str, arguments: dict) -> List:
    """Get comprehensive analytics dashboard"""
    try:
        db = FlowiseDBInterface()
        dashboard_data = db.get_admin_dashboard_data()

        # Enhance with recommendations
        recommendations = _generate_dashboard_recommendations(dashboard_data)
        dashboard_data['recommendations'] = recommendations

        return [types.TextContent(
            type="text",
            text=json.dumps(dashboard_data, indent=2)
        )]

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return [types.TextContent(
            type="text",
            text=f"❌ Error: Dashboard unavailable.\\n\\nDetails: {str(e)}"
        )]
```

### Database Availability Handling

```python
# Graceful degradation when DB unavailable
try:
    db = FlowiseDBInterface()
    data = db.get_admin_dashboard_data()
except DatabaseConnectionError:
    return "❌ Flowise database unavailable. Check connection settings."
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return f"❌ Admin operation failed: {str(e)}"
```

### Recommendation Engine

```python
def _generate_dashboard_recommendations(data: Dict) -> List[str]:
    """Generate actionable insights from dashboard data"""
    recommendations = []

    # High engagement flows
    top_flows = data.get('top_flows', [])[:3]
    if top_flows:
        recommendations.append(
            f"{top_flows[0]['name']} shows high engagement - "
            f"consider expanding similar flows"
        )

    # Low usage detection
    low_usage = [f for f in data.get('flows', []) if f.get('message_count', 0) < 10]
    if len(low_usage) > 0:
        recommendations.append(
            f"{len(low_usage)} flows show low usage - "
            f"review relevance or discoverability"
        )

    return recommendations
```

---

## ✅ Integration Contract

### Requirements

1. **Use Existing Admin Layer**
   - Don't reimplement analytics logic
   - Wrap existing functions only
   - Preserve all existing functionality

2. **Database Availability**
   - Handle connection errors gracefully
   - Provide clear error messages
   - Don't crash on DB unavailability

3. **Actionable Insights**
   - Add recommendations to raw data
   - Highlight patterns and trends
   - Suggest specific actions

4. **Format Flexibility**
   - Support JSON (default)
   - Support CSV for exports
   - Consistent structure

5. **Performance**
   - Cache where appropriate
   - Limit large queries
   - Async operations

---

## 🧪 Testing Strategy

### Unit Tests (tests/test_admin_tools.py)

```python
@pytest.mark.asyncio
async def test_flowise_admin_dashboard():
    """Test admin dashboard tool"""
    with patch('FlowiseDBInterface') as mock_db:
        mock_db.return_value.get_admin_dashboard_data.return_value = {
            "total_messages": 4506,
            "total_flows": 7
        }

        result = await handle_flowise_admin_dashboard("flowise_admin_dashboard", {})

        data = json.loads(result[0].text)
        assert "total_messages" in data
        assert "recommendations" in data
```

**Test Coverage Goals**:
- ✅ All 6 tools success paths
- ✅ Database unavailable handling
- ✅ Parameter validation
- ✅ Recommendation generation
- ✅ Export format validation

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool Response Time | <1s | Average execution |
| Database Error Handling | 100% | Graceful failures |
| Recommendation Quality | High | User feedback |
| Test Coverage | >85% | Lines covered |
| Integration Success | 100% | All tools working |

---

## 🔗 Related Components

- **flowise_admin/db_interface.py**: Database analytics
- **flowise_admin/flow_analyzer.py**: Flow performance analysis
- **flowise_admin/config_sync.py**: Configuration synchronization
- **intelligent_mcp_server.py**: Example admin integration

---

## 🚀 Production Deployment

### Environment Variables

```bash
# Flowise database connection
FLOWISE_DB_HOST=localhost
FLOWISE_DB_PORT=5432
FLOWISE_DB_NAME=flowise
FLOWISE_DB_USER=flowise_admin
FLOWISE_DB_PASSWORD=your_password
```

### MCP Server Integration

```python
# In universal_mcp_server.py
from agentic_flywheel.tools.admin_tools import (
    handle_flowise_admin_dashboard,
    handle_flowise_analyze_flow,
    handle_flowise_discover_flows,
    handle_flowise_sync_config,
    handle_flowise_export_metrics,
    handle_flowise_pattern_analysis
)

@app.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="flowise_admin_dashboard",
            description="Get analytics dashboard with flow usage and performance metrics",
            inputSchema={"type": "object", "properties": {}}
        ),
        # ... other 5 tools
    ]
```

---

## 🎯 Future Enhancements

Potential improvements (not blocking production):

1. **Real-time Analytics**: Streaming metrics updates
2. **Predictive Analysis**: Forecast flow usage patterns
3. **A/B Testing**: Compare flow variations
4. **Automated Optimization**: AI-suggested flow improvements
5. **Custom Dashboards**: User-configurable analytics views

---

**Specification Complete** ✅
**Ready for**: Implementation → Testing → Production Deployment
