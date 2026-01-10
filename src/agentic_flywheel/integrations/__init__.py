"""Integration modules for Agentic Flywheel

This package provides integration utilities for external observability and
persistence services.

Available integrations:
- langfuse_tracer: Langfuse creative archaeology tracing
- redis_state: Redis session state persistence and execution caching
"""

from .langfuse_tracer import (
    trace_mcp_tool,
    get_current_trace_id,
    LangfuseObservation,
    LangfuseScore,
    LangfuseTracerManager
)

from .redis_state import (
    RedisConfig,
    RedisSessionManager,
    RedisExecutionCache
)

__all__ = [
    # Langfuse tracing
    'trace_mcp_tool',
    'get_current_trace_id',
    'LangfuseObservation',
    'LangfuseScore',
    'LangfuseTracerManager',
    # Redis persistence
    'RedisConfig',
    'RedisSessionManager',
    'RedisExecutionCache'
]

__version__ = '1.0.0'
