"""Integration modules for Agentic Flywheel

This package provides integration utilities for external observability and
persistence services.

Available integrations:
- langfuse_tracer: Langfuse creative archaeology tracing
"""

from .langfuse_tracer import (
    trace_mcp_tool,
    get_current_trace_id,
    LangfuseObservation,
    LangfuseScore,
    LangfuseTracerManager
)
from .redis_state import (
    RedisSessionManager,
    RedisExecutionCache,
    RedisConfig
)

__all__ = [
    # Tracing
    'trace_mcp_tool',
    'get_current_trace_id',
    'LangfuseObservation',
    'LangfuseScore',
    'LangfuseTracerManager',
    # State persistence
    'RedisSessionManager',
    'RedisExecutionCache',
    'RedisConfig'
]

__version__ = '1.0.0'
