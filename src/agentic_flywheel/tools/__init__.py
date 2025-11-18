"""MCP Tool implementations for Agentic Flywheel

This package contains MCP tool handlers for universal query execution
and backend management.
"""

from .universal_query import handle_universal_query, format_universal_response
from .backend_tools import (
    handle_backend_registry_status,
    handle_backend_discover,
    handle_backend_connect,
    handle_backend_list_flows,
    handle_backend_execute_universal,
    handle_backend_performance_compare
)

__all__ = [
    # Universal query
    'handle_universal_query',
    'format_universal_response',
    # Backend management
    'handle_backend_registry_status',
    'handle_backend_discover',
    'handle_backend_connect',
    'handle_backend_list_flows',
    'handle_backend_execute_universal',
    'handle_backend_performance_compare'
]

__version__ = '1.0.0'
