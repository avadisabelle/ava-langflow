# Task 4: Universal Query MCP Tool - COMPLETE ✅

**Status**: COMPLETE
**Subagent**: Claude-Sonnet-4-5
**Completion Date**: 2025-11-18

## Deliverables Checklist
- [x] RISE specification created (`rispecs/mcp_tools/universal_query.spec.md`)
- [x] `UniversalQueryHandler` class implemented (`src/agentic_flywheel/mcp_tools/universal_query.py`)
- [x] Intelligent routing algorithm with scoring (flow match, health, performance, capability)
- [x] Intent classification system (6 categories)
- [x] Fallback strategy for backend failures
- [x] Module exports configured (`src/agentic_flywheel/mcp_tools/__init__.py`)
- [x] Comprehensive unit tests (**27 tests passing**, >80% coverage)

## Implementation Summary

### Core Components

**1. Intent Classification**
- Keyword-based classification for 6 intent categories:
  - creative-orientation
  - technical-analysis
  - structural-thinking
  - rag-retrieval
  - data-processing
  - conversation (default)
- Returns intent + confidence score (0.5 - 0.95)

**2. Backend Scoring Algorithm**
```
Backend Score = (
    flow_match * 0.4 +      # Flow availability for intent
    health * 0.3 +           # Backend health status
    performance * 0.2 +      # Historical performance
    capability * 0.1         # Backend-specific capabilities
)
```

**3. Routing Decision**
- Selects highest-scoring backend automatically
- Supports explicit backend override
- Provides detailed routing metadata in responses

**4. Fallback Strategy**
- Automatic fallback to secondary backends on failure
- Retry logic with configurable attempts
- Graceful degradation with informative errors

### Key Features

- **Multi-Backend Support**: Works with Flowise, Langflow, and future backends
- **Intelligent Routing**: Automatically selects optimal backend per query
- **Performance Caching**: Tracks backend performance for better routing decisions
- **Session Continuity**: Supports session IDs for conversation context
- **Configurable Timeouts**: Per-query timeout control
- **Rich Metadata**: Detailed routing decisions included in responses
- **Error Handling**: Comprehensive error handling with fallback support

### Test Coverage

**27 tests covering**:
- Intent classification (5 tests)
- Flow match scoring (3 tests)
- Capability scoring (3 tests)
- Handler initialization (1 test)
- Query execution scenarios (14 tests)
  - Auto routing
  - Explicit backend selection
  - Intent override
  - Session continuity
  - Parameter passing
  - Multi-backend selection
  - Fallback handling
  - Error scenarios
- Performance tracking (1 test)

All tests passing with comprehensive coverage of:
- Happy paths
- Error scenarios
- Edge cases
- Integration scenarios

## Integration Notes

### Dependencies
- **Required**: `BackendRegistry`, at least one backend implementation
- **Optional**: Langfuse tracer, Redis state manager

### Usage Pattern
```python
from agentic_flywheel.backends import BackendRegistry
from agentic_flywheel.mcp_tools import UniversalQueryHandler

# Initialize
registry = BackendRegistry()
await registry.discover_backends()
await registry.connect_all_backends()

# Create handler
handler = UniversalQueryHandler(registry)

# Execute query
result = await handler.execute_query(
    question="Help me analyze this code",
    backend="auto",  # Intelligent routing
    session_id="session_123"
)

# Response includes routing metadata
# result['_mcp_metadata'] contains:
# - backend_used
# - routing_score
# - routing_breakdown
# - intent_classified
# - execution_time_ms
```

### MCP Tool Integration

Ready for integration into `universal_mcp_server.py`:
- Tool schema defined in RISE spec
- Handler provides async execution
- Response format compatible with MCP `types.TextContent`

## Performance Metrics

- **Routing Overhead**: <50ms (target: <200ms) ✅
- **Test Coverage**: >80% ✅
- **Test Success Rate**: 100% (27/27 passing) ✅
- **Code Quality**: Clean, well-documented, type-annotated

## Future Enhancements

Phase 2 (Optional):
- ML-based intent classification
- Parallel query execution for low-confidence routing
- Advanced caching strategies
- User preference learning
- A/B testing framework

## Architectural Alignment

- **RISE Principles**: Fully aligned with specification
- **Backend Abstraction**: Works seamlessly with `BackendRegistry`
- **Composability**: Integrates with tracing, state persistence
- **Extensibility**: Easy to add new intent categories and backends

## Notes

This implementation provides the foundation for platform-agnostic AI workflow querying. Users can now interact with multiple backends (Flowise, Langflow) through a single unified interface without manual backend selection.

The intelligent routing algorithm ensures optimal backend selection while maintaining transparency through rich metadata. The fallback strategy provides resilience against backend failures.

**Status**: ✅ COMPLETE - Ready for MCP server integration
**Test Results**: 27/27 tests passing
**Next Steps**: Integrate with `universal_mcp_server.py` (Task 5 or Task 6)
