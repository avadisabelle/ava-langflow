"""Adapters for external workflow engines

This package provides adapters that bridge external workflow engines
(Flowise, Langflow, etc.) with the Universal MCP Server's unified abstractions.

Available adapters:
- FlowiseFlowAdapter: Import and map real Flowise flows from YAML registry
"""

from .flowise_flow_adapter import FlowiseFlowAdapter, FlowiseFlowMetadata

__all__ = [
    'FlowiseFlowAdapter',
    'FlowiseFlowMetadata'
]

__version__ = '1.0.0'
