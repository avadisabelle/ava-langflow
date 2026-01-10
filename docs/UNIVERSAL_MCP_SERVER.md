# Universal MCP Server Configuration Guide

## Environment Variables

### Backend Configuration

**Flowise Backend**:
```bash
FLOWISE_ENABLED=true
FLOWISE_API_URL=http://localhost:3000
FLOWISE_API_KEY=your_flowise_api_key_here
```

**Langflow Backend**:
```bash
LANGFLOW_ENABLED=true
LANGFLOW_API_URL=http://localhost:7860
LANGFLOW_API_KEY=your_langflow_api_key_here
```

### Redis State Persistence (Optional)

```bash
REDIS_STATE_ENABLED=true
REDIS_SESSION_TTL_SECONDS=604800          # 7 days
REDIS_EXECUTION_TTL_SECONDS=86400         # 1 day
REDIS_KEY_PREFIX=agentic_flywheel
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Langfuse Tracing (Optional)

```bash
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
LANGFUSE_HOST=https://cloud.langfuse.com
AGENTIC_FLYWHEEL_PARENT_TRACE_ID=your_trace_id_here
```

## Running the Server

### Start the Universal MCP Server

```bash
python -m agentic_flywheel.universal_mcp_server
```

### Add to Claude Desktop Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "agentic-flywheel": {
      "command": "python",
      "args": [
        "-m",
        "agentic_flywheel.universal_mcp_server"
      ],
      "env": {
        "FLOWISE_ENABLED": "true",
        "FLOWISE_API_URL": "http://localhost:3000",
        "LANGFLOW_ENABLED": "true",
        "LANGFLOW_API_URL": "http://localhost:7860",
        "REDIS_STATE_ENABLED": "true",
        "LANGFUSE_ENABLED": "false"
      }
    }
  }
}
```

## Available MCP Tools

### universal_query
Query AI workflows with intelligent routing across all backends.

**Parameters**:
- `question` (required): Your question or prompt
- `intent` (optional): Explicit intent override (auto, creative-orientation, technical-analysis, etc.)
- `backend` (optional): Backend selection (auto, flowise, langflow)
- `session_id` (optional): Session ID for conversation continuity
- `parameters` (optional): Flow-specific parameters (temperature, max_tokens)

**Example**:
```json
{
  "question": "Help me analyze this code for potential bugs",
  "intent": "technical-analysis",
  "backend": "auto",
  "session_id": "session_abc123",
  "parameters": {
    "temperature": 0.3,
    "max_tokens": 2000
  }
}
```

### backend_status
Get status of all registered backends.

### list_flows
List all available flows across all backends.

**Parameters**:
- `backend` (optional): Filter by backend (all, flowise, langflow)

### health_check
Perform health check on all backends.

### list_sessions
List active sessions (requires Redis).

**Parameters**:
- `pattern` (optional): Session ID pattern with wildcards

### get_session
Retrieve session details (requires Redis).

**Parameters**:
- `session_id` (required): Session ID to retrieve

## Architecture

```
┌─────────────────────────────────────┐
│   Claude Desktop / MCP Client       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   Universal MCP Server              │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  UniversalQueryHandler       │  │
│  │  - Intent classification     │  │
│  │  - Backend scoring           │  │
│  │  - Intelligent routing       │  │
│  └──────────────────────────────┘  │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  BackendRegistry             │  │
│  │  - Multi-backend management  │  │
│  │  - Health monitoring         │  │
│  │  - Flow discovery            │  │
│  └──────────────────────────────┘  │
└─────┬──────────────────┬────────────┘
      │                  │
      ▼                  ▼
┌──────────┐      ┌─────────────┐
│ Flowise  │      │  Langflow   │
│ Backend  │      │  Backend    │
└──────────┘      └─────────────┘
      │                  │
      ▼                  ▼
  [Flows]             [Flows]
```

## Integration Features

### Intelligent Routing

The server automatically selects the best backend based on:
1. **Flow Match** (40%): Which backend has flows matching the intent?
2. **Health** (30%): Is the backend healthy and responsive?
3. **Performance** (20%): Historical performance metrics
4. **Capability** (10%): Backend-specific strengths

### Session Continuity

When Redis is enabled:
- Sessions persist across server restarts
- Full conversation history maintained
- Context automatically restored
- TTL-based expiration

### Observability

When Langfuse is enabled:
- All queries traced with full metadata
- Routing decisions recorded
- Performance metrics captured
- Quality scoring

## Troubleshooting

### Backend Connection Issues

```bash
# Check backend status
# Use MCP tool: backend_status

# Check health
# Use MCP tool: health_check
```

### Redis Connection Issues

If Redis is unavailable, the server automatically disables persistence:
- Sessions become transient
- Server continues working normally
- Check Redis connection: `redis-cli ping`

### No Backends Available

Ensure at least one backend is:
1. Enabled via environment variables
2. Running and accessible
3. Properly configured with API keys

## Performance Tuning

### Routing Overhead

Target: <200ms (typically <50ms)

### Backend Timeouts

Default: 30 seconds (configurable per query)

### Session TTL

Default: 7 days (configurable via REDIS_SESSION_TTL_SECONDS)

## Security

- Never commit API keys to version control
- Use environment variables for secrets
- Redis should be password-protected in production
- Consider network security for backend connections
