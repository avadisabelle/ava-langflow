"""MCP Tool implementations for Agentic Flywheel

This package contains MCP tool handlers for universal query execution,
backend management, and admin intelligence.
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
from .admin_tools import (
    handle_flowise_admin_dashboard,
    handle_flowise_analyze_flow,
    handle_flowise_discover_flows,
    handle_flowise_sync_config,
    handle_flowise_export_metrics,
    handle_flowise_pattern_analysis
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
    'handle_backend_performance_compare',
    # Admin intelligence
    'handle_flowise_admin_dashboard',
    'handle_flowise_analyze_flow',
    'handle_flowise_discover_flows',
    'handle_flowise_sync_config',
    'handle_flowise_export_metrics',
    'handle_flowise_pattern_analysis'
]

__version__ = '1.0.0'
