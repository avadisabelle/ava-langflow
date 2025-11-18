"""MCP Tool implementations for Agentic Flywheel

This package contains MCP tool handlers for universal query execution.
"""

from .universal_query import handle_universal_query, format_universal_response

__all__ = [
    'handle_universal_query',
    'format_universal_response'
]

__version__ = '1.0.0'
